# Quick Start Guide - MeshCore Weather Bot

## Recommended LoRa Hardware (Pi Zero 2 W via Micro USB)

The easiest board to use with a Raspberry Pi Zero 2 W is the **LILYGO TTGO LoRa32 V1.6.1**
(868 MHz for UK/EU).  It connects to the Pi via USB and appears as `/dev/ttyUSB0`
automatically — no soldering or GPIO wiring required.

### What you need

| Item | Notes |
|------|-------|
| LILYGO TTGO LoRa32 V1.6.1 | 868 MHz variant for UK/EU; SX1276 chip |
| Micro USB OTG adapter | Plugs into the Pi's data micro USB port (the one closest to the centre) |
| USB-A to micro USB cable | Connects the OTG adapter to the LoRa board |

> **Note:** the Pi Zero 2 W has *two* micro USB ports.  The one closest to the centre is
> the **OTG (data) port** — use this one.  The other port is power-only.

### Quick wiring diagram

```
Pi Zero 2 W (micro USB OTG port)
  └── micro USB OTG adapter (male micro USB → female USB-A)
        └── USB-A to micro USB cable
              └── LILYGO TTGO LoRa32 (micro USB port)
```

Flash [MeshCore firmware](https://github.com/ripplebiz/MeshCore) onto the TTGO board
before connecting it to the Pi.

### DollaTek ESP32 SX1276 Wireless Bridge — will it work?

**Yes**, the DollaTek Wireless Bridge (a Heltec-designed board) uses the same ESP32 + SX1276
combination and its CP2102 chip means it shows up as `/dev/ttyUSB0` automatically, just
like the TTGO LoRa32.

Two things to check before buying:

1. **Frequency band** — the standard listing ships at **470 MHz** (China band).  You need
   the **868 MHz** variant for legal UK/EU use.  Verify this in the board's technical
   specification sheet, not just the product title — listings can be misleading.  Contact
   the seller to confirm the frequency before purchasing if unsure.
2. **Firmware profile** — flash MeshCore using the **Heltec Wireless Bridge** target, not
   the TTGO LoRa32 target.  Grab the correct `.bin` from the
   [MeshCore releases page](https://github.com/ripplebiz/MeshCore/releases).

Add your user to the `dialout` group so the serial port can be opened without `sudo`:

```bash
sudo usermod -aG dialout $USER
# log out and back in for the change to take effect
```

---

## Installation on Raspberry Pi Zero 2

### 1. Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Install Python and Dependencies
```bash
sudo apt-get install -y python3 python3-pip git
```

### 3. Clone Repository
```bash
cd ~
git clone https://github.com/hostyorkshire/MCWB.git
cd MCWB
```

### 4. Install Python Dependencies
```bash
python3 -m pip install -r requirements.txt
```

### 5. Test the Bot
```bash
# Interactive mode
python3 weather_bot.py --interactive

# Try some commands:
# wx London
# wx Manchester
# wx York
```

### 6. Run as Background Service (Optional)

```bash
# Copy service file
sudo cp weather_bot.service /etc/systemd/system/

# Update the service file if your username is not 'pi'
sudo nano /etc/systemd/system/weather_bot.service
# Change User=pi to your username
# Change WorkingDirectory and ExecStart paths if needed

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable weather_bot
sudo systemctl start weather_bot

# Check status
sudo systemctl status weather_bot

# View logs
sudo journalctl -u weather_bot -f
```

## Usage Examples

### Command Line - One Shot
```bash
python3 weather_bot.py --location "London"
python3 weather_bot.py --location "Manchester"
python3 weather_bot.py --location "Edinburgh"
```

### Interactive Mode
```bash
python3 weather_bot.py --interactive
```

Then type commands like:
- `wx London`
- `weather York`
- `wx Birmingham`
- `quit` (to exit)

### Send Message via MeshCore
```bash
# Send message without channel (simulation mode)
python3 meshcore_send.py "wx London" --node-id my_node

# Send message to a specific channel (simulation mode)
python3 meshcore_send.py "wx London" --node-id my_node --channel weather

# Send message via LoRa hardware
python3 meshcore_send.py "wx London" --node-id my_node --port /dev/ttyUSB0 --channel weather
```

### Run Weather Bot on a Specific Channel
```bash
# Start bot broadcasting responses on 'weather' channel (simulation mode)
python3 weather_bot.py --interactive --channel weather

# Start bot with LILYGO TTGO LoRa32 on /dev/ttyUSB0 (868 MHz UK/EU)
python3 weather_bot.py --port /dev/ttyUSB0 --baud 9600 --channel weather

# Run bot with custom node ID and channel
python3 weather_bot.py --node-id my_weather_bot --channel weather
```

## Supported Commands

- `wx [location]` - Get weather for location
- `weather [location]` - Alternative command format

**Examples:**
- `wx London`
- `wx Manchester`
- `weather York`
- `weather Leeds, UK`

## Weather Information Provided

- Current conditions (clear, cloudy, rain, snow, etc.)
- Temperature in Celsius
- "Feels like" temperature
- Humidity percentage
- Wind speed (km/h) and direction (degrees)
- Precipitation (mm)

## Troubleshooting

### Bot not responding
- Check internet connection
- Verify API is accessible: `curl https://api.open-meteo.com/v1/forecast`
- Check logs: `python3 weather_bot.py --debug`

### Location not found
- Use full city/town name
- Try adding country: "York, UK"
- Check spelling

### Raspberry Pi Performance
- Bot is lightweight and should work well
- Typical memory usage: < 50MB
- CPU usage: Minimal when idle

### Service not starting
```bash
# Check service status
sudo systemctl status weather_bot

# View logs
sudo journalctl -u weather_bot -n 50

# Restart service
sudo systemctl restart weather_bot
```

## Advanced Configuration

### Run with Debug Mode
```bash
python3 weather_bot.py --debug --interactive
```

### Custom Node ID
```bash
python3 weather_bot.py --node-id "my_custom_id"
```

### Run in Background (without service)
```bash
nohup python3 weather_bot.py > weather_bot.log 2>&1 &
```

## Stopping the Bot

### Interactive Mode
- Press `Ctrl+C` or type `quit`

### Service Mode
```bash
sudo systemctl stop weather_bot
```

### Background Process
```bash
pkill -f weather_bot.py
```

## Support

For issues or questions:
1. Check the main README.md
2. Review logs with `--debug` flag
3. Open an issue on GitHub

## API Information

This bot uses the free Open-Meteo API:
- No API key required
- Free for non-commercial use
- Reliable and fast
- Website: https://open-meteo.com/

## License

MIT License - Free to use and modify
