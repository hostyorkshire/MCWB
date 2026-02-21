# MCWBv2 - MeshCore Weather Bot

Lightweight Python3 weather bot for the MeshCore `#weather` channel.

## Overview

MCWBv2 listens on the MeshCore `#weather` channel and responds to weather
queries using the free [Open-Meteo](https://open-meteo.com/) API (no API key needed).

## Usage

Send any of the following in the `#weather` channel:

```
WX London
wx York
weather Manchester
```

The bot replies on the same channel with current conditions:

```
London, United Kingdom
Conditions: Partly cloudy
Temp: 14.2°C (feels like 12.8°C)
Humidity: 72%
Wind: 18 km/h at 230°
Precipitation: 0.0 mm
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
2. Connect it to your Pi (or PC) via USB.
3. The device typically appears as `/dev/ttyUSB0` or `/dev/ttyACM0` on Linux.
4. Start the bot – it auto-detects the port:

```bash
python3 weather_bot.py
```

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

## Running the bot

```bash
# Auto-detect USB port (recommended)
python3 weather_bot.py

# Specify port and baud rate
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200

# Enable debug output (shows all protocol frames)
python3 weather_bot.py -d

# Enable periodic announcements every 3 hours
python3 weather_bot.py --announce

# Restrict bot to only respond on channel index 1 (e.g., #weather channel)
python3 weather_bot.py --channel-idx 1

# Quick weather lookup (no radio hardware needed)
python3 weather_bot.py --location Leeds
```

### Command line options

```
  -p PORT, --port PORT    Serial port (e.g. /dev/ttyUSB0). Auto-detects if omitted.
  -b BAUD, --baud BAUD    Baud rate (default: 115200)
  -d, --debug             Enable debug output
  -a, --announce          Send periodic announcements every 3 hours
  -c CHANNEL_IDX, --channel-idx CHANNEL_IDX
                          Only respond to messages from this channel index (e.g., 1 for #weather)
  -l LOCATION, --location LOCATION
                          Look up weather and exit (no radio needed)
```

## Channel Filtering

By default, the bot responds to weather queries from **any channel**. To restrict the bot to only respond on a specific channel, use the `--channel-idx` option:

```bash
# Only respond to messages on channel index 1
python3 weather_bot.py --channel-idx 1 --port /dev/ttyUSB0 --baud 115200
```

This is useful when:
- You want to keep the weather bot isolated to a dedicated weather channel
- You have multiple bots running and need to prevent conflicts
- You want to control which channels can invoke the bot

**Note:** Channel indices are numeric (0, 1, 2, etc.) and correspond to the physical channel slots on your MeshCore device. Check your device's channel configuration to determine which index corresponds to your #weather channel.

## Running as a systemd service

```bash
sudo cp weather_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable weather_bot
sudo systemctl start weather_bot
```

## Troubleshooting

### No serial port found
- Check the USB cable and that the companion radio is powered.
- Run `ls /dev/ttyUSB* /dev/ttyACM*` to see available ports.
- Try `--port /dev/ttyUSB0` (or whichever port appears).

### Bot connects but receives no messages
- Ensure the companion radio is subscribed to the `#weather` channel in the
  MeshCore app / firmware configuration.
- Use `--debug` (`-d`) to see raw protocol frames.

### Location not found
- Use the full city name, or add country/region: `wx York, UK`.

## API

Weather data is from the free [Open-Meteo API](https://open-meteo.com/) –
no account or API key required.

## License

MIT License – see LICENSE file for details.

