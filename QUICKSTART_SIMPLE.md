# Quick Start Guide

**❓ Have questions?** Check the [FAQ](FAQ.md) for answers including "where is the boot setup script?"

## 🎛️ NEW: One Menu for Everything!

**Simplest way to set up everything on Raspberry Pi:**

```bash
cd ~/MCWB
./setup_mcwb.sh
```

This interactive menu lets you:
- Install weather bot service
- Install web dashboard service  
- Install BOTH at once (recommended)
- Manage services (start/stop/restart)
- View logs
- Configure firewall
- And more!

**No need to remember multiple scripts** - just run one command!

---

## TL;DR - Manual Setup

**⚠️ FIRST:** Configure channels on your radio using the MeshCore app BEFORE starting the bot!

**Install dependencies (if not already installed):**
```bash
# Create and activate virtual environment (recommended for newer systems)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Run the bot:**
```bash
# Run the weather bot (that's it!)
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d
```

No `--channel` parameter needed. The bot automatically:
- ✅ Accepts weather queries from **all channels**
- ✅ Replies on the **same channel** where each query came from
- ✅ Ensures users receive responses regardless of their channel setup

**Important:** The bot cannot add channels for you. Use the MeshCore app to join/subscribe to channels (e.g., `#weather`, `#wxtest`) before running the bot.

## Web Dashboard Setup (Optional but Recommended)

Want to monitor your bot from any device on your network? Set up the web dashboard:

```bash
cd ~/MCWB
./install_dashboard_service.sh
```

The installer will:
- Configure the dashboard to start automatically on boot
- Configure firewall if needed
- Show you the connection URL (e.g., http://192.168.1.100:5000)

**Can't connect?** See [WEB_DASHBOARD.md](WEB_DASHBOARD.md#troubleshooting-connection-issues) for help.

## Problem Solved

**Before:** Bot with `--channel weather` only accepted messages from the #weather channel, causing confusion.

**Now:** Bot accepts queries from any channel and replies where they came from. Simple and reliable.

## Usage Examples

### Basic Setup
```bash
# Interactive mode (for testing)
python3 weather_bot.py --interactive

# With LoRa hardware (production)
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200

# With debug output
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d
```

### How Users Interact

Users can send weather queries from **any channel**:

```
User1 on default channel:  "wx London"    → Gets reply on default channel
User2 on #weather channel: "wx Brighton"  → Gets reply on #weather
User3 on #alerts channel:  "wx York"      → Gets reply on #alerts
```

### Enable Periodic Announcements

The bot can broadcast a welcome/help message every 6 hours so users know it is active:

```bash
# Run with announcements enabled
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 --announce

# Announcements + debug output
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 --announce -d
```

The announcement message is:
> "Hello this is the WX Bot. To get a weather update simply type WX and your location.
> 
> Need help? See commands & more https://tinyurl.com/wxbot"

It is sent immediately on startup and then repeated every 6 hours on whichever channel users are active on.

#### Announce on a specific channel only

Use `--weather-channel-idx <N>` to pin announcements to one channel index regardless of where users are active.  
Find `<N>` by running with `-d` (debug) and checking the `channel_idx=` value shown when a message arrives on your target channel.

```bash
# Announce only on channel index 2 (e.g. your #weather channel)
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 --announce --weather-channel-idx 2

# To also restrict *responses* to that channel, add --channel-idx too:
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 --announce --weather-channel-idx 2 --channel-idx 2
```

### What About `--channel`?

The `--channel` parameter is **optional** and reserved for future features (like scheduled weather broadcasts). 

**You don't need it for normal operation.**

```bash
# This works (no channel specified)
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d

# This also works but is unnecessary for typical use
python3 weather_bot.py --channel weather --port /dev/ttyUSB0 --baud 115200 -d
```

Both commands do the same thing: accept queries from all channels and reply appropriately.

## Troubleshooting

### "Bot not responding to my queries"

Check:
1. **Most common:** Is your radio subscribed to the channels where users are sending messages? Use the MeshCore app to verify/add channel subscriptions.
2. Bot is running: `python3 weather_bot.py -d`
3. Your radio is connected to the mesh network
4. Query format is correct: `wx [location]` or `weather [location]`

### "I have --channel weather in my systemd service"

You can remove it or leave it - it doesn't matter anymore. The bot behaves the same either way.

```ini
# Before (still works)
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --channel weather --port /dev/ttyUSB0 --baud 115200

# After (simpler, recommended)
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --port /dev/ttyUSB0 --baud 115200
```

## More Information

- See [README.md](README.md) for full documentation
- See [CHANNEL_GUIDE.md](CHANNEL_GUIDE.md) for channel concepts
- Run `python3 weather_bot.py --help` for all options
