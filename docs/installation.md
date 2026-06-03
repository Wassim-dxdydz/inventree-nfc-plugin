# Installation

This guide explains how to set up the InvenTree NFC plugin development environment, install the required dependencies, and verify that the NFC reader works correctly.

## Overview

The project uses three main parts:

- **InvenTree** as the main inventory platform.
- **A local NFC agent / reader stack** to communicate with the USB NFC reader.
- **The NFC plugin** to link NFC tags with InvenTree parts.

This guide is written for a Linux development machine and an InvenTree devcontainer-based workflow.

The examples below use Debian/Ubuntu commands for Linux. If you are using another host OS, review the platform-specific notes before you begin.

## Prerequisites

Before starting, make sure you have:

- A machine running Linux, macOS, or Windows 10/11 with WSL2.
- `git` installed.
- Docker and Docker Compose installed, or Docker Desktop on macOS/Windows.
- Node.js and npm installed.
- Python 3 and `venv` available.
- A compatible NFC USB reader connected to the machine.
- Permission to use Docker and access USB devices, if required.

## Platform-specific notes

### Debian/Ubuntu

This guide uses Debian/Ubuntu package commands. If you are on Debian or Ubuntu, follow the steps in this file.

### Other Linux distributions

On Fedora, CentOS, Arch, or other distributions, use your distro's package manager to install Docker, Node.js, Python, PC/SC, and NFC reader libraries. The plugin code itself is platform-independent, but the system packages and service names vary by distribution.

### macOS

On macOS, install dependencies with Homebrew and use Docker Desktop for containers. Direct USB passthrough to Docker may be limited, so a Linux VM or remote Linux host is often easier for NFC hardware testing.

Example macOS dependency installation:

```bash
brew install git python node pcsc-lite
pip install pyscard
```

### Windows / WSL2

Windows can run InvenTree in Docker Desktop and use WSL2 for development. Native Windows PC/SC support usually works through the Smart Card service, but Docker may not expose USB NFC readers directly unless you use WSL2 and USB passthrough tools such as `usbipd`.

Use the Windows installers for Git, Node.js, and Python, or install them inside WSL2 for a Linux-style development environment.

## Install Docker

Add Docker’s official GPG key:

```bash
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```

Add the Docker repository:

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/debian $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Install Docker Engine and the Compose plugin:

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Allow running Docker without `sudo`:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## Install Node.js

Install `nvm`:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
```

Install the latest LTS version of Node.js:

```bash
nvm install --lts
```

Verify the installation:

```bash
node --version
npm --version
```

## Set up InvenTree

Create a working directory:

```bash
mkdir inventree
cd inventree
```

Download the official container files:

```bash
wget -q https://raw.githubusercontent.com/inventree/InvenTree/master/contrib/container/docker-compose.yml
wget -q https://raw.githubusercontent.com/inventree/InvenTree/master/contrib/container/.env
wget -q https://raw.githubusercontent.com/inventree/InvenTree/stable/contrib/container/Caddyfile
```

Update `.env` with your local credentials and configuration values.

Initialize the database and admin user:

```bash
docker compose run --rm inventree-server invoke update
```

Start InvenTree:

```bash
docker compose up -d
```

Add the local hostname entry:

```bash
echo "127.0.0.1 inventree.localhost" | sudo tee -a /etc/hosts
```

You should now be able to access InvenTree through the browser.

## Set up the devcontainer

Open the InvenTree project in VS Code and reopen it in the container:

- Open the command palette.
- Choose **Reopen in Container**.

This will build the development containers for the InvenTree server, PostgreSQL database, and Redis cache.

Once inside the container, activate the virtual environment if needed:

```bash
source /home/inventree/dev/venv/bin/activate
```

## Install the plugin

Go to the plugin directory inside the InvenTree data folder:

```bash
cd inventree/inventree-data/plugins
```

Create the plugin directory and files:

```bash
mkdir nfc_plugin
cd nfc_plugin
touch __init__.py
touch nfc_plugin.py
touch setup.cfg
```

Make sure the folder is writable by your user:

```bash
sudo chown -R $USER:$USER ~/inventree/inventree-data/plugins
```

Install the plugin in editable mode:

```bash
pip install -e path/to/nfc_plugin
```

If needed, verify that the plugin is installed:

```bash
pip show nfc-plugin
```

## Build the frontend

From the plugin frontend folder:

```bash
cd path/to/nfc_plugin/frontend
npm install
npm run build
```

Use `npm run build` when you want InvenTree to load the compiled frontend assets. `npm run dev` is useful for local preview, but it does not generate the static files that InvenTree expects.

## Install NFC dependencies

Install the packages needed for NFC/PCSC communication:

```bash
sudo apt-get update
sudo apt-get install -y libpcsclite-dev pcscd pcsc-tools libccid usbutils
pip install pyscard
```

If you are also using a local NFC agent development environment, you may additionally need:

```bash
sudo apt-get install -y python3-venv
pip install nfcpy
pip install cryptnoxpy
```

## Start PC/SC service

Make sure the PC/SC daemon is running:

```bash
sudo systemctl start pcscd
sudo systemctl enable pcscd
sudo systemctl status pcscd
```

If needed, restart it:

```bash
sudo killall pcscd
sudo pcscd --foreground --debug
```

## Check reader detection

Verify that the NFC reader is plugged in:

```bash
lsusb
```

You should see your reader listed, for example:

- Feitian Technologies, Inc. SC Reader KP382

Then check reader detection with:

```bash
pcsc_scan
```

If everything is working, you should see the reader appear and cards/tags should be detected when placed on the reader.

You can also test reader access from Python:

```bash
python3 -c "
from smartcard.System import readers
r = readers()
print('Readers found:', r)
"
```

Expected output:

```bash
Readers found: [<smartcard.CardReader.CardReader>]
```

## Verify the setup

After completing all steps:

1. Start InvenTree.
2. Enable the NFC plugin in the InvenTree admin interface.
3. Open the plugin settings and confirm the agent/reader configuration.
4. Test scanning an NFC tag.
5. Confirm that the tag can be linked to a part and read back correctly.

## Common issues

### Docker permission denied

If Docker commands fail with permission errors, make sure your user belongs to the `docker` group:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Reader not detected

If `pcsc_scan` shows no reader:

- Check the USB connection.
- Confirm `pcscd` is running.
- Check `lsusb`.
- Try restarting `pcscd`.

### InvenTree does not load the plugin

If the plugin does not appear in InvenTree:

- Confirm the plugin is installed in editable mode.
- Rebuild the frontend with `npm run build`.
- Restart the InvenTree server.

### Frontend changes do not appear

If UI changes are missing:

- Rebuild the frontend.
- Refresh the browser.
- Restart the server if needed.

## Notes

This setup was developed and tested on a Linux-based dev environment with a USB NFC reader. If your environment differs, some commands may need slight adjustment.