# Troubleshooting

This guide covers the most common issues you may encounter when using the InvenTree NFC plugin.

## Plugin does not appear in InvenTree

### Symptoms

- The plugin is not visible in the InvenTree plugin list.
- The NFC panel or dashboard item does not appear.

### Possible causes

- The plugin is not installed correctly.
- The frontend build was not generated.
- Plugin support is disabled in the InvenTree server configuration.

### Fix

1. Confirm that the plugin is installed in editable mode.
2. Rebuild the frontend assets:
   ```bash
   npm run build
   ```
3. Make sure plugin support is enabled in the InvenTree configuration.
4. Restart the InvenTree server.
5. Run the update step again if needed:
   ```bash
   docker compose run --rm inventree-server invoke update
   ```

## Agent not reachable

### Symptoms

- The health indicator shows **Agent not reachable**.
- Scans fail immediately.
- The NFC reader status stays red.

### Possible causes

- The local NFC agent is not running.
- The agent is running on the wrong host or port.
- The browser cannot reach the agent URL.
- The agent configuration in the plugin is incorrect.

### Fix

1. Make sure the NFC agent is running on the workstation with the USB reader.
2. Check the agent URL in the plugin settings.
3. Confirm that the configured port matches the running agent.
4. Open the browser console and check for network errors.
5. Try the health endpoint directly if needed.

## Reader not detected

### Symptoms

- The agent starts, but the reader status stays red.
- `pcsc_scan` shows no reader.
- The agent health endpoint reports no reader connected.

### Possible causes

- The NFC reader is unplugged.
- `pcscd` is not running.
- PC/SC libraries are missing.
- The USB reader is not recognized by the system.

### Fix

1. Check that the USB reader is plugged in.
2. Verify that the reader appears in:
   ```bash
   lsusb
   ```
3. Make sure `pcscd` is running:
   ```bash
   sudo systemctl status pcscd
   ```
4. Restart the PC/SC service if needed.
5. Test detection with:
   ```bash
   pcsc_scan
   ```

## Scan times out

### Symptoms

- The UI shows a timeout message.
- No tag is detected before the scan window ends.

### Possible causes

- No tag was placed on the reader.
- The tag was placed too late.
- The reader is not reading the tag correctly.

### Fix

1. Place the tag directly on the reader when the scan starts.
2. Try again with a different tag if available.
3. Confirm the reader is supported and working with `pcsc_scan`.
4. Check the scan timeout setting in the plugin configuration.

## Tag already linked

### Symptoms

- Linking fails with a conflict error.
- The plugin says the tag is already linked to a part.

### Possible causes

- The UID is already active on another part.
- The tag was previously linked and not unlinked first.

### Fix

1. Open the part that currently owns the tag.
2. Unlink the existing tag first.
3. Retry the link operation.
4. If needed, check the tag record in the database.

## Part already has a tag

### Symptoms

- Linking fails with a conflict error.
- The plugin says the part already has an active NFC tag.

### Possible causes

- The part already has an active link.
- The existing tag was not removed before linking a new one.

### Fix

1. Open the part detail page.
2. Check whether a tag is already linked.
3. Click **Unlink tag** first.
4. Link the new tag after the old one is removed.

## Plugin settings are wrong

### Symptoms

- The status is red even though the reader works.
- Scans go to the wrong agent address.
- The scan timeout behaves unexpectedly.

### Possible causes

- The agent base URL is incorrect.
- The timeout value is too short or too long.
- Auto-redirect is configured differently than expected.

### Fix

1. Open the plugin settings.
2. Check the agent base URL.
3. Confirm the scan timeout value.
4. Review the auto-redirect setting.
5. Save the settings and refresh the page.

## Frontend changes do not show up

### Symptoms

- You changed the code, but the UI still shows the old version.

### Possible causes

- The frontend was not rebuilt.
- The browser cached the old bundle.
- The server was not restarted after the change.

### Fix

1. Run:
   ```bash
   npm run build
   ```
2. Refresh the page.
3. Restart the InvenTree server if needed.
4. Clear the browser cache if the old UI still appears.

## Useful checks

These commands are useful when debugging NFC issues:

```bash
lsusb
pcsc_scan
sudo systemctl status pcscd
docker compose logs
```

If the issue still remains after these checks, compare the browser console, server logs, and agent logs to find where the failure occurs.