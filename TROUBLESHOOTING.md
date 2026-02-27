# MCWB Weather Bot Troubleshooting Guide

This guide helps you troubleshoot common issues with the MeshCore Weather Bot.

## 🚨 Critical Issue: Can't SSH into Raspberry Pi (But Ping Works)

### Symptoms

- ✅ Ping works: `ping 192.168.1.109` succeeds
- ❌ SSH fails: `ssh user@192.168.1.109` connection refused or times out

### Cause

**Firewall is blocking SSH port 22.** This is the #1 most common issue when you can ping but can't SSH.

### Quick Fix

**If you have physical access (keyboard/monitor):**

```bash
# Option 1: Run the fix script
cd ~/MCWB
./fix_ssh_access.sh

# Option 2: Manual fix
sudo ufw allow 22/tcp
sudo ufw reload
```

**Complete guide:** See **[SSH_TROUBLESHOOTING.md](SSH_TROUBLESHOOTING.md)** for detailed recovery instructions.

---

## 🚨 Critical Issue: WiFi Not Working / Cannot Resolve Host

### Symptoms

- ❌ `git pull` fails with "could not resolve host"
- ❌ Cannot access the internet from your Raspberry Pi
- ❌ Network commands time out or fail
- ❌ Bot cannot reach weather API

### Cause

**WiFi connection lost or DNS not working.** Common causes include:
- WiFi interface is down
- Not connected to any WiFi network
- No IP address assigned
- DNS servers not configured
- Router/gateway unreachable

### Quick Diagnostic

**If you have physical access (keyboard/monitor):**

```bash
# Run the WiFi diagnostic script
cd ~/MCWB
./check_wifi.sh
```

This script will check:
1. WiFi adapter status
2. Connection status and signal strength
3. IP address assignment
4. Gateway (router) connectivity
5. Internet connectivity
6. DNS resolution
7. Network configuration

### Quick Fix

**Most common fixes:**

```bash
# Restart WiFi interface
sudo ip link set wlan0 down
sudo ip link set wlan0 up

# Restart networking service
sudo systemctl restart networking

# Reconfigure WiFi
sudo raspi-config
# Select 'System Options' → 'Wireless LAN'
# Enter your WiFi SSID and password

# If DNS is the issue (most common for "could not resolve host")
# For systems using systemd-resolved (most modern systems):
sudo nano /etc/systemd/resolved.conf
# Uncomment and set: DNS=8.8.8.8 1.1.1.1
sudo systemctl restart systemd-resolved

# For systems using NetworkManager:
sudo nmcli connection modify "Your-WiFi-Name" ipv4.dns "8.8.8.8 1.1.1.1"
sudo nmcli connection up "Your-WiFi-Name"

# For legacy systems or quick temporary fix:
sudo bash -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'
sudo bash -c 'echo "nameserver 1.1.1.1" >> /etc/resolv.conf'

# Reboot as last resort
sudo reboot
```

### Testing After Fix

```bash
# Test basic connectivity
ping -c 3 8.8.8.8

# Test DNS resolution
ping -c 3 github.com

# Test GitHub specifically
curl -I https://github.com

# Run full diagnostic again
./check_wifi.sh
```

**See also:** [API_CONNECTIVITY_TROUBLESHOOTING.md](API_CONNECTIVITY_TROUBLESHOOTING.md) for detailed network troubleshooting.

---

## Issue: "externally-managed-environment" Error During Installation

### Symptoms

When running `pip install -r requirements.txt`, you get:
```
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.
```

### Diagnosis

This error occurs on newer Linux distributions (Debian 12+, Ubuntu 23.04+) due to PEP 668. These systems prevent direct pip installation to protect the system Python environment.

### Solution

**Use a virtual environment (recommended):**

```bash
cd MCWB

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
python3 weather_bot.py
```

**Important**: If you're setting up a systemd service with a virtual environment, update the service file to use the venv Python:
```ini
ExecStart=/home/pi/MCWB/venv/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200
```

The installation scripts (`install_service.sh`, `install_dashboard_service.sh`) automatically handle virtual environments for you.

## Issue: systemd Service Error - "Unknown section '&gt;'" or HTML Entities

### Symptoms

When checking the weather_bot service status or logs, you see errors like:
```
systemd[1]: /etc/systemd/system/weather_bot.service:1: Unknown section '&gt;
```

Or the service fails to start with configuration errors related to HTML entities (`&gt;`, `&lt;`, `&amp;`).

### Diagnosis

This error occurs when the systemd service file contains **corrupted HTML entities** instead of proper characters. This typically happens when users copy the service file content from a web browser (e.g., GitHub's rendered web view) instead of using the actual file from the repository.

**How it happens:**
- Viewing markdown files on GitHub or other web platforms renders them as HTML
- When you copy text from the browser, HTML entities may be copied instead of actual characters
- `>` becomes `&gt;`, `<` becomes `&lt;`, `&` becomes `&amp;`
- systemd cannot parse these corrupted characters and rejects the service file

### Solution

**Option 1 - Use the repository file (Recommended):**

This is the safest and fastest solution:

```bash
# Remove the corrupted service file
sudo rm /etc/systemd/system/weather_bot.service

# Navigate to your MCWB directory
cd /home/pi/MCWB  # Or wherever you cloned the repository

# Copy the correct file from the repository
sudo cp weather_bot.service /etc/systemd/system/

# If you need to customize it (username, paths, etc.)
sudo nano /etc/systemd/system/weather_bot.service

# Reload systemd and restart the service
sudo systemctl daemon-reload
sudo systemctl restart weather_bot

# Verify it's working
sudo systemctl status weather_bot
```

**Option 2 - Fix manually:**

If you prefer to fix the corrupted file in place:

```bash
# Edit the service file
sudo nano /etc/systemd/system/weather_bot.service

# Look for and fix any HTML entities:
# - Change &gt; to >
# - Change &lt; to <
# - Change &amp; to &
# - Ensure [Unit], [Service], and [Install] section headers are EXACTLY as shown

# The file should start with:
# [Unit]
# Description=MCWB - MeshCore Weather Bot
# ...
# NOT:
# &lt;Unit&gt; or [Unit&gt; or any corrupted variant

# After fixing, reload and restart
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
sudo systemctl status weather_bot
```

**Option 3 - Use the automated installer:**

The automated installation script prevents this issue entirely:

```bash
cd ~/MCWB
./install_service.sh
```

### Prevention

To avoid this issue in the future:

✅ **DO:**
- Use `sudo cp weather_bot.service /etc/systemd/system/` to copy the file directly
- Clone the repository and use the actual files
- Use the automated `install_service.sh` script

❌ **DON'T:**
- Copy service file content from web browsers
- Copy from GitHub's rendered markdown view
- Manually type out the service file (high risk of typos)

### Verification

After applying the fix, verify the service file is correct:

```bash
# Check the first few lines - should show [Unit] with proper brackets
head -5 /etc/systemd/system/weather_bot.service

# Expected output:
# [Unit]
# Description=MCWB - MeshCore Weather Bot
# ...

# Check for any HTML entities (should return nothing)
grep -E '&gt;|&lt;|&amp;' /etc/systemd/system/weather_bot.service

# Check service status
sudo systemctl status weather_bot
```

If you still see HTML entities or the service fails to start, repeat Option 1 above.

## Issue: "No messages are showing and bot is not answering back"

### Understanding the Log Output

When you run the weather bot with the `-d` (debug) flag, you'll see various log messages:

#### Normal Startup Messages
```
[2026-02-21 05:24:49] MeshCore [WX_BOT]: Mapped channel 'weather' to channel_idx 1
[2026-02-21 05:24:49] MeshCore [WX_BOT]: Channel filter set to: 'weather'
[2026-02-21 05:24:49] MeshCore [WX_BOT]: LoRa connected on /dev/ttyUSB1 at 115200 baud
[2026-02-21 05:24:49] MeshCore [WX_BOT]: MeshCore started
```
✅ These are good - they mean the bot started successfully.

#### Protocol Messages
```
[2026-02-21 05:24:49] MeshCore [WX_BOT]: MeshCore: device time requested, responding…
[2026-02-21 05:25:12] MeshCore [WX_BOT]: MeshCore: message acknowledgment received
[2026-02-21 05:25:13] MeshCore [WX_BOT]: MeshCore: message queue empty
```
✅ These are normal - the bot is communicating with the LoRa radio.

#### Data Filtering (Removed - Now Silent)

Previously, the bot would log "Ignoring non-JSON LoRa data" for protocol messages and noise. This was confusing users who thought their commands were being ignored. **This message has been removed** - non-message data is now silently filtered without cluttering the logs.

If you see NO log messages at all after commands are sent, see the troubleshooting steps below.

### What You Should See When a Message Arrives

When someone sends "wx London" to the bot, you should see:

```
[2026-02-21 05:25:30] MeshCore [WX_BOT]: Binary frame: CHANNEL_MSG_V3 on channel_idx 2
[2026-02-21 05:25:30] MeshCore [WX_BOT]: LoRa RX channel msg from USER1 on channel_idx 2: wx London
[2026-02-21 05:25:30] MeshCore [WX_BOT]: Channel filter check: default=False, matching=False, unnamed=True → will_process=True (filter: 'weather')
[2026-02-21 05:25:30] MeshCore [WX_BOT]: Received message from USER1: wx London
[2026-02-21 05:25:30] WeatherBot: Processing message from USER1: wx London
[2026-02-21 05:25:30] WeatherBot: Weather request for location: London
[2026-02-21 05:25:30] WeatherBot: Replying on channel_idx 2: Weather for London, GB...
```

If you don't see these messages, it means:
1. No one has sent a "wx [location]" command yet, OR
2. The messages are not reaching your bot's radio

### Troubleshooting Steps

#### 1. Verify Someone is Actually Sending Commands

**Action**: Use another radio or the MeshCore app to send "wx London" on any channel.

**Expected**: You should see "LoRa RX channel msg" in the logs.

**If you don't see it**: The message is not reaching your radio. Check:
- Is the sending radio within range?
- Is the sending radio powered on and transmitting?
- Are both radios on the same frequency/band?
- Check radio configuration (LoRa settings, encryption, etc.)

#### 2. Check Channel Configuration

The bot with `--channel weather` will accept messages from:
- **Default channel** (channel_idx 0) - Always accepted
- **Any non-default channel** (channel_idx 1-7) - Always accepted when no specific channel name is set
- **Named "weather" channel** - Always accepted

This means the bot should respond to messages on ANY channel! The `--channel` parameter mainly affects WHERE the bot SENDS its responses.

**What this means**: 
- If you send "wx London" on channel_idx 0 (default), the bot will receive and respond
- If you send "wx London" on channel_idx 1, the bot will receive and respond
- If you send "wx London" on channel_idx 2, the bot will receive and respond
- And so on...

The bot replies on the SAME channel_idx it received the message on.

#### 3. Check Message Format

The bot looks for commands matching:
- `wx [location]` (e.g., "wx London", "wx Manchester", "wx New York")
- `weather [location]` (e.g., "weather London")

**Case insensitive**: "WX LONDON" and "wx london" both work.

**Won't match**:
- "weather" (no location specified)
- "wxLondon" (no space)
- "what's the weather" (wrong format)

#### 4. Check Internet Connection

The weather bot needs internet access to query the weather API.

**Test**: Run in test mode:
```bash
python3 weather_bot.py -l London -d
```

If this shows "Error: requests library not found" or connection errors, your network is not working.

#### 5. Enable Full Debug Logging

Run with the `-d` flag to see all internal processing:

```bash
python3 weather_bot.py -n WX_BOT --port /dev/ttyUSB1 --baud 115200 --channel weather -d
```

Look for:
- "Binary frame: CHANNEL_MSG" - means a message arrived
- "LoRa RX channel msg from [sender]" - shows who sent what
- "Channel filter check" - shows if the message passed filtering
- "Processing message from [sender]" - shows the bot is handling it
- "Weather request for location: [location]" - shows the command was recognized

### Common Scenarios

#### Scenario 1: Everything Starts Fine, But No Messages

**Symptoms**:
```
[2026-02-21 05:24:49] MeshCore [WX_BOT]: MeshCore started
Weather Bot started. Send 'wx [location]' to get weather.
Listening for messages...
[2026-02-21 05:25:12] MeshCore [WX_BOT]: MeshCore: message queue empty
[2026-02-21 05:25:13] MeshCore [WX_BOT]: MeshCore: message queue empty
```

**Diagnosis**: The bot is working correctly and waiting for messages. No one has sent a command yet.

**Action**: Send "wx London" from another radio and watch the logs. You should see "Binary frame: CHANNEL_MSG" when a message arrives.

#### Scenario 2: Messages Received But Not Processed

**Symptoms**:
```
[2026-02-21 05:25:30] MeshCore [WX_BOT]: LoRa RX channel msg from USER1: hello world
[2026-02-21 05:25:30] WeatherBot: Processing message from USER1: hello world
[2026-02-21 05:25:30] WeatherBot: Not a weather command: hello world
```

**Diagnosis**: The bot received the message but it doesn't match the "wx [location]" pattern.

**Action**: Send a properly formatted command like "wx London".

## Getting Help

If you're still having issues after following this guide:

1. **Capture a full debug log**: Run with `-d` and save the output
2. **Note what you sent**: Record exactly what command you sent and from which radio
3. **Look for channel message logs**: Search for "Binary frame: CHANNEL_MSG" or "LoRa RX channel msg" to see if messages are arriving
4. **Open an issue**: Include the above information in a GitHub issue

## Advanced Debugging

### Checking Serial Port

Verify your serial port is working:

```bash
ls -l /dev/ttyUSB*
# Should show your device

# Check permissions
sudo chmod 666 /dev/ttyUSB1  # Or add your user to the dialout group
```

### Testing Without Radio

Test the bot logic without hardware:

```bash
python3 weather_bot.py -i -d
```

This starts interactive mode where you can type commands directly.

### Monitoring Serial Data

Use a serial monitor to see raw data:

```bash
# Install screen or minicom
screen /dev/ttyUSB1 115200
# or
minicom -D /dev/ttyUSB1 -b 115200
```

Press Ctrl+A then K to exit screen.

## Understanding Channel Behavior

### Bot Configuration: `--channel weather`

This configuration means:
- **RECEIVING**: Accept messages from ALL channels (default and non-default)
- **REPLYING**: Always reply on the same channel_idx where the message came from
- **BROADCASTING**: Any bot-initiated broadcasts go to the "weather" channel

**Why reply on the incoming channel?**

In the MeshCore app, different users have `#weather` mapped to different channel_idx values:
- User A: `#weather` = channel_idx 1
- User B: `#weather` = channel_idx 2  
- User C: `#weather` = channel_idx 3

This happens because channel_idx depends on join order. The bot cannot know which
channel_idx corresponds to `#weather` for each user. Replying on the incoming
channel ensures the sender always receives the response.

### Example Flow

1. User on channel_idx 0 sends: "wx London"
2. Bot receives on channel_idx 0 (accepted - bot listens to all channels)
3. Bot processes the command
4. Bot replies on channel_idx 0 (same as incoming)
5. User (who sent on channel_idx 0) sees the response

This design ensures senders always receive replies regardless of their channel configuration!
