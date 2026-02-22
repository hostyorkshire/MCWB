# Raspberry Pi Zero 2 Headless Setup Guide

This guide explains how to set up the MeshCore Weather Bot to run automatically on boot on a Raspberry Pi Zero 2 in headless mode (no display, keyboard, or mouse).

## Overview

The bot will:
- ✅ Start automatically when the Pi boots
- ✅ Automatically detect and connect to the MeshCore radio via USB
- ✅ Restart automatically if it crashes
- ✅ Run in the background without requiring a display or SSH session
- ✅ Log all activity to systemd journal for troubleshooting

## Prerequisites

- Raspberry Pi Zero 2 with Raspbian/Raspberry Pi OS installed
- MicroSD card (8GB or larger recommended)
- MeshCore companion radio (ESP32/LoRa device with MeshCore firmware)
- USB cable to connect the radio to the Pi
- Network access (WiFi or Ethernet) for the initial setup

## Initial Setup

### 1. Set Up Headless Access (First Time Only)

If you haven't already configured headless access to your Pi:

**Enable SSH:**
```bash
# On the boot partition of your SD card, create an empty file named 'ssh'
touch /boot/ssh
```

**Configure WiFi (if using WiFi):**
Create a file named `wpa_supplicant.conf` on the boot partition:
```
country=GB
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YourNetworkName"
    psk="YourPassword"
    key_mgmt=WPA-PSK
}
```

Replace `GB` with your [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) (e.g., `US` for United States, `CA` for Canada, `AU` for Australia, `DE` for Germany, `GB` for United Kingdom) to comply with local WiFi regulations. Also update the SSID and password for your network.

**📡 Remote Access:** For accessing your Pi from outside your local network (e.g., when deployed in a remote location), see the [SSH Remote Access Guide](SSH_REMOTE_ACCESS.md) for comprehensive instructions on secure remote SSH access, VPN setup, and more.

### 2. Connect to Your Pi

After booting the Pi:

```bash
# Find your Pi on the network (default hostname is raspberrypi)
ssh pi@raspberrypi.local

# Or use the IP address if .local doesn't work
ssh pi@192.168.1.xxx

# Default password is 'raspberry' (change it immediately!)
```

### 3. Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 4. Install Dependencies

```bash
# Install Python and required tools
sudo apt-get install -y python3 python3-pip git

# Optional but recommended: create a virtual environment
sudo apt-get install -y python3-venv
```

## Installing the Weather Bot

### 1. Clone the Repository

```bash
cd /home/pi
git clone https://github.com/hostyorkshire/MCWB.git
cd MCWB
```

### 2. Install Python Dependencies

```bash
# Install directly (simpler)
pip3 install -r requirements.txt

# OR use a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Connect Your MeshCore Radio

1. Connect your MeshCore companion radio to the Pi via USB
2. Verify it's detected:

```bash
ls /dev/ttyUSB* /dev/ttyACM*
# Should show /dev/ttyUSB0 or /dev/ttyACM0
```

### 4. Test the Bot Manually

Before setting up auto-start, verify the bot works:

```bash
# Test with auto-detection
python3 /home/pi/MCWB/weather_bot.py -d

# Or specify the port
python3 /home/pi/MCWB/weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d

# You should see connection messages and the bot waiting for messages
# Press Ctrl+C to stop
```

## Setting Up Auto-Start on Boot

### Method 1: Using systemd Service (Recommended)

This is the most reliable method for running the bot on boot.

#### Step 1: Customize the Service File

The repository includes a systemd service file. You may need to customize it:

```bash
# Copy the service file
sudo cp /home/pi/MCWB/weather_bot.service /etc/systemd/system/

# Edit if needed (e.g., if your username is not 'pi')
sudo nano /etc/systemd/system/weather_bot.service
```

The service file should look like this:
```ini
[Unit]
Description=MCWBv2 - MeshCore Weather Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/MCWB
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Key settings explained:**
- `User=pi` - Change this if your username is different
- `WorkingDirectory` - Directory containing the bot
- `ExecStart` - The command to run (with auto USB detection)
- `Restart=on-failure` - Restart if the bot crashes
- `RestartSec=10` - Wait 10 seconds before restarting
- `After=network-online.target` - Wait for network before starting

#### Step 2: Enable and Start the Service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable weather_bot

# Start the service now
sudo systemctl start weather_bot

# Check the status
sudo systemctl status weather_bot
```

You should see output like:
```
● weather_bot.service - MCWBv2 - MeshCore Weather Bot
   Loaded: loaded (/etc/systemd/system/weather_bot.service; enabled; vendor preset: enabled)
   Active: active (running) since ...
```

#### Step 3: Monitor the Logs

```bash
# View live logs
sudo journalctl -u weather_bot -f

# View recent logs
sudo journalctl -u weather_bot -n 50

# View logs since last boot
sudo journalctl -u weather_bot -b
```

### Method 2: Using rc.local (Alternative)

If you prefer a simpler method (though less robust):

```bash
# Edit rc.local
sudo nano /etc/rc.local
```

Add this line before `exit 0`:
```bash
# Start weather bot
/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 > /home/pi/weather_bot.log 2>&1 &
```

Make sure rc.local is executable:
```bash
sudo chmod +x /etc/rc.local
```

**Note:** This method doesn't provide automatic restarts or proper logging like systemd does.

## Verification

### Test Auto-Start

1. Reboot your Pi:
```bash
sudo reboot
```

2. Wait for the Pi to boot (30-60 seconds)

3. SSH back in and check the service:
```bash
ssh pi@raspberrypi.local
sudo systemctl status weather_bot
```

4. Verify it's running:
```bash
# Check logs
sudo journalctl -u weather_bot -n 50

# You should see connection messages and the bot listening
```

### Send a Test Message

From another MeshCore device, send a weather query:
```
wx London
```

The bot should respond on the same channel with weather information.

## Managing the Service

### Start/Stop/Restart

```bash
# Start the service
sudo systemctl start weather_bot

# Stop the service
sudo systemctl stop weather_bot

# Restart the service
sudo systemctl restart weather_bot

# Check status
sudo systemctl status weather_bot
```

### Disable Auto-Start

If you want to disable auto-start on boot:
```bash
sudo systemctl disable weather_bot
```

To re-enable:
```bash
sudo systemctl enable weather_bot
```

### Update the Bot

When updating the bot code:

```bash
cd /home/pi/MCWB
git pull
pip3 install -r requirements.txt  # If dependencies changed

# Restart the service
sudo systemctl restart weather_bot

# Check it's working
sudo systemctl status weather_bot
```

## Troubleshooting

### Service Fails to Start

**Check the logs:**
```bash
sudo journalctl -u weather_bot -n 100
```

**Common issues:**

1. **USB device not found:**
   - Check the radio is connected: `ls /dev/ttyUSB* /dev/ttyACM*`
   - Try specifying the port in the service file: `--port /dev/ttyUSB0`
   - Ensure the user has permissions: `sudo usermod -a -G dialout pi`

2. **Python dependencies missing:**
   ```bash
   cd /home/pi/MCWB
   pip3 install -r requirements.txt
   ```

3. **Permission denied:**
   ```bash
   # Add user to dialout group
   sudo usermod -a -G dialout pi
   
   # Log out and log back in, or reboot
   sudo reboot
   ```

4. **Network not ready:**
   - The service waits for network, but if your network is slow to start, increase the restart delay
   - Edit the service file and change `RestartSec=10` to `RestartSec=30`

### Bot Running But Not Responding

**Check the bot can see messages:**
```bash
# View live logs
sudo journalctl -u weather_bot -f

# Send a test message and watch for it in the logs
```

**Verify radio connection:**
- Ensure the MeshCore radio is connected to the mesh network
- Check the radio's configuration includes the weather channel
- Try debug mode: Edit service file and add `-d` to ExecStart

### USB Device Name Changes

The bot automatically detects USB ports, so it should handle device name changes (e.g., /dev/ttyUSB0 → /dev/ttyUSB1) after reboot.

If you still have issues:
```bash
# Create a udev rule for persistent naming
sudo nano /etc/udev/rules.d/99-meshcore.rules
```

Add:
```
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="meshcore"
```

Replace idVendor and idProduct with your device's values (find them with `lsusb`).

Then update the service to use `/dev/meshcore` instead of auto-detection.

### High CPU or Memory Usage

The bot is lightweight, but if you see high resource usage:

```bash
# Check resource usage
top
# Press 'M' to sort by memory, 'P' to sort by CPU

# Check bot's specific usage
ps aux | grep weather_bot
```

The bot typically uses:
- **Memory:** 20-40 MB
- **CPU:** <5% when idle, brief spikes when processing messages

### Service Stops After Some Time

If the service randomly stops:

1. **Check if it's crashing:**
   ```bash
   sudo journalctl -u weather_bot -n 200
   ```

2. **Look for Python errors in the logs**

3. **Increase restart delay** to avoid restart loops:
   ```bash
   sudo nano /etc/systemd/system/weather_bot.service
   # Change RestartSec=10 to RestartSec=30
   sudo systemctl daemon-reload
   sudo systemctl restart weather_bot
   ```

## Advanced Configuration

### Running with Announcements

To enable periodic weather announcements every 3 hours:

```bash
# Edit the service file
sudo nano /etc/systemd/system/weather_bot.service

# Change ExecStart line to:
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --announce

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
```

### Running on a Specific Channel

If you want to restrict the bot to a specific channel:

```bash
# Edit the service file
sudo nano /etc/systemd/system/weather_bot.service

# Change ExecStart line to include channel index:
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --channel-idx 1

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
```

### Filtering by Country (Location Disambiguation)

If you're deploying in a specific country, you can filter location searches to prefer cities in that country. This is useful when city names are ambiguous (e.g., "York" exists in both UK and USA):

```bash
# Edit the service file
sudo nano /etc/systemd/system/weather_bot.service

# For UK deployments, change ExecStart line to:
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --country GB

# Or for US deployments:
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --country US

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
```

**Note:** Use [ISO 3166-1 alpha-2 country codes](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) (e.g., GB, US, FR, DE, CA, AU).

### Debug Mode in Production

To run with debug logging enabled:

```bash
# Edit the service file
sudo nano /etc/systemd/system/weather_bot.service

# Change ExecStart line to:
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 -d

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
```

**Warning:** Debug mode produces verbose logs. Only use temporarily for troubleshooting.

### Resource Optimization for Pi Zero 2

The Pi Zero 2 has limited resources. Here are some tips:

1. **Reduce log retention:**
   ```bash
   sudo nano /etc/systemd/journald.conf
   # Add or modify:
   SystemMaxUse=50M
   sudo systemctl restart systemd-journald
   ```

2. **Disable unnecessary services:**
   ```bash
   # Check what's running
   systemctl list-units --type=service --state=running
   
   # Disable unnecessary services (example)
   sudo systemctl disable bluetooth
   ```

3. **Use a lightweight OS:**
   - Raspberry Pi OS Lite (no desktop environment)
   - This saves significant RAM and CPU

## Security Considerations

### Change Default Password

**Important:** Change the default 'pi' user password:
```bash
passwd
```

### Secure SSH Access

For comprehensive SSH security including key-based authentication, hardening, and remote access:
- 📖 See the [SSH Remote Access Guide](SSH_REMOTE_ACCESS.md)

Quick security improvement:
```bash
# Set up SSH key authentication instead of passwords
# See SSH_REMOTE_ACCESS.md for detailed instructions
```

### Enable Firewall (Optional)

```bash
sudo apt-get install ufw
sudo ufw allow ssh
sudo ufw enable
```

### Keep System Updated

```bash
# Set up automatic security updates
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Complete Setup Checklist

- [ ] Raspberry Pi OS installed and updated
- [ ] SSH access configured (for headless setup)
- [ ] WiFi configured (if applicable)
- [ ] Git and Python3 installed
- [ ] Repository cloned to /home/pi/MCWB
- [ ] Python dependencies installed
- [ ] MeshCore radio connected via USB
- [ ] Bot tested manually (works correctly)
- [ ] systemd service file copied and customized
- [ ] Service enabled for auto-start
- [ ] Service started and verified
- [ ] Pi rebooted to test auto-start
- [ ] Service confirmed running after reboot
- [ ] Test message sent and received
- [ ] Logs checked for errors

## Summary

Your Raspberry Pi Zero 2 is now configured to:
1. **Boot up** → Wait for network
2. **Automatically start** the weather bot service
3. **Connect** to the MeshCore radio via USB (auto-detected)
4. **Listen** for weather queries on any channel
5. **Respond** with weather information
6. **Restart automatically** if it crashes
7. **Log everything** to systemd journal for troubleshooting

The bot runs entirely in the background with no display, keyboard, or active SSH session required.

## Further Reading

- [SSH Remote Access Guide](SSH_REMOTE_ACCESS.md) - Secure remote SSH access, VPN setup, and troubleshooting
- [Main README](README.md) - Full bot documentation
- [Quick Start Guide](QUICKSTART.md) - General setup instructions
- [Channel Guide](CHANNEL_GUIDE.md) - Understanding channel behavior
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

## Support

If you encounter issues:
1. Check the logs: `sudo journalctl -u weather_bot -n 100`
2. Verify the radio connection: `ls /dev/ttyUSB* /dev/ttyACM*`
3. Review this guide's troubleshooting section
4. Check the main troubleshooting documentation
5. Open an issue on GitHub with your logs and setup details
