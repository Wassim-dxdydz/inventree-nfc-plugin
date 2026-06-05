import {
  checkPluginVersion,
  type InvenTreePluginContext,
  ModelType
} from '@inventreedb/ui';
import { t } from '@lingui/core/macro';
import {
  Accordion,
  Alert,
  Badge,
  Box,
  Button,
  Group,
  Loader,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconLink, IconTrash, IconWifi } from '@tabler/icons-react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useCallback, useMemo, useState } from 'react';
import { LocalizedComponent } from './locale';

interface NfcConfig {
  agent_base_url: string;
  scan_timeout_seconds: number;
  auto_redirect: boolean;
  allow_link_from_scan: boolean;
  sound_enabled: boolean;
}

interface TagByPartResponse {
  found: boolean;
  uid?: string;
  part_id?: number;
  linked_at?: string;
  linked_by?: string | null;
}

interface ScanResult {
  // Agent returns { uid: "AABBCCDD" } on success, or { error: "timeout" | "no_reader" }
  uid?: string;
  error?: string;
}

interface TagLookupResult {
  found: boolean;
  uid?: string;
  part_id?: number;
  part_name?: string;
  part_description?: string;
  total_stock?: number;
  part_url?: string;
}

interface AgentHealth {
  status: 'ok' | 'unreachable';
  agent_reachable: boolean;
  reader_connected: boolean;
  readers?: string[];
}

class AgentScanError extends Error {
  code: string;

  constructor(code: string, message?: string) {
    super(message ?? code);
    this.code = code;
  }
}

async function getAgentHealth(agentBaseUrl: string): Promise<AgentHealth> {
  try {
    const res = await fetch(`${agentBaseUrl}/health`);

    if (!res.ok) {
      return {
        status: 'unreachable',
        agent_reachable: false,
        reader_connected: false,
        readers: []
      };
    }

    const data = await res.json();

    return {
      status: 'ok',
      agent_reachable: true,
      reader_connected: !!data.reader_connected,
      readers: Array.isArray(data.readers) ? data.readers : []
    };
  } catch {
    return {
      status: 'unreachable',
      agent_reachable: false,
      reader_connected: false,
      readers: []
    };
  }
}

async function scanOnce(
  agentBaseUrl: string,
  timeoutSeconds: number
): Promise<string> {
  const controller = new AbortController();

  const timer = window.setTimeout(
    () => {
      controller.abort();
    },
    (timeoutSeconds + 2) * 1000
  );

  try {
    const res = await fetch(`${agentBaseUrl}/scan/once`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ timeout: timeoutSeconds }),
      signal: controller.signal
    });

    const data: ScanResult = await res.json().catch(() => ({}));

    if (res.ok && data.uid) {
      return data.uid;
    }

    throw new AgentScanError(data.error ?? `http_${res.status}`);
  } catch (err: any) {
    if (err?.name === 'AbortError') {
      throw new AgentScanError('client_timeout');
    }

    if (err instanceof AgentScanError) {
      throw err;
    }

    throw new AgentScanError('network_error');
  } finally {
    clearTimeout(timer);
  }
}

function getScanErrorMessage(code: string): string {
  switch (code) {
    case 'timeout':
    case 'client_timeout':
      return 'No tag detected before timeout.';
    case 'no_reader':
      return 'No NFC reader detected on this workstation.';
    case 'scan_in_progress':
      return 'A scan is already in progress.';
    case 'network_error':
      return 'Cannot reach the local NFC agent.';
    default:
      return 'Scan failed.';
  }
}

/**async function pollForTag(
  agentBaseUrl: string,
  timeoutSeconds: number,
  signal: AbortSignal
): Promise<string | null> {
  const deadline = Date.now() + timeoutSeconds * 1000;
  while (Date.now() < deadline) {
    if (signal.aborted) return null;

    const res = await fetch(`${agentBaseUrl}/scan/once`, {
      method: 'POST', // agent exposes POST /scan/once
      signal
    }).catch(() => null);

    if (!res) return null;

    const data: ScanResult = await res.json();

    // Success — agent returned a UID
    if (data.uid) return data.uid;

    // Hard stop — no reader plugged in, no point retrying
    if (data.error === 'no_reader') return null;

    // Timeout from agent — loop again if we still have budget
    await new Promise((r) => setTimeout(r, 200));
  }

  return null;
}**/

/**
 * Render a custom panel with the provided context.
 * Refer to the InvenTree documentation for the context interface
 * https://docs.inventree.org/en/latest/plugins/mixins/ui/#plugin-context
 */
function NFCPanel({ context }: { context: InvenTreePluginContext }) {
  const partId = useMemo(
    () => (context.model === ModelType.part ? (context.id ?? null) : null),
    [context.model, context.id]
  );

  // Staff
  const isStaff = useMemo(() => !!context.user?.isStaff, [context.user]);

  // Config
  const configQuery = useQuery<NfcConfig>(
    {
      queryKey: ['nfc-config'],
      queryFn: () => context.api.get('/plugin/nfc/config/').then((r) => r.data),
      staleTime: 0,
      refetchOnWindowFocus: true,
    },
    context.queryClient
  );

  const config = configQuery.data;

  const healthQuery = useQuery<AgentHealth>(
    {
      queryKey: ['nfc-agent-health', config?.agent_base_url],
      enabled: !!config?.agent_base_url,
      queryFn: () => getAgentHealth(config!.agent_base_url),
      refetchInterval: 3000,
      retry: false
    },
    context.queryClient
  );

  const health = healthQuery.data;
  const agentReachable = !!health?.agent_reachable;
  const readerReady = !!health?.agent_reachable && !!health?.reader_connected;
  const canScan = !!config && readerReady;

  // Tag linked to this part
  const tagByPartQuery = useQuery<TagByPartResponse>(
    {
      queryKey: ['nfc-tag-by-part', partId],
      enabled: !!partId,
      queryFn: () =>
        context.api
          .get(`/plugin/nfc/tag/by-part/${partId}/`)
          .then((r) => r.data),
      staleTime: 60_000
    },
    context.queryClient
  );

  const linkedTag = tagByPartQuery.data?.found ? tagByPartQuery.data : null;

  // Unlink
  const unlinkMutation = useMutation(
    {
      mutationFn: (uid: string) =>
        context.api.delete(`/plugin/nfc/link/${uid}/`),
      onSuccess: () => {
        // Refresh the tag status for this part
        context.queryClient.invalidateQueries({
          queryKey: ['nfc-tag-by-part', partId]
        });
        notifications.show({
          title: t`Tag unlinked`,
          message: t`NFC tag has been successfully unlinked.`,
          color: 'green'
        });
      },
      onError: () => {
        notifications.show({
          title: t`Unlink failed`,
          message: t`Could not remove the NFC tag. Try again.`,
          color: 'red'
        });
      }
    },
    context.queryClient
  );

  /**const [linkScanning, setLinkScanning] = useState(false);
  const startLinkScan = useCallback(async () => {
    if (!config || !partId) return;
    setLinkScanning(true);

    const uid = await pollForTag(
      config.agent_base_url,
      config.scan_timeout_seconds,
      new AbortController().signal
    );

    if (!uid) {
      notifications.show({
        title: t`No tag detected`,
        message: t`Scan timed out or no reader found.`,
        color: 'yellow'
      });
      setLinkScanning(false);
      return;
    }

    try {
      await context.api.post('/plugin/nfc/link/', { uid, part_id: partId });
      context.queryClient.invalidateQueries({
        queryKey: ['nfc-tag-by-part', partId]
      });
      notifications.show({
        title: t`Tag linked`,
        message: `${uid} → part #${partId}`,
        color: 'green'
      });
    } catch (err: any) {
      notifications.show({
        title: t`Link failed`,
        message:
          err?.response?.data?.error ?? t`Could not link tag. Try again.`,
        color: 'red'
      });
    }

    setLinkScanning(false);
  }, [config, partId, context.api, context.queryClient]);**/

  // Link Scan
  const [linkScanning, setLinkScanning] = useState(false);

  const startLinkScan = useCallback(async () => {
    if (!config || !partId || linkScanning) return;

    setLinkScanning(true);

    try {
      const uid = await scanOnce(
        config.agent_base_url,
        config.scan_timeout_seconds
      );

      await context.api.post('/plugin/nfc/link/', { uid, part_id: partId });

      context.queryClient.invalidateQueries({
        queryKey: ['nfc-tag-by-part', partId]
      });

      notifications.show({
        title: t`Tag linked`,
        message: `${uid} → part #${partId}`,
        color: 'green'
      });
    } catch (err: any) {
      const message =
        err?.response?.data?.error ??
        getScanErrorMessage(err?.code ?? 'unknown');

      notifications.show({
        title: t`Link failed`,
        message,
        color:
          err?.code === 'timeout' || err?.code === 'client_timeout'
            ? 'yellow'
            : 'red'
      });
    } finally {
      setLinkScanning(false);
    }
  }, [config, partId, linkScanning, context.api, context.queryClient]);

  /**const [findScanning, setFindScanning] = useState(false);
  const [findResult, setFindResult] = useState<TagLookupResult | null>(null);

  const startFindScan = useCallback(async () => {
    if (!config) return;
    setFindScanning(true);
    setFindResult(null);

    const uid = await pollForTag(
      config.agent_base_url,
      config.scan_timeout_seconds,
      new AbortController().signal
    );

    if (!uid) {
      notifications.show({
        title: t`No tag detected`,
        message: t`Scan timed out or no reader found.`,
        color: 'yellow'
      });
      setFindScanning(false);
      return;
    }

    try {
      const res = await context.api.get(`/plugin/nfc/tag/${uid}/`);
      const data: TagLookupResult = res.data;
      setFindResult(data);

      if (data.found && config.auto_redirect && data.part_url) {
        context.navigate(data.part_url);
      }
    } catch {
      notifications.show({
        title: t`Lookup failed`,
        message: t`Could not check this tag. Try again.`,
        color: 'red'
      });
    }

    setFindScanning(false);
  }, [config, context.api, context.navigate]);**/

  // Find scan
  const [findScanning, setFindScanning] = useState(false);
  const [findResult, setFindResult] = useState<TagLookupResult | null>(null);

  const startFindScan = useCallback(async () => {
    if (!config || findScanning) return;

    setFindScanning(true);
    setFindResult(null);

    try {
      const uid = await scanOnce(
        config.agent_base_url,
        config.scan_timeout_seconds
      );

      const res = await context.api.get(`/plugin/nfc/tag/${uid}/`);
      const data: TagLookupResult = res.data;
      setFindResult(data);

      if (data.found && config.auto_redirect && data.part_url) {
        context.navigate(data.part_url);
      }
    } catch (err: any) {
      notifications.show({
        title: t`Scan failed`,
        message: getScanErrorMessage(err?.code ?? 'unknown'),
        color:
          err?.code === 'timeout' || err?.code === 'client_timeout'
            ? 'yellow'
            : 'red'
      });
    } finally {
      setFindScanning(false);
    }
  }, [config, findScanning, context.api, context.navigate]);

  // Render
  if (configQuery.isLoading) {
    return (
      <Group justify='center' p='md'>
        <Loader size='sm' />
        <Text c='dimmed'>{t`Loading NFC config...`}</Text>
      </Group>
    );
  }

  if (configQuery.isError || !config) {
    return (
      <Alert color='red' title={t`Config error`}>
        {t`Could not load NFC plugin settings.`}
      </Alert>
    );
  }

  return (
    <>
      <Group gap='xs' mb='sm'>
        <Box
          w={10}
          h={10}
          style={{
            borderRadius: '999px',
            backgroundColor: healthQuery.isLoading
              ? 'var(--mantine-color-yellow-6)'
              : readerReady
                ? 'var(--mantine-color-green-6)'
                : 'var(--mantine-color-red-6)',
            flexShrink: 0
          }}
        />
        <Text
          size='sm'
          c={healthQuery.isLoading ? 'yellow' : readerReady ? 'green' : 'red'}
        >
          {healthQuery.isLoading
            ? t`Checking reader...`
            : !agentReachable
              ? t`Agent not reachable`
              : readerReady
                ? t`Reader connected`
                : t`Reader not available`}
        </Text>
      </Group>

      <Accordion defaultValue='scan'>
        {/* Link / Unlink — staff + part page only */}
        {partId && isStaff && (
          <Accordion.Item value='link'>
            <Accordion.Control>
              <Title c={context.theme.primaryColor} order={4}>
                {t`NFC Tag`}
              </Title>
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap='sm'>
                {tagByPartQuery.isLoading ? (
                  <Group>
                    <Loader size='xs' />
                    <Text size='sm' c='dimmed'>
                      {t`Checking tag...`}
                    </Text>
                  </Group>
                ) : linkedTag ? (
                  <>
                    <Alert
                      color='teal'
                      title={t`Tag linked`}
                      icon={<IconWifi size={16} />}
                    >
                      <Stack gap={4}>
                        <Group gap='xs'>
                          <Text size='sm' fw={600}>
                            {t`UID:`}
                          </Text>
                          <Badge variant='outline' color='teal'>
                            {linkedTag.uid}
                          </Badge>
                        </Group>
                        {linkedTag.linked_by && (
                          <Text size='xs' c='dimmed'>
                            {t`Linked by`} {linkedTag.linked_by}
                            {linkedTag.linked_at &&
                              ` — ${new Date(linkedTag.linked_at).toLocaleDateString()}`}
                          </Text>
                        )}
                      </Stack>
                    </Alert>

                    <Button
                      color='red'
                      variant='light'
                      leftSection={<IconTrash size={16} />}
                      loading={unlinkMutation.isPending}
                      onClick={() => unlinkMutation.mutate(linkedTag.uid!)}
                    >
                      {t`Unlink tag`}
                    </Button>
                  </>
                ) : (
                  <>
                    <Text size='sm' c='dimmed'>
                      {t`No NFC tag linked to this part.`}
                    </Text>

                    <Button
                      color={context.theme.primaryColor}
                      disabled={!canScan}
                      leftSection={
                        linkScanning ? (
                          <Loader size={14} color='white' />
                        ) : (
                          <IconLink size={16} />
                        )
                      }
                      loading={linkScanning}
                      onClick={startLinkScan}
                    >
                      {linkScanning ? t`Waiting for tag...` : t`Link NFC Tag`}
                    </Button>
                  </>
                )}
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>
        )}
        {/* Scan to Find — everyone */}
        <Accordion.Item value='scan'>
          <Accordion.Control>
            <Title c={context.theme.primaryColor} order={4}>
              {t`Scan to Find`}
            </Title>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap='sm'>
              <Button
                color={context.theme.primaryColor}
                disabled={!canScan}
                leftSection={
                  findScanning ? (
                    <Loader size={14} color='white' />
                  ) : (
                    <IconWifi size={16} />
                  )
                }
                loading={findScanning}
                onClick={startFindScan}
              >
                {findScanning ? t`Waiting for tag...` : t`Scan Tag`}
              </Button>

              {findResult &&
                (findResult.found ? (
                  <Alert color='teal' title={t`Part found`}>
                    <Stack gap={4}>
                      <Text fw={600}>{findResult.part_name}</Text>

                      {findResult.part_description && (
                        <Text size='sm' c='dimmed'>
                          {findResult.part_description}
                        </Text>
                      )}

                      <Text size='sm'>
                        {t`Stock:`} {findResult.total_stock ?? '—'}
                      </Text>

                      <Button
                        size='xs'
                        variant='light'
                        color='teal'
                        mt={4}
                        onClick={() => context.navigate(findResult.part_url!)}
                      >
                        {t`Go to part`}
                      </Button>
                    </Stack>
                  </Alert>
                ) : (
                  <Alert color='yellow' title={t`Unknown tag`}>
                    <Stack gap='xs'>
                      <Text size='sm'>
                        {t`No part linked to`}{' '}
                        <Badge variant='outline'>{findResult.uid}</Badge>
                      </Text>

                      {config.allow_link_from_scan && (
                        <Button
                          size='xs'
                          variant='light'
                          color='yellow'
                          onClick={() => context.navigate('/part/')}
                        >
                          {t`Browse parts to link`}
                        </Button>
                      )}
                    </Stack>
                  </Alert>
                ))}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </>
  );
}

// This is the function which is called by InvenTree to render the actual panel component
export function renderNFCPanel(context: InvenTreePluginContext) {
  checkPluginVersion(context);

  return (
    <LocalizedComponent locale={context.locale} context={context}>
      <NFCPanel context={context} />
    </LocalizedComponent>
  );
}
