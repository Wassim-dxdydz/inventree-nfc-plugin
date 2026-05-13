import {
  checkPluginVersion,
  type InvenTreePluginContext
} from '@inventreedb/ui';
import { t } from '@lingui/core/macro';
import {
  Alert,
  Badge,
  Button,
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

async function pollForTag(
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

    // Hard stop — no reader plugged in
    if (data.error === 'no_reader') return null;

    // Agent timed out — loop again if we still have budget
    await new Promise((r) => setTimeout(r, 200));
  }
  return null;
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
      staleTime: 60_000
    },
    context.queryClient
  );

  const config = configQuery.data;

  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState<TagLookupResult | null>(null);

  const startScan = useCallback(async () => {
    if (!config) return;
    setScanning(true);
    setResult(null);

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
      setScanning(false);
      return;
    }

    try {
      const res = await context.api.get(`/plugin/nfc/tag/${uid}/`);
      const data: TagLookupResult = res.data;
      setResult(data);
      if (data.found && config.auto_redirect && data.part_url) {
        context.navigate(data.part_url);
      }
    } catch {
      notifications.show({
        title: t`Lookup failed`,
        message: t`Could not check this tag.`,
        color: 'red'
      });
    }

    setScanning(false);
  }, [config, context.api, context.navigate]);

  return (
    <SimpleGrid cols={1} spacing='md'>
      <Button
        color='teal'
        leftSection={
          scanning ? <Loader size={14} color='white' /> : <IconWifi size={16} />
        }
        loading={scanning}
        disabled={!config}
        onClick={startScan}
      >
        {scanning ? t`Waiting for tag…` : t`Scan NFC Tag`}
      </Button>

      {result &&
        (result.found ? (
          <Alert color='teal' title={t`Part found`}>
            <Stack gap={4}>
              <Text fw={600}>{result.part_name}</Text>
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
