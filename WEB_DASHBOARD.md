# MCWB Web Dashboard

A dark-themed web interface for monitoring the MeshCore Weather Bot in real-time.

## Features

- 🌙 **Dark Theme** - Easy on the eyes with a beautiful gradient background
- 📊 **Real-time Status** - Monitor bot status and log file information
- 📝 **Log Viewer** - View and filter bot logs with color-coded entries
- 🔄 **Auto-refresh** - Automatically updates every 10 seconds
- 📱 **Responsive** - Works on desktop, tablet, and mobile devices

## Quick Start

> **🚀 For Raspberry Pi users:** Jump to the [Running on Raspberry Pi](#running-on-raspberry-pi) section to set up the dashboard as a systemd service that starts automatically on boot.

### Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Running the Dashboard

Start the web dashboard:

```bash
python3 web_dashboard.py
```

By default, the dashboard will be available at:
- **Local access:** http://localhost:5000

To allow network access from other devices:
```bash
python3 web_dashboard.py --host 0.0.0.0
```
Then access at: **http://[your-ip]:5000**

### Command-Line Options

```bash
# Run on a specific host and port
python3 web_dashboard.py --host 0.0.0.0 --port 8080

# Run in debug mode
python3 web_dashboard.py --debug

# View help
python3 web_dashboard.py --help
```

## Usage

### Dashboard Sections

1. **System Status** - Shows the current status of the bot and log file information
2. **Log Viewer** - View logs from different sources:
   - Bot Log - Main weather bot logs
   - Bot Errors - Error logs from the bot
   - MeshCore - MeshCore communication logs
   - MeshCore Errors - MeshCore error logs

### Features

- Click on different log tabs to switch between log sources
- Logs auto-refresh every 10 seconds
- Click the "🔄 Refresh" button to manually refresh
- Log entries are color-coded:
  - 🔴 Red - ERROR and CRITICAL messages
  - 🟡 Yellow - WARNING messages
  - 🔵 Blue - INFO messages
  - ⚪ White - Other messages

## Running on Raspberry Pi

To run the dashboard on boot, use the included installation script:

### Method 1: Automated Installation (Recommended)

The repository includes an installation script that automatically configures the systemd service for your system:

```bash
cd /home/pi/MCWB  # Or wherever you cloned the repository
./install_dashboard_service.sh
```

The script will:
- ✅ Detect your username and installation directory automatically
- ✅ Check Python dependencies and install if needed
- ✅ Create a customized systemd service file for your system
- ✅ Install and enable the service
- ✅ Optionally start the service immediately

**Example usage:**
```bash
# Navigate to the MCWB directory
cd ~/MCWB

# Run the installer (don't use sudo)
./install_dashboard_service.sh

# Follow the prompts to install and start the service
```

After installation, the dashboard will:
- Start automatically on boot
- Restart automatically if it crashes
- Be accessible on your network

### Method 2: Manual Installation

If you prefer to install manually:

1. Create a service file:

```bash
sudo nano /etc/systemd/system/mcwb-dashboard.service
```

2. Add the following content:

> **⚠️ IMPORTANT:** Customize the `User` and `WorkingDirectory` to match your system:
> - Replace `pi` with your actual username (e.g., `weatherbot`, `ubuntu`, etc.)
> - Update the paths to match where you cloned the MCWB repository
> - Both the `WorkingDirectory` and paths in `ExecStart` should use the same base directory

```ini
[Unit]
Description=MCWB Web Dashboard
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/MCWB
ExecStart=/usr/bin/python3 /home/pi/MCWB/web_dashboard.py --host 0.0.0.0 --port 5000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Example for user 'weatherbot' with installation in /home/weatherbot/MCWB:**
```ini
[Unit]
Description=MCWB Web Dashboard
After=network.target

[Service]
Type=simple
User=weatherbot
WorkingDirectory=/home/weatherbot/MCWB
ExecStart=/usr/bin/python3 /home/weatherbot/MCWB/web_dashboard.py --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

3. Reload systemd and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcwb-dashboard.service
sudo systemctl start mcwb-dashboard.service
```

4. Check status:

```bash
sudo systemctl status mcwb-dashboard.service
```

If the service fails to start, check the troubleshooting section below.

## Security Notes

- By default, the dashboard binds to `127.0.0.1` (localhost only) for security
- To allow network access, use `--host 0.0.0.0` (only on trusted networks)
- For production use, consider:
  - Using a reverse proxy (nginx, Apache) with SSL/TLS
  - Implementing authentication
  - Restricting access to specific IP addresses
  - Using a firewall to limit access

## Troubleshooting

### Systemd Service Fails to Start

If you see `Active: activating (auto-restart)` or `Active: failed`, check the following:

**RECOMMENDED FIX: Use the Automated Installer**

The easiest way to fix service issues is to reinstall using the automated installation script:

```bash
cd ~/MCWB  # Or wherever you installed MCWB

# If the service is installed, uninstall it first
sudo systemctl stop mcwb-dashboard 2>/dev/null || true
sudo systemctl disable mcwb-dashboard 2>/dev/null || true
sudo rm /etc/systemd/system/mcwb-dashboard.service 2>/dev/null || true
sudo systemctl daemon-reload

# Run the installer (it automatically detects your username and paths)
./install_dashboard_service.sh
```

**Manual Troubleshooting:**

If you prefer to troubleshoot manually, check the following:

**1. Exit Code 217/USER - User does not exist:**

This error occurs when the `User=` setting in the service file doesn't match your actual username.

```bash
# Check your username
whoami

# View the service file to see what user it's configured for
sudo grep User= /etc/systemd/system/mcwb-dashboard.service
```

Solution: The automated installer (`install_dashboard_service.sh`) fixes this automatically, or update manually:
```bash
sudo nano /etc/systemd/system/mcwb-dashboard.service
# Change User=pi to User=yourname (e.g., User=weatherbot)
# Also update WorkingDirectory and ExecStart paths to match
sudo systemctl daemon-reload
sudo systemctl restart mcwb-dashboard.service
```

**2. Corrupted Configuration - Port number appears as `8&gt;` or similar:**

If you copied the configuration from a web browser, HTML entities may have corrupted the text. The port should be a number like `5000` or `8080`, not `8&gt;`.

Solution: The automated installer prevents this issue, or fix manually:
```bash
# Edit the service file and fix the port number
sudo nano /etc/systemd/system/mcwb-dashboard.service
# Change: ExecStart=/usr/bin/python3 ... --port 8&gt;
# To:     ExecStart=/usr/bin/python3 ... --port 5000
sudo systemctl daemon-reload
sudo systemctl restart mcwb-dashboard.service
```

**3. Path does not exist:**

Ensure all paths in the service file are correct:
```bash
# Verify the MCWB directory exists
ls /home/pi/MCWB/web_dashboard.py
# Or if installed elsewhere:
ls /home/weatherbot/MCWB/web_dashboard.py

# Check Python path
which python3
```

**4. View detailed error logs:**

```bash
# View recent service logs
sudo journalctl -u mcwb-dashboard.service -n 50

# View live logs
sudo journalctl -u mcwb-dashboard.service -f

# Check for permission errors
sudo journalctl -u mcwb-dashboard.service | grep -i "permission\|denied\|error"
```

### Port Already in Use

If port 5000 is already in use, specify a different port:

```bash
python3 web_dashboard.py --port 8080
```

### Cannot Access from Another Device

Make sure:
1. The dashboard is running with `--host 0.0.0.0`
2. Firewall allows incoming connections on the port
3. You're using the correct IP address of the host machine

### Logs Not Showing

Make sure:
1. The weather bot is running and generating logs
2. Log files exist in the `logs/` directory
3. The web dashboard has read permissions for the log files

## Design

The dashboard features:
- Dark gradient background (#1a1a2e to #16213e)
- Glassmorphic cards with transparency
- Blue accent color (#60a5fa)
- Smooth animations and transitions
- Custom-styled scrollbars
- Responsive grid layout

## License

Same as MCWB - See LICENSE file for details.
