# Raspberry Pi Zero 2 Headless Setup Guide

This guide explains how to set up the MeshCore Weather Bot to run automatically on boot on a Raspberry Pi Zero 2 in headless mode (no display, keyboard, or mouse).

## Table of Contents

1. [Complete Raspberry Pi OS Lite Setup (For New Pi Zero 2W)](#complete-raspberry-pi-os-lite-setup-for-new-pi-zero-2w)
2. [Overview](#overview)
3. [Prerequisites](#prerequisites)
4. [Initial Setup](#initial-setup)
5. [Installing the Weather Bot](#installing-the-weather-bot)
6. [Setting Up Auto-Start on Boot](#setting-up-auto-start-on-boot)
7. [Verification](#verification)
8. [Managing the Service](#managing-the-service)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Configuration](#advanced-configuration)
11. [Security Considerations](#security-considerations)

---

## Complete Raspberry Pi OS Lite Setup (For New Pi Zero 2W)

**This section provides comprehensive step-by-step instructions for setting up a brand new Raspberry Pi Zero 2W with Raspberry Pi OS Lite from scratch.** If you already have your Pi set up and can SSH into it, skip to the [Initial Setup](#initial-setup) section.

### What You'll Need

- **Raspberry Pi Zero 2W** (the wireless model)
- **MicroSD card** (16GB or larger recommended, Class 10 or better)
- **SD card reader** for your computer
- **USB cable** (for power and data connection to MeshCore radio)
- **Power supply** (5V, 2.5A recommended for stability)
- **Computer** (Windows, Mac, or Linux) for setting up the SD card
- **WiFi network** with internet access (for initial setup)
- **MeshCore companion radio** (ESP32/LoRa device with MeshCore firmware)

### Step 1: Download Raspberry Pi OS Lite

Raspberry Pi OS Lite is a minimal, command-line-only version without a desktop environment - perfect for headless deployments.

1. **Visit the Raspberry Pi Downloads Page:**
   - Go to https://www.raspberrypi.com/software/operating-systems/
   
2. **Download Raspberry Pi OS Lite (64-bit):**
   - Scroll to **"Raspberry Pi OS (64-bit)"** section
   - Click **"Raspberry Pi OS Lite"** download link
   - The file will be named something like: `2024-xx-xx-raspios-bookworm-arm64-lite.img.xz`
   - **Note:** Choose the 64-bit version for Pi Zero 2W (it has a 64-bit processor)
   
3. **Alternative: Use the Raspberry Pi Imager (Recommended - Easier)**
   - Download from: https://www.raspberrypi.com/software/
   - Install it on your computer (available for Windows, Mac, Linux)
   - We'll use this in the next step

### Step 2: Flash the OS to Your SD Card

We'll use the **Raspberry Pi Imager** which makes the process much easier and allows us to preconfigure WiFi, SSH, and user settings.

#### Using Raspberry Pi Imager (Recommended)

1. **Launch Raspberry Pi Imager**
   - Insert your microSD card into your computer's SD card reader
   - Open the Raspberry Pi Imager application

2. **Choose the Operating System**
   - Click **"Choose OS"**
   - Select **"Raspberry Pi OS (other)"**
   - Select **"Raspberry Pi OS Lite (64-bit)"**
   - This is the command-line only version without desktop

3. **Choose Your SD Card**
   - Click **"Choose Storage"**
   - Select your microSD card
   - ⚠️ **WARNING:** All data on this card will be erased!

4. **Configure Advanced Settings (CRITICAL STEP)**
   - Click the **gear icon** (⚙️) in the bottom right corner, or press `Ctrl+Shift+X`
   - This opens the advanced options menu where we'll preconfigure everything

5. **Configure Hostname (Optional but Recommended)**
   - Check **"Set hostname"**
   - Enter: `raspberrypi` (or choose your own, e.g., `weatherbot`)
   - This is how you'll identify your Pi on the network

6. **Enable SSH (REQUIRED for Headless Setup)**
   - Check **"Enable SSH"**
   - Select **"Use password authentication"** (or use SSH keys if you're familiar)
   - This allows you to connect remotely without a monitor

7. **Set Username and Password (REQUIRED)**
   - Check **"Set username and password"**
   - Username: `pi` (default, or choose your own)
   - Password: Enter a strong password (you'll use this to log in)
   - ⚠️ **Important:** Remember these credentials!

8. **Configure WiFi (REQUIRED for Headless Setup)**
   - Check **"Configure wireless LAN"**
   - **SSID:** Enter your WiFi network name (case-sensitive!)
   - **Password:** Enter your WiFi password
   - **Wireless LAN country:** Select your country (e.g., GB, US, CA, AU, DE)
     - This is required for legal compliance with local WiFi regulations
     - Use [ISO 3166-1 alpha-2 country codes](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)

9. **Set Locale Settings (Optional)**
   - Check **"Set locale settings"**
   - **Time zone:** Select your timezone (e.g., Europe/London, America/New_York)
   - **Keyboard layout:** Select your keyboard layout (e.g., us, gb)

10. **Save and Write**
    - Click **"Save"** to save your advanced settings
    - Click **"Write"** to begin flashing the SD card
    - Confirm the warning (this will erase the SD card)
    - Wait for the process to complete (5-10 minutes)
    - When finished, you'll see "Write Successful"

11. **Safely Eject the SD Card**
    - Close the Imager
    - Safely eject/unmount the SD card from your computer

#### Alternative: Manual Configuration (If Not Using Imager Advanced Options)

If you flashed the image without using the advanced options, you'll need to manually configure SSH and WiFi:

**Enable SSH:**
```bash
# On Windows (in boot partition):
cd /d E:\  # Replace E: with your SD card boot drive letter
type nul > ssh

# On Mac/Linux (in boot partition):
cd /Volumes/bootfs  # Or wherever your boot partition is mounted
touch ssh
```

**Configure WiFi:**

Create a file named `wpa_supplicant.conf` on the boot partition:

```bash
# On Windows, create the file with Notepad
# On Mac/Linux, use your text editor

# File contents:
country=GB
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YourNetworkName"
    psk="YourPassword"
    key_mgmt=WPA-PSK
}
```

Replace:
- `GB` with your country code (e.g., `US`, `CA`, `AU`, `DE`)
- `YourNetworkName` with your WiFi SSID (case-sensitive!)
- `YourPassword` with your WiFi password

**Create User (for newer Raspberry Pi OS versions):**

Create a file named `userconf.txt` on the boot partition with your username and hashed password:

```bash
# On Mac/Linux, generate the hashed password:
echo 'yourpassword' | openssl passwd -6 -stdin

# Create userconf.txt with:
pi:$6$encrypted_password_here

# On Windows, use an online bcrypt generator or the Pi after first boot
```

### Step 3: First Boot and Connection

Now that everything is configured, let's boot up your Pi and connect to it.

1. **Insert the SD Card into Your Pi Zero 2W**
   - Make sure the Pi is powered off
   - Insert the microSD card into the Pi's SD card slot

2. **Power On the Pi**
   - Connect the power supply to your Pi Zero 2W
   - The green LED should start flashing (indicating SD card activity)
   - Wait 30-90 seconds for first boot to complete
   - The Pi will automatically:
     - Resize the filesystem to use the full SD card
     - Connect to your WiFi network
     - Enable SSH

3. **Find Your Pi on the Network**

   On your computer, open a terminal (Command Prompt on Windows, Terminal on Mac/Linux):

   ```bash
   # Try connecting via hostname (easiest):
   ssh pi@raspberrypi.local
   
   # If that doesn't work, find the IP address:
   # On Mac/Linux:
   ping raspberrypi.local
   
   # On Windows:
   ping raspberrypi.local
   # Or use: arp -a | findstr b8-27
   
   # On your router's admin page, look for "raspberrypi" in connected devices
   ```

4. **SSH into Your Pi**

   ```bash
   # Connect using hostname:
   ssh pi@raspberrypi.local
   
   # Or using IP address if hostname doesn't work:
   ssh pi@192.168.1.XXX  # Replace with your Pi's actual IP
   
   # Enter the password you set during imaging
   ```

   On first connection, you'll see a warning about the host authenticity. Type `yes` to continue.

5. **You're In!**
   
   You should now see the Raspberry Pi OS command prompt:
   ```
   pi@raspberrypi:~ $
   ```

### Step 4: Initial System Configuration

Now that you're connected, let's configure your Pi using the command-line configuration tool.

```bash
# Launch the Raspberry Pi Configuration Tool
sudo raspi-config
```

**Navigate through the menu using arrow keys, Enter to select, Tab to move between options, and Escape to go back.**

#### Recommended Configuration Steps:

1. **System Options (Option 1)**
   - **S1 Wireless LAN** - Verify WiFi is configured (skip if already working)
   - **S3 Password** - Change your password if you used a temporary one
   - **S4 Hostname** - Change hostname if desired (e.g., `weatherbot`)
   
2. **Interface Options (Option 3)**
   - **I2 SSH** - Ensure SSH is enabled (should already be enabled)
   - **I6 Serial Port** - Keep login shell **disabled**, but hardware **enabled** (for serial devices)

3. **Localisation Options (Option 5)**
   - **L1 Locale** - Set locale (e.g., `en_GB.UTF-8` or `en_US.UTF-8`)
   - **L2 Timezone** - Set your timezone (e.g., Europe/London, America/New_York)
   - **L3 Keyboard** - Set keyboard layout (usually `Generic 104-key` → `English (US)` or `English (UK)`)
   - **L4 WLAN Country** - Set WiFi country code (should match what you set earlier)

4. **Performance Options (Option 4)** - Optional
   - **P2 GPU Memory** - Set to `16` (minimum, since no desktop) to save RAM

5. **Advanced Options (Option 6)**
   - **A1 Expand Filesystem** - Should be done automatically, but verify
   - **A6 Boot Order** - Leave as default (SD card)

6. **Finish and Reboot**
   - Tab to `<Finish>`
   - Select `Yes` to reboot if prompted
   - If not prompted, manually reboot: `sudo reboot`

Wait 30 seconds, then SSH back in:
```bash
ssh pi@raspberrypi.local
```

### Step 5: Update System and Install Core Tools

Once reconnected, update your system and install essential tools:

```bash
# Update package list
sudo apt-get update

# Upgrade all installed packages (this may take 10-15 minutes)
sudo apt-get upgrade -y

# Install essential development tools
sudo apt-get install -y git python3 python3-pip python3-venv

# Optional but recommended tools for troubleshooting
sudo apt-get install -y htop vim nano curl wget

# Clean up
sudo apt-get autoremove -y
sudo apt-get clean
```

### Step 6: Configure User Permissions for Serial/USB

The weather bot needs to access USB serial devices. Add your user to the necessary groups:

```bash
# Add user to dialout group (for serial port access)
sudo usermod -a -G dialout $USER

# Add user to gpio group (optional, for GPIO access)
sudo usermod -a -G gpio $USER

# Verify groups
groups

# Log out and back in for changes to take effect
exit
```

SSH back in:
```bash
ssh pi@raspberrypi.local
```

Verify the group membership:
```bash
groups
# Should show: pi dialout gpio ... and other groups
```

### Step 7: Verify Your Setup

Before installing the weather bot, verify everything is working:

```bash
# Check system info
uname -a
# Should show: Linux raspberrypi 6.x.x ... aarch64 GNU/Linux

# Check Python version
python3 --version
# Should be Python 3.11 or newer

# Check pip
pip3 --version

# Check Git
git --version

# Check disk space
df -h
# Should have several GB free on /dev/root

# Check memory
free -h

# Check network
ping -c 3 google.com
# Should show successful responses

# Check WiFi signal strength
iwconfig wlan0
# Should show link quality and signal level
```

### Step 8: Set Up Static IP (Optional but Recommended)

For reliability, especially if deploying remotely, set a static IP address:

```bash
# Edit dhcpcd configuration
sudo nano /etc/dhcpcd.conf

# Scroll to the bottom and add (modify for your network):
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8

# Save: Ctrl+O, Enter
# Exit: Ctrl+X

# Reboot to apply
sudo reboot
```

Replace:
- `192.168.1.100` with your desired static IP (check your router's DHCP range)
- `192.168.1.1` with your router's IP address
- DNS servers as needed

After reboot, SSH using the new static IP:
```bash
ssh pi@192.168.1.100
```

### Step 9: Set Up Time Synchronization (Important for Logging)

Ensure your Pi has the correct time:

```bash
# Check current time
timedatectl

# Enable NTP (should be enabled by default)
sudo timedatectl set-ntp true

# Verify
timedatectl
# "System clock synchronized: yes" should show
```

### You're Ready!

Your Raspberry Pi Zero 2W is now fully configured with Raspberry Pi OS Lite and ready for the weather bot installation. Continue with the [Installing the Weather Bot](#installing-the-weather-bot) section below.

**Quick Checklist:**
- ✅ Raspberry Pi OS Lite installed and booted
- ✅ SSH access working
- ✅ WiFi connected to internet
- ✅ System updated and upgraded
- ✅ Git, Python3, pip installed
- ✅ User added to dialout group
- ✅ System time synchronized
- ✅ (Optional) Static IP configured

---

## Overview

The bot will:
- ✅ Start automatically when the Pi boots
- ✅ Automatically detect and connect to the MeshCore radio via USB
- ✅ Restart automatically if it crashes
- ✅ Run in the background without requiring a display or SSH session
- ✅ Log all activity to systemd journal for troubleshooting

## Prerequisites

**If starting from scratch:** Follow the [Complete Raspberry Pi OS Lite Setup](#complete-raspberry-pi-os-lite-setup-for-new-pi-zero-2w) section above for comprehensive instructions from downloading to first boot.

**If you already have your Pi set up:**
- Raspberry Pi Zero 2 with Raspberry Pi OS (Lite or Desktop) installed
- SSH access to your Pi
- MicroSD card (8GB or larger, 16GB+ recommended)
- MeshCore companion radio (ESP32/LoRa device with MeshCore firmware)
- USB cable to connect the radio to the Pi
- Network access (WiFi or Ethernet) for the initial setup
- Python 3.11+ installed (comes with Raspberry Pi OS)

## Initial Setup

**Note:** If you followed the [Complete Raspberry Pi OS Lite Setup](#complete-raspberry-pi-os-lite-setup-for-new-pi-zero-2w) section above, you've already completed most of these steps. You can skip to [Installing the Weather Bot](#installing-the-weather-bot).

### 1. Set Up Headless Access (First Time Only)

If you haven't already configured headless access to your Pi (and didn't use the Raspberry Pi Imager advanced options):

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
# Or use the password you set during imaging
```

### 3. Update System

**Note:** Skip this if you just completed the full setup above.

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 4. Install Dependencies

**Note:** Skip this if you just completed the full setup above.

```bash
# Install Python and required tools
sudo apt-get install -y python3 python3-pip git

# Optional but recommended: create a virtual environment
sudo apt-get install -y python3-venv

# Add user to dialout group for serial port access
sudo usermod -a -G dialout $USER

# Log out and back in for group changes to take effect
exit
# Then SSH back in
```

## Installing the Weather Bot

### 1. Clone the Repository

```bash
cd /home/pi
git clone https://github.com/yourusername/MCWB.git
cd MCWB
```

### 2. Install Python Dependencies

**Recommended: Use a virtual environment** (prevents PEP 668 errors on newer Raspberry Pi OS):

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** The automated installer (`install_service.sh` and `install_dashboard_service.sh`) handles virtual environment setup automatically, including updating the service file to use the venv's Python interpreter.

**Alternative: Manual venv setup** (not recommended, use the automated installer instead):
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

Then update the service file to use `/home/pi/MCWB/venv/bin/python3` instead of `/usr/bin/python3`.

**Note:** On newer systems (Debian 12+, Ubuntu 23.04+), `pip3 install --user` will fail with "externally-managed-environment" error due to PEP 668. Always use a virtual environment or the automated installers.

### 3. Connect Your MeshCore Radio

**CRITICAL STEP:** Before connecting the radio, you must configure which channels it should monitor.

#### Configure Channels First (Required)

1. **Using the MeshCore mobile app:**
   - Open the MeshCore app on your phone/tablet
   - Connect to your companion radio
   - Go to Channel Settings
   - Join/subscribe to the channels you want the bot to monitor
   - Common channels: `#weather`, `#wxtest`, `#forecast`, etc.
   - **Important:** The bot software cannot add channels for you - this MUST be done through the MeshCore app

2. **Why this matters:**
   - The companion radio protocol does not provide commands to subscribe to channels programmatically
   - If you skip this step, the bot won't receive messages from those channels
   - You can always add more channels later, but you'll need to restart the bot

#### Connect the Radio

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

### 🎛️ Method 1: Unified Service Manager (Easiest!)

**NEW: One menu for all services!**

```bash
cd ~/MCWB
./setup_mcwb.sh
```

This interactive menu provides:
- ✅ **Option 3: Install BOTH services** - Weather bot + web dashboard at once
- ✅ Automatic configuration (username, paths, firewall)
- ✅ Service management (start/stop/restart)
- ✅ Log viewing
- ✅ Status checking

**Recommended for first-time setup!** No need to remember multiple scripts.

### Method 2: Individual Installation Scripts

You can also use the individual scripts directly:

**For Weather Bot:**
```bash
./install_service.sh
```

**For Web Dashboard:**
```bash
./install_dashboard_service.sh
```

### Method 3: Manual systemd Service (Advanced)

This is the most reliable method for running the bot on boot.

#### Step 1: Customize the Service File

The repository includes a systemd service file. You may need to customize it:

```bash
# Copy the service file
sudo cp /home/pi/MCWB/weather_bot.service /etc/systemd/system/

# Edit if needed (e.g., if your username is not 'pi' or if using a virtual environment)
sudo nano /etc/systemd/system/weather_bot.service
```

The service file should look like this:
```ini
[Unit]
Description=MCWB - MeshCore Weather Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/MCWB
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --announce
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

> **⚠️ IMPORTANT: Avoid HTML Encoding Issues**
> 
> When copying the service file content above:
> - **DO NOT copy from GitHub's rendered web view** - the browser may corrupt text with HTML entities
> - **Instead:** Use the command above to copy the actual file from your repository: `sudo cp /home/pi/MCWB/weather_bot.service /etc/systemd/system/`
> - **If you must manually type/paste the content**, ensure `[Unit]`, `[Service]`, and `[Install]` appear EXACTLY as shown - no HTML entities like `&gt;`, `&lt;`, or `&amp;`
> - **If you see errors like "Unknown section '&gt;"**, your service file has corrupted HTML entities - see the troubleshooting section below

**If using a virtual environment**, change the `ExecStart` line to use the venv Python:
```ini
ExecStart=/home/pi/MCWB/venv/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --announce
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
● weather_bot.service - MCWB - MeshCore Weather Bot
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

5. **"Unknown section" error with HTML entities (e.g., `Unknown section '&gt;'`):**
   
   This error occurs when the service file contains corrupted HTML entities instead of proper characters.
   
   **Symptoms:**
   ```bash
   systemd[1]: /etc/systemd/system/weather_bot.service:1: Unknown section '&gt;
   ```
   
   **Cause:** Copying the service file content from a web browser (e.g., GitHub's web view) can corrupt the text with HTML entities like `&gt;` (instead of `>`), `&lt;` (instead of `<`), or `&amp;` (instead of `&`).
   
   **Solution:**
   
   **Option 1 - Use the repository file (Recommended):**
   ```bash
   # Remove the corrupted service file
   sudo rm /etc/systemd/system/weather_bot.service
   
   # Copy the correct file from the repository
   cd /home/pi/MCWB
   sudo cp weather_bot.service /etc/systemd/system/
   
   # Reload and restart
   sudo systemctl daemon-reload
   sudo systemctl restart weather_bot
   ```
   
   **Option 2 - Fix manually:**
   ```bash
   # Edit the service file
   sudo nano /etc/systemd/system/weather_bot.service
   
   # Fix any HTML entities:
   # - Change &gt; to >
   # - Change &lt; to <
   # - Change &amp; to &
   # - Ensure [Unit], [Service], and [Install] sections are correct
   
   # Reload and restart
   sudo systemctl daemon-reload
   sudo systemctl restart weather_bot
   ```
   
   **Prevention:** Always copy the service file directly from the repository using `sudo cp weather_bot.service /etc/systemd/system/` rather than copying text from web browsers.

### Bot Running But Not Responding

**Check the bot can see messages:**
```bash
# View live logs
sudo journalctl -u weather_bot -f

# Send a test message and watch for it in the logs
```

**Most common cause: Radio not subscribed to channels**
- The companion radio must be subscribed to channels BEFORE starting the bot
- Use the MeshCore app to verify channel subscriptions
- Add missing channels in the MeshCore app, then restart the bot:
  ```bash
  sudo systemctl restart weather_bot
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

### Running with Announcements (Enabled by Default)

**Note:** As of the latest version, periodic weather announcements every 3 hours are **enabled by default** when using the installer scripts.

If you installed manually and want to enable announcements:

```bash
# Edit the service file
sudo nano /etc/systemd/system/weather_bot.service

# Change ExecStart line to include --announce:
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --announce

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
```

To **disable** announcements if you don't want them:

```bash
# Edit the service file
sudo nano /etc/systemd/system/weather_bot.service

# Remove --announce from the ExecStart line:
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200

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

⚠️ **CRITICAL: Always allow SSH BEFORE enabling the firewall or you will be locked out!**

```bash
sudo apt-get install ufw

# IMPORTANT: Allow SSH FIRST, before enabling firewall
sudo ufw allow 22/tcp
sudo ufw allow ssh

# Now it's safe to enable the firewall
sudo ufw enable
```

**If you get locked out:** See [SSH_TROUBLESHOOTING.md](SSH_TROUBLESHOOTING.md) for recovery instructions.

**Incorrect Order (will lock you out):**
```bash
# ❌ DON'T DO THIS:
sudo ufw enable          # Enables firewall first - locks you out!
sudo ufw allow 22/tcp    # Too late, you're already locked out
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
- [ ] **MeshCore radio channels configured (CRITICAL: do this BEFORE connecting to Pi)**
- [ ] **Verified radio is subscribed to desired channels using MeshCore app**
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
