# MCWB Web Dashboard

A dark-themed web interface for monitoring the MeshCore Weather Bot in real-time.

## Features

- 🌙 **Dark Theme** - Easy on the eyes with a beautiful gradient background
- 📊 **Real-time Status** - Monitor bot status and log file information
- 📝 **Log Viewer** - View and filter bot logs with color-coded entries
- 🔄 **Auto-refresh** - Automatically updates every 10 seconds
- 📱 **Responsive** - Works on desktop, tablet, and mobile devices

## Quick Start

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

To run the dashboard on boot, you can create a systemd service:

1. Create a service file:

```bash
sudo nano /etc/systemd/system/mcwb-dashboard.service
```

2. Add the following content:

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

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
sudo systemctl enable mcwb-dashboard.service
sudo systemctl start mcwb-dashboard.service
```

4. Check status:

```bash
sudo systemctl status mcwb-dashboard.service
```

## Security Notes

- By default, the dashboard binds to `127.0.0.1` (localhost only) for security
- To allow network access, use `--host 0.0.0.0` (only on trusted networks)
- For production use, consider:
  - Using a reverse proxy (nginx, Apache) with SSL/TLS
  - Implementing authentication
  - Restricting access to specific IP addresses
  - Using a firewall to limit access

## Troubleshooting

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
