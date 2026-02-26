# MCWB - Frequently Asked Questions (FAQ)

Quick answers to common questions about the MeshCore Weather Bot.

## Table of Contents
- [Setup & Installation](#setup--installation)
- [Raspberry Pi & Boot Options](#raspberry-pi--boot-options)
- [Usage & Commands](#usage--commands)
- [Troubleshooting](#troubleshooting)
- [Dashboard & Web Interface](#dashboard--web-interface)

---

## Setup & Installation

### Where is the script for setting up boot options for Raspberry Pi?

**Answer:** There are multiple scripts available depending on your needs:

1. **`setup_mcwb.sh`** - **Recommended for most users**
   - Interactive menu-based setup tool
   - Handles both Weather Bot and Dashboard installation
   - Easy-to-use interface with status display
   - Location: Root of the MCWB directory
   - Usage: `./setup_mcwb.sh`
   - Documentation: [SETUP_MENU_GUIDE.md](SETUP_MENU_GUIDE.md)

2. **`install_service.sh`** - Direct Weather Bot service installation
   - Automated installation of weather bot systemd service
   - Configures auto-start on boot
   - Location: Root of the MCWB directory
   - Usage: `./install_service.sh`
   - Documentation: [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)

3. **`install_dashboard_service.sh`** - Dashboard service installation
   - Automated installation of web dashboard systemd service
   - Location: Root of the MCWB directory
   - Usage: `./install_dashboard_service.sh`

**Quick Setup:**
```bash
cd /home/pi/MCWB
./setup_mcwb.sh
# Select option 3 to install both services
```

### How do I make the bot start automatically on boot?

Use the setup script to install it as a systemd service:

```bash
cd /home/pi/MCWB
./install_service.sh
```

This will:
- Configure the bot to run as a system service
- Enable auto-start on boot
- Set up USB permissions
- Start the service immediately

See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for complete instructions.

### What's the difference between the installation scripts?

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `setup_mcwb.sh` | Interactive menu for all services | First-time setup, managing services |
| `install_service.sh` | Install weather bot service only | Just want the weather bot |
| `install_dashboard_service.sh` | Install dashboard service only | Just want the web dashboard |

**Recommendation:** Use `setup_mcwb.sh` for the easiest experience!

### Do I need to run the setup as root/sudo?

**No!** Run the scripts as a normal user:
```bash
./setup_mcwb.sh
```

The scripts will ask for your sudo password when needed for specific operations.

---

## Raspberry Pi & Boot Options

### Which Raspberry Pi models are supported?

All models are supported, but **Raspberry Pi Zero 2** is specifically tested and documented for headless operation:
- ✅ Raspberry Pi Zero 2 W (recommended for portability)
- ✅ Raspberry Pi 3
- ✅ Raspberry Pi 4
- ✅ Raspberry Pi 5

See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for Pi-specific instructions.

### Can I run the bot in headless mode (no display)?

**Yes!** The bot is designed for headless operation:
- SSH access only
- No display required
- Auto-starts on boot
- Logs accessible via systemd journal

Complete headless setup guide: [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)

### How do I check if the service is running?

```bash
# Check status
sudo systemctl status weather_bot

# View live logs
sudo journalctl -u weather_bot -f

# Quick status check
sudo systemctl is-active weather_bot
```

### How do I stop or restart the service?

```bash
# Stop
sudo systemctl stop weather_bot

# Start
sudo systemctl start weather_bot

# Restart
sudo systemctl restart weather_bot

# Disable auto-start on boot
sudo systemctl disable weather_bot
```

Or use the interactive menu:
```bash
./setup_mcwb.sh
# Select option 5: Start/Stop services
```

---

## Usage & Commands

### What commands does the bot respond to?

The bot responds to weather queries starting with `wx` or `weather`:

```
wx Seattle
weather 98101
wx Paris, France
weather london
```

See [README.md](README.md#usage) for more examples.

### Do I need to configure channel IDs?

**No!** By default, the bot:
- Listens on ALL channels (0-7)
- Responds on the SAME channel where the request came from
- Works automatically without configuration

See [docs/FAQ_CHANNEL_DETECTION.md](docs/FAQ_CHANNEL_DETECTION.md) for details.

### How do I enable periodic weather announcements?

Edit the service file to add the `--announce` and `--weather-channel-idx` parameters:

```bash
sudo nano /etc/systemd/system/weather_bot.service
```

Change the ExecStart line to:
```
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --announce --weather-channel-idx 1
```

Then restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
```

**How announcements work:**
- The bot sends periodic announcements every 3 hours during normal operation
- On reboot, it will ALWAYS announce immediately to let users know the bot is operational
- This ensures users are aware the bot is active, regardless of when the last announcement was sent
- The `--weather-channel-idx 1` ensures announcements go to channel_idx 1 (typically the #weather channel)
- Change the channel index if your #weather channel uses a different channel_idx

**Note:** The service file in the repository now includes these flags by default.

See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md#enabling-weather-announcements) for more details.

---

## Troubleshooting

### The bot isn't responding to commands

1. **Check if the service is running:**
   ```bash
   sudo systemctl status weather_bot
   ```

2. **Check the logs for errors:**
   ```bash
   sudo journalctl -u weather_bot -n 50
   ```

3. **Verify USB connection:**
   ```bash
   ls -la /dev/ttyUSB* /dev/ttyACM*
   ```

4. **Check user permissions:**
   ```bash
   groups $USER | grep dialout
   ```
   If not in dialout group, add yourself:
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more solutions.

### USB device not found or permission denied

**Solution:**
1. Add your user to the dialout group:
   ```bash
   sudo usermod -a -G dialout $USER
   ```

2. Log out and back in (or reboot)

3. Verify permissions:
   ```bash
   ls -l /dev/ttyUSB0
   groups $USER
   ```

The `install_service.sh` script does this automatically.

### Service fails to start after reboot

Check the logs:
```bash
sudo journalctl -u weather_bot -b
```

Common issues:
- Network not ready (service should wait for network-online.target)
- USB device not detected
- Python dependencies missing

See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md#troubleshooting) for detailed solutions.

### How do I update the bot to the latest version?

```bash
cd /home/pi/MCWB
git pull
pip3 install -r requirements.txt
sudo systemctl restart weather_bot
```

---

## Dashboard & Web Interface

### How do I access the web dashboard?

After installing the dashboard service:

```bash
# Get your Pi's IP address
hostname -I

# Access dashboard at:
# http://[your-pi-ip]:5000
```

Example: `http://192.168.1.100:5000`

See [WEB_DASHBOARD.md](WEB_DASHBOARD.md) for complete dashboard documentation.

### Can I access the dashboard remotely (outside my network)?

Yes! See [SSH_REMOTE_ACCESS.md](SSH_REMOTE_ACCESS.md) for:
- Port forwarding
- VPN setup (Tailscale/WireGuard)
- Dynamic DNS
- Security best practices

### Dashboard shows "Cannot connect to bot"

1. **Verify weather bot is running:**
   ```bash
   sudo systemctl status weather_bot
   ```

2. **Check if both services are enabled:**
   ```bash
   sudo systemctl is-active weather_bot mcwb-dashboard
   ```

3. **Review dashboard logs:**
   ```bash
   sudo journalctl -u mcwb-dashboard -n 50
   ```

See [DASHBOARD_CONNECTIVITY_TROUBLESHOOTING.md](DASHBOARD_CONNECTIVITY_TROUBLESHOOTING.md) for detailed solutions.

---

## Additional Resources

### Complete Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Main documentation, getting started |
| [QUICKSTART.md](QUICKSTART.md) | Quick setup guide |
| [QUICKSTART_SIMPLE.md](QUICKSTART_SIMPLE.md) | Simplified quick start |
| [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) | Complete Pi setup guide |
| [SETUP_MENU_GUIDE.md](SETUP_MENU_GUIDE.md) | setup_mcwb.sh usage |
| [WEB_DASHBOARD.md](WEB_DASHBOARD.md) | Dashboard documentation |
| [SSH_REMOTE_ACCESS.md](SSH_REMOTE_ACCESS.md) | Remote access guide |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Problem-solving guide |
| [CONNECTION_GUIDE.md](CONNECTION_GUIDE.md) | MeshCore connection help |

### Quick Reference Commands

```bash
# Installation
./setup_mcwb.sh                    # Interactive setup menu
./install_service.sh               # Install weather bot service

# Service Management
sudo systemctl status weather_bot   # Check status
sudo systemctl start weather_bot    # Start service
sudo systemctl stop weather_bot     # Stop service
sudo systemctl restart weather_bot  # Restart service

# Logs
sudo journalctl -u weather_bot -f   # Follow logs
sudo journalctl -u weather_bot -n 50 # Last 50 lines
./viewlogs.py                       # View log files

# Updates
cd /home/pi/MCWB && git pull        # Update code
pip3 install -r requirements.txt    # Update dependencies
sudo systemctl restart weather_bot  # Restart to apply
```

### Getting Help

- **Issues:** [GitHub Issues](https://github.com/hostyorkshire/MCWB/issues)
- **Documentation:** Check the guides listed above
- **Logs:** Always check logs when troubleshooting: `sudo journalctl -u weather_bot -n 50`

---

## Still Have Questions?

If your question isn't answered here:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Search existing [GitHub Issues](https://github.com/hostyorkshire/MCWB/issues)
3. Open a new issue with details about your setup and the problem
