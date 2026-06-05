import {
  checkPluginVersion,
  type InvenTreePluginContext
} from '@inventreedb/ui';
import { t } from '@lingui/core/macro';
import {
  Alert,
  Badge,
  Box,
  Button,
  Group,
  Loader,
  SimpleGrid,
  Stack,
  Text
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconWifi } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

interface NfcConfig {
  agent_base_url: string;
  scan_timeout_seconds: number;
  auto_redirect: boolean;
  sound_enabled: boolean;
}

interface AgentHealth {
  status: 'ok' | 'unreachable';
  agent_reachable: boolean;
  reader_connected: boolean;
  readers?: string[];
}

interface ScanResult {
  // Agent returns { uid: "AABBCCDD" } on success, or { error: "timeout" | "no_reader" }
  uid?: string;
  error?: string;
}

interface TagLookupResult {
  found: boolean;
  uid: string;
  part_name?: string;
  part_description?: string;
  total_stock?: number;
  part_url?: string;
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

/**
 * NFC Dashboard widget — shown on the InvenTree dashboard for staff users.
 * Provides a quick "Scan to Find" directly from the home screen.
 */
function NFCDashboardItem({ context }: { context: InvenTreePluginContext }) {
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

  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState<TagLookupResult | null>(null);

  const startScan = useCallback(async () => {
    if (!config || scanning) return;

    setScanning(true);
    setResult(null);

    try {
      const uid = await scanOnce(
        config.agent_base_url,
        config.scan_timeout_seconds
      );

      const res = await context.api.get(`/plugin/nfc/tag/${uid}/`);
      const data: TagLookupResult = res.data;
      setResult(data);

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
      setScanning(false);
    }
  }, [config, scanning, context.api, context.navigate]);

  return (
    <SimpleGrid cols={1} spacing='md'>
      <Group gap='xs'>
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

      <Button
        color='teal'
        leftSection={
          scanning ? <Loader size={14} color='white' /> : <IconWifi size={16} />
        }
        loading={scanning}
        disabled={!canScan}
        onClick={startScan}
      >
        {scanning ? t`Waiting for tag...` : t`Scan NFC Tag`}
      </Button>

      {result &&
        (result.found ? (
          <Alert color='teal' title={t`Part found`}>
            <Stack gap={4}>
              <Text fw={600}>{result.part_name}</Text>

              {result.part_description && (
                <Text size='sm' c='dimmed'>
                  {result.part_description}
                </Text>
              )}

              <Text size='sm'>
                {t`Stock:`} {result.total_stock ?? '—'}
              </Text>

              <Button
                size='xs'
                variant='light'
                color='teal'
                onClick={() => context.navigate(result.part_url!)}
              >
                {t`Go to part`}
              </Button>
            </Stack>
          </Alert>
        ) : (
          <Alert color='yellow' title={t`Unknown tag`}>
            <Text size='sm'>
              {t`No part linked to`}{' '}
              <Badge variant='outline'>{result.uid}</Badge>
            </Text>
          </Alert>
        ))}
    </SimpleGrid>
  );
}

// This is the function which is called by InvenTree to render the dashboard component
export function renderNFCDashboardItem(context: InvenTreePluginContext) {
  checkPluginVersion(context);
  return <NFCDashboardItem context={context} />;
}
