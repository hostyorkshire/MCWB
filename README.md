# MCWB - MeshCore Weather Bot

Lightweight Python3 weather bot for MeshCore mesh networks.

> **⚠️ SECURITY NOTE:** All examples in this repository use placeholder values for security:
> - Domain: `weather.example.com` (replace with your actual domain)
> - IP Address: `192.168.1.100` (replace with your local IP)
> - GitHub User: `yourusername` (replace with your GitHub username)
> - Email: `your.email@example.com` (replace with your email)
> 
> **Never commit real credentials, API keys, or production URLs to public repositories!**

## 🚨 Having Issues?

- **🆘 EMERGENCY: Cannot SSH OR Cannot See Dashboard?** → See [ACCESS_EMERGENCY.md](ACCESS_EMERGENCY.md) - ONE command fixes both!
- **📡 WiFi Not Working / Cannot Resolve Host?** → Run `./check_wifi.sh` - Diagnose and fix WiFi connectivity issues
- **Cannot SSH into Pi AND/OR Dashboard not working?** → Run `./fix_access_issues.sh` - Master fix script for both issues
- **Dashboard URL not working?** → See [QUICK_FIX_GUIDE.md](QUICK_FIX_GUIDE.md) - Fast solutions for connectivity issues
- **Bot not announcing on boot?** → See [QUICK_FIX_GUIDE.md](QUICK_FIX_GUIDE.md) - Fix announcement problems in 2 steps

## 📖 Quick Links

- **🆘 [ACCESS EMERGENCY](ACCESS_EMERGENCY.md)** - Can't SSH or see dashboard? ONE command fixes both!
- **⚡ [QUICK FIX GUIDE](QUICK_FIX_GUIDE.md)** - Fast solutions for common issues
- **❓ [FAQ](FAQ.md)** - Common questions & quick answers (including boot setup scripts!)
- **🚀 [Quick Start](QUICKSTART_SIMPLE.md)** - Get started in minutes
- **📟 [DollaTek Board Setup](DOLLATEK_SETUP.md)** - DollaTek ESP32 SX1276 Wireless Bridge configuration
- **🍓 [Raspberry Pi Setup](RASPBERRY_PI_SETUP.md)** - Auto-start on boot guide
- **🌐 [Web Dashboard](WEB_DASHBOARD.md)** - Monitor your bot with a web interface
- **🐛 [Troubleshooting](TROUBLESHOOTING.md)** - Problem-solving guide
- **🔧 [SSH Troubleshooting](SSH_TROUBLESHOOTING.md)** - Can't SSH? Start here! (ping works but SSH doesn't)

## 🎯 IMPORTANT: Bot Works on ANY Channel You Create!

**The bot is NOT limited to any specific channel.** It works on:
- ✅ **ANY channel name** you create in your MeshCore app
- ✅ **#weather**, **#wxtest**, **#forecast**, **#sensors** - whatever you want!
- ✅ **ALL your channels simultaneously** by default
- ✅ **Zero configuration needed** - just run it!

**Note:** Examples in this documentation use channel names like `#weather` and `#wxtest`, but these are **ONLY EXAMPLES**. You should use whatever channel names make sense for YOUR mesh network!

**✨ Zero Configuration Required** - The bot automatically works on any channel without needing to configure channel IDs!

**🍓 Raspberry Pi Zero 2 Ready** - See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for headless auto-start on boot setup!

**🌙 NEW: Dark-Themed Web Dashboard** - Monitor your bot in real-time with a beautiful dark-themed web interface! See [WEB_DASHBOARD.md](WEB_DASHBOARD.md) for details or [CONNECTION_GUIDE.md](CONNECTION_GUIDE.md) for quick troubleshooting.

**🌐 NEW: Cloudflare Tunnel Integration** - Connect your static website to your local bot without port forwarding! Perfect for cPanel-hosted sites. See [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md) and [CPANEL_DEPLOYMENT_GUIDE.md](CPANEL_DEPLOYMENT_GUIDE.md) for setup instructions.

**📚 Documentation Website** - Complete wiki-style documentation website available at https://weather.example.com/

## Overview

MCWB listens for weather queries and responds using the free [Open-Meteo](https://open-meteo.com/) API (no API key needed).

**Simple Setup:**
1. Connect your MeshCore companion radio via USB
2. Run `python3 weather_bot.py`
3. Done! The bot works on ANY channel where users send weather commands

**✨ UK Location Bias** - The bot defaults to UK locations for ambiguous city names:
- `wx Halifax` → Halifax, United Kingdom (not Canada)
- `wx York` → York, United Kingdom (not USA)
- Users can still specify other countries: `wx Halifax CA` or `wx York USA`

**✨ Country Specification** - Users can specify country in their commands:
- `wx York UK` → York, United Kingdom
- `wx York USA` → York, USA
- No more confusion with ambiguous city names!

**✨ UK Postcode Support** - Get weather by entering a UK postcode:
- `wx S1 2HH` → Sheffield city centre
- `weather S71` → Barnsley area
- `wx SW1A 1AA` → London (Buckingham Palace area)
- Works with both full and partial postcodes!

## Usage

**Send weather commands on ANY channel you've created!** Examples:

In your `#weather` channel:
```
WX London
```

In your `#forecast` channel:
```
wx York
```

In your `#wxtest` channel:
```
weather Manchester
```

In YOUR custom channel (whatever name you chose):
```
wx [your location]
```

### Using UK Postcodes

You can now get weather by entering a UK postcode instead of a city name:

```
wx S1 2HH        # Full postcode - Sheffield city centre
weather S71      # Partial postcode (outward code) - Barnsley area
wx SW1A 1AA      # London (Buckingham Palace area)
WX M1 1AE        # Manchester city centre
```

**Supported postcode formats:**
- **Full postcodes**: `S1 2HH`, `SW1A 1AA`, `M1 1AE` (with or without space)
- **Partial postcodes** (outward code): `S71`, `S1`, `SW1A`, `LS1`

The bot automatically detects UK postcodes and uses the free [Postcodes.io](https://postcodes.io) API to geocode them.

### Specifying Country in Your Query

**Default Behavior:** The bot defaults to UK locations for UK users. When you type `wx Halifax` or `wx York`, you'll get the UK location automatically.

When you want a location in a different country, specify the country directly in your command:

```
wx Halifax        # Halifax, United Kingdom (default)
wx Halifax CA     # Halifax, Canada (explicit)
wx York           # York, United Kingdom (default)
wx York USA       # York, Pennsylvania USA (explicit)
wx Paris FR       # Paris, France
wx Berlin DE      # Berlin, Germany
```

**Supported country codes:**
- `UK`, `GB`, or `United Kingdom` → United Kingdom (default)
- `USA`, `US`, or `United States` → United States
- Any ISO-3166-1 alpha-2 country code (2 letters): `FR`, `DE`, `CA`, `JP`, `AU`, etc.

**For non-UK deployments:** You can change the default country by running the bot with `--country <code>`:
```bash
python3 weather_bot.py --country US  # For US deployments
python3 weather_bot.py --country FR  # For French deployments
```

The bot replies on the same channel with current conditions:

```
London, GB
⛅ Partly cloudy
Temp: 14.2°C (feels 12.8°C)
Humid: 72%
Wind: 18 km/h at 230°
```

### 🌤️ Weather Outlook Feature

After sending the current weather, the bot **automatically sends** a concise 3-day forecast:

```
London, GB 3-day:
02-25: Cloudy 8-15°C
02-26: Rain 9-16°C
02-27: Overcast 7-14°C
https://weather.example.com
```

The outlook includes the country code (e.g., "London, GB" or "York, US") to avoid confusion when cities have the same name in different countries.

See [docs/WEATHER_OUTLOOK_FEATURE.md](docs/WEATHER_OUTLOOK_FEATURE.md) for complete documentation.

## LoRa Radio Hardware

MCWB connects to a **MeshCore companion radio** over USB serial.
The companion radio is a LoRa-based device (e.g. a T-Beam, LILYGO LoRa32, DollaTek ESP32 SX1276, Heltec WiFi LoRa 32, or
similar ESP32/LoRa board) running the
[MeshCore firmware](https://github.com/ripplebiz/MeshCore).

**📟 Using a DollaTek ESP32 SX1276 Wireless Bridge?** See the [DollaTek Setup Guide](DOLLATEK_SETUP.md) for board-specific configuration instructions, including LED indicator setup.

```
Raspberry Pi / PC
  │
  │  USB serial (default 115200 baud)
  │
  ▼
MeshCore companion radio  ←→  LoRa RF  ←→  Other MeshCore nodes
```

The bot speaks the MeshCore companion radio binary protocol directly over the
USB serial port (no extra libraries beyond `pyserial`).  It handles:

| Frame | Direction | Description |
|-------|-----------|-------------|
| `CMD_APP_START` (0x01) | → radio | Initialise session on connect |
| `CMD_GET_DEVICE_TIME` (0x05) | ← radio | Radio requests time; bot responds immediately |
| `CMD_SYNC_NEXT_MSG` (0x0A) | → radio | Drain queued messages |
| `CMD_SEND_CHAN_MSG` (0x03) | → radio | Send a weather reply on a channel |
| `RESP_CHANNEL_MSG` (0x08/0x11) | ← radio | Incoming channel message |
| `PUSH_CHAN_MSG` (0x88) | ← radio | Inline push of a channel message |
| `PUSH_MSG_WAITING` (0x83) | ← radio | New message queued; bot fetches it |

### Connecting the radio

1. Flash your ESP32/LoRa board with [MeshCore firmware](https://github.com/ripplebiz/MeshCore).
2. **IMPORTANT: Configure channels on your radio BEFORE starting the bot**
   - Open the MeshCore app on your phone
   - Join/subscribe to the channels you want the bot to monitor (e.g., `#weather`, `#wxtest`)
   - The bot cannot add channels for you - this must be done through the MeshCore app
   - Without this step, the bot won't receive messages from those channels
3. Connect it to your Pi (or PC) via USB.
4. The device typically appears as `/dev/ttyUSB0` or `/dev/ttyACM0` on Linux.
5. Start the bot – it auto-detects the port:

```bash
python3 weather_bot.py
```

## Web Dashboard

MCWB includes a beautiful dark-themed web interface for monitoring your bot in real-time!

**🔒 NEW: HTTPS Support** - Run your dashboard with HTTPS for secure connections from HTTPS sites! See [HTTPS_SETUP.md](HTTPS_SETUP.md) for setup instructions.

### 🚀 Quick Start (Recommended for Raspberry Pi)

**The easiest way to set up the dashboard:**

```bash
cd ~/MCWB
./install_dashboard_service.sh
```

This script will:
- ✅ Automatically configure everything for your system
- ✅ Create a virtual environment and install dependencies
- ✅ Configure the service to use the venv (no manual activation needed)
- ✅ Configure firewall if needed
- ✅ Start the dashboard and show you the connection URL
- ✅ Enable auto-start on reboot

The installer will display your connection URL, like: `http://192.168.1.100:5000`

**⭐ HIGHLY RECOMMENDED: Reserve a Static IP in Your Router**

After installation, reserve a static IP for your Raspberry Pi in your router's DHCP settings. This ensures your dashboard URL never changes, making it perfect for bookmarking and website integration. See [CONNECTION_GUIDE.md](CONNECTION_GUIDE.md#step-15-reserve-a-static-ip-highly-recommended) for detailed instructions.

**✨ Important:** Once installed as a service, the dashboard starts automatically on every reboot. You **don't need to activate the virtual environment manually** - the service handles this automatically using the venv's Python interpreter.

**For HTTPS:** After installation, see [HTTPS_SETUP.md](HTTPS_SETUP.md) to enable SSL.

### Manual Start (For Testing Only)

**Note:** Only use this for testing. For production use, install as a service (above) which handles everything automatically.

```bash
# Create and activate virtual environment if not already done
python3 -m venv venv
source venv/bin/activate

# Install Flask (already in requirements.txt)
pip install -r requirements.txt

# Start the dashboard (HTTP)
python3 web_dashboard.py

# OR start with HTTPS (recommended for HTTPS access)
python3 web_dashboard.py --ssl
```

**For HTTPS setup:** See [HTTPS_SETUP.md](HTTPS_SETUP.md) for generating SSL certificates.

The dashboard will display the connection URL when it starts.

**Can't connect?** 
- **Quick fix (if it worked before):** Run `./fix_dashboard.sh` to quickly restore functionality
- **Full diagnostics:** Run `./diagnose_dashboard.sh` to identify and fix issues
- **Manual troubleshooting:** See [DASHBOARD_CONNECTIVITY_TROUBLESHOOTING.md](DASHBOARD_CONNECTIVITY_TROUBLESHOOTING.md)

![Dark Theme Dashboard](https://github.com/user-attachments/assets/514e2c7d-0c52-4708-b0fc-ab571c9069f6)

### Features

- 🌙 **Dark Theme** - Beautiful gradient background easy on the eyes
- 📊 **Real-time Status** - Monitor bot and log file status
- 📝 **Log Viewer** - View bot logs with color-coded entries (errors in red, warnings in yellow)
- 🔄 **Auto-refresh** - Updates every 10 seconds automatically
- 📱 **Responsive** - Works on desktop, tablet, and mobile

For detailed documentation, see [WEB_DASHBOARD.md](WEB_DASHBOARD.md).


Or specify the port explicitly:

```bash
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200
```

## Requirements

- Python 3.7+
- `requests` and `pyserial` (see `requirements.txt`)
- MeshCore companion radio connected via USB

## Installation

```bash
git clone https://github.com/hostyorkshire/MCWB.git
cd MCWB

# Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** On newer systems (Debian 12+, Ubuntu 23.04+), direct `pip install` may fail with "externally-managed-environment" error due to PEP 668. Using a virtual environment is the recommended solution.

### 🎛️ Unified Service Manager (Raspberry Pi)

**NEW: One menu for all services!** Manage weather bot and web dashboard from a single interactive menu:

```bash
./setup_mcwb.sh
```

This unified menu lets you:
- ✅ Install weather bot and/or dashboard services
- ✅ Check service status
- ✅ Start/stop/restart services
- ✅ View logs
- ✅ Configure firewall
- ✅ Uninstall services

**Perfect for Raspberry Pi users** - No need to remember multiple scripts! See [SETUP_MENU_GUIDE.md](SETUP_MENU_GUIDE.md) for details.

> **Note:** Individual installation scripts (`install_service.sh`, `install_dashboard_service.sh`) still work if you prefer to use them directly.

## Running the bot

```bash
# Auto-detect USB port (recommended) - works on any channel automatically
python3 weather_bot.py

# Specify port and baud rate
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200

# Enable debug output (shows all protocol frames)
python3 weather_bot.py -d

# Enable periodic announcements every 6 hours
python3 weather_bot.py --announce


# Quick weather lookup (no radio hardware needed)
python3 weather_bot.py --location Leeds
```

### Advanced: Channel-Specific Configuration

**Most users don't need this!** The bot automatically adapts to work on any channel.

Only use these options if you need to restrict the bot to a specific channel:

```bash
# OPTIONAL: Restrict bot to only respond on channel index 1
python3 weather_bot.py --channel-idx 1

# OPTIONAL: Configure announcements to be sent on channel index 2
# (Bot will still respond to messages from ANY channel)
python3 weather_bot.py --weather-channel-idx 2 --announce
```

### Command line options

```
  -p PORT, --port PORT    Serial port (e.g. /dev/ttyUSB0). Auto-detects if omitted.
  -b BAUD, --baud BAUD    Baud rate (default: 115200)
  -d, --debug             Enable debug output
  -a, --announce          Send periodic announcements every 6 hours
  -r, --reboot-notify     Send notification on reboot/restart (useful for detecting power loss or crashes)
  -c CHANNEL_IDX, --channel-idx CHANNEL_IDX
                          Only respond to messages from this channel index (e.g., 1 for #weather)
  -w WEATHER_CHANNEL_IDX, --weather-channel-idx WEATHER_CHANNEL_IDX
                          Specify which channel index to use for announcements. Bot will still
                          respond to messages from ANY channel unless --channel-idx is also specified.
  --country COUNTRY       Default country code for geocoding (default: GB for UK).
                          Filters location searches to prefer cities in this country.
                          Useful for non-UK deployments (e.g., --country US, --country FR).
  -l LOCATION, --location LOCATION
                          Look up weather and exit (no radio needed)
```

## Periodic Announcements

The bot can send periodic announcements to let users know it's online and how to use it.

### How Announcements Work

When you enable announcements with the `--announce` flag:

- The bot **ALWAYS announces on every startup/reboot** to let users know it's operational
- After startup, the bot announces every **6 hours** during normal operation
- Announcement timestamps are persisted to disk (`logs/.last_announce`) for tracking periodic announcements only
- **No code prevents re-announcing** - the bot will announce on every boot, regardless of how recently it last announced

### ✨ NEW: Automatic Weather Channel Detection

**The bot now automatically detects your #weather channel!** No manual configuration needed in most cases.

When announcements are enabled, the bot will:
- 🔍 **Auto-detect** the #weather channel by monitoring incoming messages
- 📡 Detect channels containing `#weather`, `#wx`, or "weather channel" in messages
- 🎯 Automatically use the channel that receives weather commands (WX/weather)
- 📢 Send all announcements to the detected weather channel

**This works automatically - just run:**
```bash
python3 weather_bot.py --announce
```

The bot will detect your #weather channel from the first message it receives!

### Manual Channel Configuration (Optional)

If you need explicit control over the announcement channel, you can still manually specify it:

```bash
# Announcements go to channel_idx 1 (typically #weather)
python3 weather_bot.py --announce --weather-channel-idx 1

# Announcements go to channel_idx 2
python3 weather_bot.py --announce --weather-channel-idx 2
```

**Note:** Manual configuration overrides auto-detection and is useful for:
- Pre-configuring the announcement channel before any messages arrive
- Ensuring announcements go to a specific channel from bot startup
- Advanced multi-bot deployments

### Announcement Message

The announcement message is:
```
Hello this is the WX Bot. To get a weather update simply type WX and your location.

Need help? See commands & more https://tinyurl.com/wxbot
```

### Example: Raspberry Pi Service Setup

The included `weather_bot.service` file is pre-configured with announcements enabled:

```ini
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --announce --weather-channel-idx 1
```

**NEW:** You can now simplify this to use auto-detection:
```ini
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --announce
```

The bot will automatically detect and use your #weather channel!

## How It Works

### Automatic Channel Adaptation

**No configuration needed!** The bot automatically:
- ✅ Listens on **ALL channels** for weather commands
- ✅ Responds on the **SAME channel** where each request came from  
- ✅ Adapts announcements to use the **channel that users are active on**

Users on different MeshCore devices can have #weather mapped to different channel indices, and the bot handles this automatically.

### Example Scenario

```
User A's device: #weather → channel_idx 1
User B's device: #weather → channel_idx 2  
User C's device: #weather → channel_idx 3

Bot behavior:
- User A sends "wx London" on channel_idx 1 → Bot replies on channel_idx 1
- User B sends "wx Paris" on channel_idx 2 → Bot replies on channel_idx 2
- User C sends "wx Berlin" on channel_idx 3 → Bot replies on channel_idx 3
- All users get responses on their respective channels automatically!
```

## Channel Filtering (Advanced)

By default, the bot responds to weather queries from **any channel**. 

**When to use channel filtering:**
- You want to isolate the bot to a dedicated weather channel only
- You have multiple bots running and need to prevent conflicts
- You want explicit control over which channel the bot uses

**When NOT to use channel filtering:**
- For most typical deployments (just run `python3 weather_bot.py`)
- When users might have #weather on different channel indices
- When you want maximum flexibility

### Option 1: Basic Channel Filtering

```bash
# Only respond to messages on channel index 1
python3 weather_bot.py --channel-idx 1
```

### Option 2: Weather-Specific Channel Configuration

```bash
# Configure announcements to be sent on channel index 2
# Bot will still respond to messages from ALL channels
python3 weather_bot.py --weather-channel-idx 2 --announce

# To ALSO restrict responses to only channel 2, combine both flags:
python3 weather_bot.py --weather-channel-idx 2 --channel-idx 2 --announce
```

This is useful when:
- You want explicit control over where announcement messages are sent
- You need to ensure announcements start on a specific channel from bot startup
- You want announcements on one channel but responses on all channels

**Note:** Channel indices are numeric (0, 1, 2, etc.) and correspond to the physical channel
slots on your MeshCore device. Slot 0 is the default channel (typically using a well-known PSK for broad accessibility). Slots 1–7 are hashtag/named channels configured in the MeshCore app with unique encryption keys (PSKs).

### Finding Your Weather Channel Index (Optional)

**✨ NEW: Auto-detection makes this unnecessary in most cases!**

The bot now automatically detects your #weather channel from incoming messages. You rarely need to manually configure the channel index anymore.

If you still need to find the channel index for advanced scenarios:

1. **Check your MeshCore app** - Look at Channel Settings to see which slot #weather is assigned to
2. **Use debug mode** - Run `python3 weather_bot.py --debug`, send a test message on #weather, 
   and observe the `channel_idx` in the output:
   ```
   [17:45:32] channel_idx=2 SomeUser: wx test
   ```

Once you know the index, you can manually configure it with `--weather-channel-idx` if desired.

**How Auto-Detection Works:**
- The bot monitors incoming messages for #weather channel indicators
- It detects messages containing `#weather`, `#wx`, or "weather channel"
- It also learns from weather commands (WX/weather) to identify the active weather channel
- Once detected, all announcements use the detected channel automatically 
the bot automatically replies on whatever channel receives requests, manual configuration is 
usually not necessary.

You can also send a message directly on a specific channel slot using `meshcore_send.py`:

```bash
# Send on channel slot 1 by index (MESHCORE_CHANNEL_IDX)
python3 meshcore_send.py "wx Leeds" --channel-idx 1

# Send by name (mapped to a slot automatically)
python3 meshcore_send.py "wx Leeds" --channel weather
```

See `CHANNEL_GUIDE.md` for a full explanation of the channel name / channel index relationship.

## Reboot Notifications

The bot can automatically notify users when it restarts after a power loss or crash. This is useful for monitoring the bot's availability on remote or unmanned installations.

### Enabling Reboot Notifications

Add the `--reboot-notify` (or `-r`) flag when starting the bot:

```bash
python3 weather_bot.py --reboot-notify
```

### How It Works

1. **First Run:** The bot creates a state file (`/var/tmp/mcwb_state.txt`) but does NOT send a notification
2. **Subsequent Restarts:** If the state file exists when the bot starts, it detects this as a restart and sends a notification message
3. **Notification Message:** "MCWBv2 weather bot has restarted and is now online."
4. **Channel Selection:** The notification is sent on the same channel used for announcements (see `--weather-channel-idx`)

The state file is stored in `/var/tmp/` which persists across system reboots, allowing the bot to detect and notify about both:
- **Power loss/system reboots:** After the system restarts, the state file still exists
- **Bot crashes:** When systemd restarts the service, the state file indicates the previous run

- **Remote Monitoring:** Get alerted when your Raspberry Pi weather bot reboots after power loss
- **Reliability Tracking:** Know when the bot crashes and automatically recovers
- **Maintenance Awareness:** See when systemd restarts the service after failures

### Example Configurations

```bash
# Reboot notifications only
python3 weather_bot.py --reboot-notify

# Reboot notifications with announcements
python3 weather_bot.py --reboot-notify --announce

# Reboot notifications on specific channel
python3 weather_bot.py --reboot-notify --weather-channel-idx 1

# Full production setup with all monitoring features
python3 weather_bot.py --reboot-notify --announce --weather-channel-idx 1
```

**Note:** The reboot notification feature uses a state file stored in `/var/tmp/` which persists across system reboots. This allows detection of both power loss scenarios (full system reboot) and bot-only crashes (systemd service restart).

### Use Cases

For production deployments, especially on Raspberry Pi, you can run the bot as a systemd service that starts automatically on boot:

```bash
sudo cp weather_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable weather_bot
sudo systemctl start weather_bot
```

**📖 Raspberry Pi Zero 2 Headless Setup:** See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for complete instructions on setting up the bot to run automatically on boot in headless mode (no display required).

**📡 Remote SSH Access:** See [SSH_REMOTE_ACCESS.md](SSH_REMOTE_ACCESS.md) for comprehensive instructions on accessing your Raspberry Pi remotely when deployed in remote locations, including VPN setup, port forwarding, and security best practices.

## LED Activity Indicators

The bot supports LED indicators for visual feedback on compatible ESP32 LoRa boards.

### Quick Start

**For DollaTek ESP32 SX1276 Wireless Bridge:**
```bash
python3 weather_bot.py --enable-leds --led-board-variant dollatek
```

**For Heltec WiFi LoRa 32 V2:**
```bash
python3 weather_bot.py --enable-leds --led-board-variant heltec-v2
```

**For custom GPIO pins:**
```bash
python3 weather_bot.py --enable-leds --led-blue-pin 25 --led-green-pin 4 --led-red-pin 5
```

### Supported Board Variants

#### DollaTek ESP32 SX1276 Wireless Bridge
The DollaTek board has a single onboard LED:

| Colour | GPIO  | Behaviour |
|--------|-------|-----------|
| Blue   | GPIO25 | Heartbeat – blinks every 2 s while the bot is running |

Use with: `--enable-leds --led-board-variant dollatek`

**Note**: This board only has one LED available. Green and Red indicators are not available because:
- GPIO26 is used for LoRa DIO0 (interrupt pin)
- GPIO27 is not connected to an LED on this board

#### Heltec WiFi LoRa 32 V2
The Heltec V2 board has one onboard LED:

| Colour | GPIO  | Behaviour |
|--------|-------|-----------|
| Blue   | GPIO25 | Heartbeat – blinks every 2 s while the bot is running |

Use with: `--enable-leds --led-board-variant heltec-v2`

**Note**: Earlier documentation incorrectly suggested GPIO26/27 for additional LEDs. These pins conflict with LoRa operation:
- GPIO26 is used for LoRa DIO0 (interrupt pin) and cannot be used for LEDs
- GPIO27 may be used for LoRa MOSI or other functions depending on board revision

### Custom GPIO Configuration

If your board has LEDs on different GPIO pins, you can specify them manually:

```bash
python3 weather_bot.py --enable-leds \
  --led-blue-pin 25 \
  --led-green-pin 4 \
  --led-red-pin 5
```

Available LEDs:
- **Blue LED**: Heartbeat indicator (blinks every 2 seconds while running)
- **Green LED**: RX indicator (flashes when a weather request is received)
- **Red LED**: TX indicator (flashes when a response is sent)

To disable a specific LED, simply omit the corresponding `--led-*-pin` argument. The bot will automatically handle disabled LEDs gracefully.

### Technical Notes

**GPIO Compatibility:**
- This feature requires GPIO command support in your MeshCore firmware version
- If GPIO commands are not supported, LED events are logged in debug mode (`--debug`)
- The bot continues to operate normally regardless of GPIO support
- Avoid using GPIO pins that conflict with your board's LoRa, SPI, or I2C functions

**Common GPIO Pin Conflicts:**
- **GPIO26**: Often used for LoRa DIO0 (do not use for LEDs)
- **GPIO6-11**: Reserved for SPI flash (do not use)
- **GPIO34-39**: Input-only pins (cannot drive LEDs)

Always verify your board's pinout before configuring custom GPIO pins.

## Troubleshooting

### No serial port found
- Check the USB cable and that the companion radio is powered.
- Run `ls /dev/ttyUSB* /dev/ttyACM*` to see available ports.
- Try `--port /dev/ttyUSB0` (or whichever port appears).

### Bot connects but receives no messages
- **Most common cause:** The companion radio is NOT subscribed to the channels where users are sending messages
- **Solution:** Use the MeshCore app to join/subscribe to channels (e.g., `#weather`, `#wxtest`) BEFORE starting the bot
- The bot cannot configure channels automatically - you must add them through the MeshCore app first
- Verify your channel subscriptions in the MeshCore app's Channel Settings
- Use `--debug` (`-d`) to see raw protocol frames and verify if messages are being received

### Location not found
- Use the full city name, or add country/region: `wx York, UK`.
- **For UK locations**: Try using a postcode instead: `wx S1 2HH` or `wx S71`

### Wrong city returned (city in another country)
Some city names exist in multiple countries (e.g., "Halifax" in UK, Canada; "York" in UK, USA; "Paris" in France, USA).

**Default behavior:** The bot defaults to UK locations. If you type `wx Halifax`, you'll get Halifax, UK automatically.

**Solutions:**

1. **For UK locations (default):** Just use the city name:
   - `wx Halifax` → Returns Halifax, United Kingdom (automatic)
   - `wx York` → Returns York, United Kingdom (automatic)
   - No need to specify UK!

2. **For non-UK locations:** Specify the country in your command:
   - `wx Halifax CA` → Returns Halifax, Canada
   - `wx York USA` → Returns York, Pennsylvania USA  
   - `wx Paris FR` → Returns Paris, France
   - Supports: `UK`, `USA`, `US`, `GB`, `CA`, or any ISO-3166-1 alpha-2 country code (2 letters)

3. **Use comma-separated format:** Traditional explicit format:
   - `wx York, UK` instead of just `wx York`
   - `wx Paris, France` instead of just `wx Paris`

4. **Configure a different default country:** For non-UK deployments, run the bot with the `--country` flag:
   ```bash
   python3 weather_bot.py --country US  # Defaults to US cities
   python3 weather_bot.py --country FR  # Defaults to French cities
   python3 weather_bot.py --country GB  # UK (default behavior)
   ```
   
   This filters location searches to prefer cities in the specified country while still
   allowing users to override by specifying a different country in their query (e.g., `wx York USA`).

**For UK users:** You can now use postcodes directly! See the [Using UK Postcodes](#using-uk-postcodes) section above.

## API

Weather data is from the free [Open-Meteo API](https://open-meteo.com/) –
no account or API key required.

UK postcode geocoding is provided by the free [Postcodes.io API](https://postcodes.io) –
no account or API key required.

## License

MIT License – see LICENSE file for details.

