# Installation
 
This guide explains how to set up the InvenTree NFC plugin development environment, install the required dependencies, and verify that the NFC reader works correctly.
 
## Overview
 
The project is organized as a single repository with three main components:
 
```
NFC/
├── agent/               # Local NFC agent (communicates with the USB reader)
│   ├── agent.py
│   └── requirements.txt
├── docs/                # Documentation
├── frontend/            # React
├── nfc/                 # Python plugin package
│   ├── migrations/
│   ├── static/          # Compiled frontend assets are placed here
│   ├── tests/
│   ├── admin.py
│   ├── apps.py
│   ├── core.py          # Plugin entry point (NFC class)
│   ├── models.py
│   ├── nfc_reader.py
│   └── views.py
├── pyproject.toml       # Package definition (name: inventree-nfc)
└── MANIFEST.in
```
 
- **`nfc/`** is the Django/InvenTree plugin package. The entry point is `nfc.core:NFC`.
- **`frontend/`** holds the frontend source. Build output is copied into `nfc/static/`.
- **`agent/`** is a standalone local process that reads from the USB NFC hardware and communicates with InvenTree.
This guide is written for a Linux development machine and an InvenTree devcontainer-based workflow.
 
## Prerequisites
 
Before starting, make sure you have:
 
- A machine running Linux, macOS, or Windows 10/11 with WSL2.
- `git` installed.
- Docker and Docker Compose installed, or Docker Desktop on macOS/Windows.
- Node.js and npm installed.
- Python 3.9+ and `pip` available.
- A compatible NFC USB reader connected to the machine.
- Permission to use Docker and access USB devices, if required.

## Platform-specific notes
 
### Debian/Ubuntu
 
This guide uses Debian/Ubuntu package commands. If you are on Debian or Ubuntu, follow the steps in this file directly.
 
### Other Linux distributions
 
On Fedora, CentOS, Arch, or other distributions, use your distro's package manager to install Docker, Node.js, Python, PC/SC, and NFC reader libraries. The plugin code itself is platform-independent, but the system packages and service names vary by distribution.
 
### macOS
 
On macOS, install dependencies with Homebrew and use Docker Desktop for containers. Direct USB passthrough to Docker may be limited, so a Linux VM or remote Linux host is often easier for NFC hardware testing.
 
```bash
brew install git python node pcsc-lite
pip install pyscard
```
 
### Windows / WSL2
 
Windows can run InvenTree in Docker Desktop and use WSL2 for development. Native Windows PC/SC support usually works through the Smart Card service, but Docker may not expose USB NFC readers directly unless you use WSL2 and USB passthrough tools such as `usbipd`.
 
Use the Windows installers for Git, Node.js, and Python, or install them inside WSL2 for a Linux-style development environment.
 
## Install Docker
 
Add Docker's official GPG key:
 
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
 
You should now be able to access InvenTree in the browser.
 
## Set up the devcontainer
 
Open the repository in VS Code and reopen it in the container:
 
- Open the command palette.
- Choose **Reopen in Container**.

This will build the development containers for the InvenTree server, PostgreSQL database, and Redis cache.
 
Once inside the container, activate the virtual environment if needed: 
```bash
source /home/inventree/dev/venv/bin/activate
```
 
## Clone the plugin repository
 
If you have not already done so, clone the repository somewhere on your machine:
 
```bash
git clone <your-repo-url> NFC
cd NFC
```
 
All subsequent commands assume you are running from the root of this repository unless stated otherwise.
 
## Install the plugin
 
The plugin package is named `inventree-nfc` and its Python module is `nfc/`. Install it in editable mode from the repository root so that InvenTree picks up changes immediately:
 
```bash
pip install -e .
```
 
Verify that the package is installed:
 
```bash
pip show inventree-nfc
```
 
You should see output similar to:
 
```
Name: inventree-nfc
Location: /path/to/NFC
```
 
> **Note:** Do not manually create or copy files into `inventree-data/plugins/`. The plugin is loaded by InvenTree through the installed Python package, not by file placement.
 
## Build the frontend
 
The frontend source lives in `frontend/`. Build output is written into `nfc/static/`, where InvenTree can serve it.
 
```bash
cd frontend
npm install
npm run build
cd ..
```
 
Use `npm run build` whenever you want InvenTree to serve the latest compiled assets. `npm run dev` is useful for local frontend preview only and does not produce the files InvenTree expects.
 
## Install NFC dependencies
 
Install the system packages and Python libraries needed for NFC/PCSC communication:
 
```bash
sudo apt-get update
sudo apt-get install -y libpcsclite-dev pcscd pcsc-tools libccid usbutils
pip install pyscard
```
 
## Set up the agent
 
The `agent/` directory contains a standalone process that handles low-level communication with the USB NFC reader. Install its dependencies separately:
 
```bash
cd agent
pip install -r requirements.txt
cd ..
```
 
If you also need `nfcpy` or `cryptnoxpy` support:
 
```bash
pip install nfcpy cryptnoxpy
```
 
## Start the PC/SC service
 
Make sure the PC/SC daemon is running before you test the reader:
 
```bash
sudo systemctl start pcscd
sudo systemctl enable pcscd
sudo systemctl status pcscd
```
 
If you need to restart it:
 
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
 
```
Feitian Technologies, Inc. SC Reader KP382
```
 
Then check reader detection with:
 
```bash
pcsc_scan
```
 
If everything is working, the reader will appear and cards or tags will be detected when placed on it.
 
You can also verify reader access from Python:
 
```bash
python3 -c "
from smartcard.System import readers
r = readers()
print('Readers found:', r)
"
```
 
Expected output:
 
```
Readers found: [<smartcard.CardReader.CardReader>]
```
 
## Verify the full setup
 
After completing all steps:
 
1. Start InvenTree (`docker compose up -d`).
2. Enable the NFC plugin in the InvenTree admin interface.
3. Open the plugin settings and confirm the agent/reader configuration.
4. Start the agent from the `agent/` directory.
5. Test scanning an NFC tag.
6. Confirm that the tag can be linked to a part and read back correctly.

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
 
- Confirm `pip show inventree-nfc` shows the correct install location.
- Make sure you ran `pip install -e .` from the repository root.
- Rebuild the frontend with `npm run build` from the `frontend/` directory.
- Restart the InvenTree server.

### Frontend changes do not appear
 
If UI changes are missing:
 
- Run `npm run build` from the `frontend/` directory.
- Refresh the browser (hard refresh if needed).
- Restart the InvenTree server.

## Notes
 
This setup was developed and tested on a Linux-based development environment with a USB NFC reader. If your environment differs, some commands may need slight adjustment.
 
