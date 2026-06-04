# Usage

This document explains how to use the nfc plugin after installation.

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

### Link a tag to a part

Use the part detail panel to link a new NFC tag to a part.

### Steps

1. Open the part page.
2. Expand the NFC panel.
3. If no tag is linked yet, click **Link NFC Tag**.
4. Place the tag on the reader when prompted.
5. Wait for confirmation.
