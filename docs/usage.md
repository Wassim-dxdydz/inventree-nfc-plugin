# Usage

This document explains how to use the NFC plugin after installation.

## Overview

The plugin lets you:

- Scan an NFC tag and find the linked InvenTree part.
- Link a tag to a part.
- Unlink a tag from a part.
- Check whether the NFC reader is connected.

The plugin uses a local NFC agent on the workstation that is physically connected to the NFC reader.

## Health indicator

The plugin shows the reader status in the UI:

- **Green**: the reader is connected and ready.
- **Yellow**: the agent is being checked or a scan is in progress.
- **Red**: the agent is unreachable or the reader is not available.

If the indicator stays red, check that the reader is plugged in, the agent is running, and PC/SC is working correctly.

## Scan to find

Use **Scan NFC Tag** to scan a tag and search for the linked part.

### Steps

1. Open the NFC dashboard item.
2. Confirm the reader status is green.
3. Click **Scan NFC Tag**.
4. Place the NFC tag on the reader.
5. Wait for the result.

### Result behavior

- If the tag is linked, the plugin shows the part name, stock level, and a button to open the part page.
- If the tag is not linked, the plugin shows an unknown-tag message.

If auto-redirect is enabled in the plugin settings, the plugin automatically opens the part page when a matching tag is found.

## Link a tag to a part

Use the part detail panel to link a new NFC tag to a part.

### Steps

1. Open the part page.
2. Expand the NFC panel.
3. If no tag is linked yet, click **Link NFC Tag**.
4. Place the tag on the reader when prompted.
5. Wait for confirmation.

### Notes

- A part can only have one active NFC tag at a time.
- A tag can only be linked to one active part at a time.
- If the tag or part is already linked, the plugin will show a conflict error.

## Unlink a tag

If a part already has a tag linked, the panel shows the UID and an **Unlink tag** button.

### Steps

1. Open the part page.
2. Expand the NFC panel.
3. Confirm the tag UID is the one you want to remove.
4. Click **Unlink tag**.

Only staff users can unlink tags.

## What the status means

### Reader connected

The agent can see a valid NFC reader and can accept scans.

### Reader not available

The agent is running, but no reader is detected.

### Agent not reachable

The frontend cannot reach the local NFC agent at all.

## Typical workflow

A normal workflow looks like this:

1. Start the NFC agent on the workstation.
2. Open InvenTree.
3. Confirm the reader status is green.
4. Scan a tag to find the linked part.
5. Open the part page.
6. Link or unlink tags as needed.

## Common cases

### New tag

If a scanned tag is unknown, you must link it to a part from the part detail panel.

### Existing tag

If a tag is already linked, the scan result shows the matching part.

### Duplicate link attempt

If you try to link a tag that is already used, the plugin will reject it.

### Reader disconnected

If the reader is unplugged during use, the status changes to red and scans will fail until the reader is restored.

## Tips

- Keep the NFC reader connected before opening InvenTree.
- Refresh the page if the agent was started after the UI loaded.
- Recheck the plugin settings if the status never turns green.
- Use the browser console and agent logs if you need to debug a connection problem.