import type { InvenTreePluginContext } from '@inventreedb/ui';
import { Alert, Button, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';

function PluginSettingsDisplay({
  context: _context
}: {
  context: InvenTreePluginContext;
}) {
  return (
    <Alert color='blue' title='NFC Plugin'>
      <Text>Custom settings UI for the NFC plugin.</Text>
      <Text>Configure the plugin settings from the InvenTree admin panel.</Text>
      <Button
        color='blue'
        mt='sm'
        onClick={() => {
          notifications.show({
            title: 'NFC Plugin',
            message: 'Settings panel loaded.',
            color: 'blue'
          });
        }}
      >
        Test Notification
      </Button>
    </Alert>
  );
}

export function renderPluginSettings(context: InvenTreePluginContext) {
  return <PluginSettingsDisplay context={context} />;
}
