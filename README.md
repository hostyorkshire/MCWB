# MCWBv2 - MeshCore Weather Bot

Lightweight Python3 weather bot for MeshCore mesh networks.

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

**📚 Documentation Website** - Complete wiki-style documentation website available at https://mcwb.netlify.app/. See [NETLIFY_DEPLOYMENT.md](NETLIFY_DEPLOYMENT.md) for automatic deployment setup from GitHub.

## Overview

MCWBv2 listens for weather queries and responds using the free [Open-Meteo](https://open-meteo.com/) API (no API key needed).

**Simple Setup:**
1. Connect your MeshCore companion radio via USB
2. Run `python3 weather_bot.py`
3. Done! The bot works on ANY channel where users send weather commands

**✨ NEW: Country Specification** - Users can now specify country in their commands:
- `wx York UK` → York, United Kingdom
- `wx York USA` → York, USA
- No more confusion with ambiguous city names!

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

### Specifying Country in Your Query

When city names are ambiguous (like York, Paris, Birmingham), you can specify the country directly in your command:

```
wx York UK        # York, United Kingdom
wx York USA       # York, Pennsylvania USA
wx Paris FR       # Paris, France
wx Berlin DE      # Berlin, Germany
```

**Supported country codes:**
- `UK`, `GB`, or `United Kingdom` → United Kingdom
- `USA`, `US`, or `United States` → United States
- Any ISO-3166-1 alpha-2 country code (2 letters): `FR`, `DE`, `CA`, `JP`, `AU`, etc.

The bot replies on the same channel with current conditions:

```
London, GB
Partly cloudy
Temp: 14.2°C (feels 12.8°C)
Humid: 72%
Wind: 18 km/h at 230°
Precip: 0.0 mm
```

## LoRa Radio Hardware

MCWBv2 connects to a **MeshCore companion radio** over USB serial.
The companion radio is a LoRa-based device (e.g. a T-Beam, LILYGO LoRa32, or
similar ESP32/LoRa board) running the
[MeshCore firmware](https://github.com/ripplebiz/MeshCore).

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

MCWBv2 includes a beautiful dark-themed web interface for monitoring your bot in real-time!

### 🚀 Quick Start (Recommended for Raspberry Pi)

**The easiest way to set up the dashboard:**

```bash
cd ~/MCWB
./install_dashboard_service.sh
```

This script will:
- ✅ Automatically configure everything for your system
- ✅ Configure firewall if needed
- ✅ Start the dashboard and show you the connection URL
- ✅ Enable auto-start on reboot

The installer will display your connection URL, like: `http://192.168.1.109:5000`

### Manual Start (For Testing)

```bash
# Install Flask (already in requirements.txt)
pip install -r requirements.txt

# Start the dashboard
python3 web_dashboard.py
```

The dashboard will display the connection URL when it starts.

**Can't connect?** See the [Troubleshooting Connection Issues](WEB_DASHBOARD.md#troubleshooting-connection-issues) section in WEB_DASHBOARD.md.

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
pip install -r requirements.txt
```

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

**Perfect for Raspberry Pi users** - No need to remember multiple scripts!

> **Note:** Individual installation scripts (`install_service.sh`, `install_dashboard_service.sh`) still work if you prefer to use them directly.

## Running the bot

```bash
# Auto-detect USB port (recommended) - works on any channel automatically
python3 weather_bot.py

# Specify port and baud rate
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200

# Enable debug output (shows all protocol frames)
python3 weather_bot.py -d

# Enable periodic announcements every 3 hours
python3 weather_bot.py --announce

# Filter location searches to prefer UK cities (useful if most users are in UK)
python3 weather_bot.py --country GB

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
  -a, --announce          Send periodic announcements every 3 hours
  -c CHANNEL_IDX, --channel-idx CHANNEL_IDX
                          Only respond to messages from this channel index (e.g., 1 for #weather)
  -w WEATHER_CHANNEL_IDX, --weather-channel-idx WEATHER_CHANNEL_IDX
                          Specify which channel index to use for announcements. Bot will still
                          respond to messages from ANY channel unless --channel-idx is also specified.
  --country COUNTRY       Default country code for geocoding (e.g., GB, US, FR). Filters location
                          searches to prefer cities in this country. Useful when city names are
                          ambiguous (e.g., York, Paris, etc.).
  -l LOCATION, --location LOCATION
                          Look up weather and exit (no radio needed)
```

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

### Finding Your Weather Channel Index (If Needed)

**Remember:** You usually don't need to find this! The bot works automatically.

If you do need to configure a specific channel index for advanced scenarios:

1. **Check your MeshCore app** - Look at Channel Settings to see which slot #weather is assigned to
2. **Use debug mode** - Run `python3 weather_bot.py --debug`, send a test message on #weather, 
   and observe the `channel_idx` in the output:
   ```
   [17:45:32] channel_idx=2 SomeUser: wx test
   ```

Once you know the index, configure it with `--weather-channel-idx` if needed.

**Important:** The bot cannot automatically detect which channel index corresponds to #weather 
because the MeshCore protocol only provides numeric indices, not channel names. However, since 
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

## Running as a systemd service

For production deployments, especially on Raspberry Pi, you can run the bot as a systemd service that starts automatically on boot:

```bash
sudo cp weather_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable weather_bot
sudo systemctl start weather_bot
```

**📖 Raspberry Pi Zero 2 Headless Setup:** See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for complete instructions on setting up the bot to run automatically on boot in headless mode (no display required).

**📡 Remote SSH Access:** See [SSH_REMOTE_ACCESS.md](SSH_REMOTE_ACCESS.md) for comprehensive instructions on accessing your Raspberry Pi remotely when deployed in remote locations, including VPN setup, port forwarding, and security best practices.

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

### Wrong city returned (city in another country)
Some city names exist in multiple countries (e.g., "York" in UK, USA; "Paris" in France, USA).
By default, the bot returns the first match from the geocoding API.

**Solutions:**

1. **Specify country in the command (recommended):** Users can add the country directly in their weather request:
   - `wx York UK` → Returns York, United Kingdom
   - `wx York USA` → Returns York, Pennsylvania USA  
   - `wx Paris FR` → Returns Paris, France
   - Supports: `UK`, `USA`, `US`, `GB`, or any ISO-3166-1 alpha-2 country code (2 letters)

2. **Use comma-separated format:** Traditional explicit format:
   - `wx York, UK` instead of just `wx York`
   - `wx Paris, France` instead of just `wx Paris`

3. **Configure a default country:** If most users are in one country, run the bot with the `--country` flag:
   ```bash
   python3 weather_bot.py --country GB  # Prefers UK cities
   python3 weather_bot.py --country US  # Prefers US cities
   ```
   
   This filters location searches to prefer cities in the specified country while still
   allowing users to override by specifying a different country in their query (e.g., `wx York USA`).

## API

Weather data is from the free [Open-Meteo API](https://open-meteo.com/) –
no account or API key required.

## License

MIT License – see LICENSE file for details.

