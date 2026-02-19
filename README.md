# MCWB - MeshCore Weather Bot

UK Meshcore weather bot for broadcasting real-time weather data via MeshCore mesh radio network.

## Overview

MCWB is a Python-based weather bot that integrates with the MeshCore mesh radio network to provide real-time UK weather information using the Open-Meteo API. Users can query weather conditions by sending a simple command with their location.

## Features

- **Real-time Weather Data**: Fetches current weather conditions from the Open-Meteo API
- **Location Geocoding**: Automatically converts city/town names to coordinates
- **MeshCore Integration**: Communicates via MeshCore mesh radio network
- **Raspberry Pi Compatible**: Designed to run on Raspberry Pi Zero 2
- **Low Resource Usage**: Minimal dependencies and efficient operation
- **Simple Command Interface**: Just type `wx [location]` to get weather

## Weather Information Provided

- Current conditions (clear, cloudy, rain, snow, etc.)
- Temperature (°C)
- Feels-like temperature
- Humidity (%)
- Wind speed and direction
- Precipitation

## Requirements

- Python 3.7 or higher
- `requests` library
- Internet connection for API access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hostyorkshire/MCWB.git
cd MCWB
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

For Raspberry Pi:
```bash
python3 -m pip install -r requirements.txt
```

## Usage

### Interactive Mode (Testing)

Run the bot in interactive mode to test locally:

```bash
python3 weather_bot.py --interactive
```

Then type commands like:
- `wx London`
- `wx Manchester`
- `wx York`

### One-Shot Mode

Get weather for a specific location and exit:

```bash
python3 weather_bot.py --location "London"
```

### Daemon Mode

Run the bot as a daemon to listen for mesh network messages:

```bash
python3 weather_bot.py
```

### Command Line Options

```
usage: weather_bot.py [-h] [-n NODE_ID] [-c CHANNEL] [-p PORT] [-b BAUD] [-d] [-i] [-l LOCATION]

MeshCore Weather Bot - UK Weather via mesh radio network

optional arguments:
  -h, --help            show this help message and exit
  -n NODE_ID, --node-id NODE_ID
                        Node ID for this bot (default: weather_bot)
  -c CHANNEL, --channel CHANNEL
                        Channel to broadcast responses on (optional)
  -p PORT, --port PORT  Serial port for LoRa module (e.g., /dev/ttyUSB0).
                        When omitted the bot runs in simulation mode.
  -b BAUD, --baud BAUD  Baud rate for LoRa serial connection (default: 9600)
  -d, --debug           Enable debug output
  -i, --interactive     Run in interactive mode for testing
  -l LOCATION, --location LOCATION
                        Get weather for a specific location and exit
```

#### Channel Broadcasting

The weather bot can broadcast responses to a specific channel:

```bash
# Broadcast weather responses on the 'weather' channel
python3 weather_bot.py --channel weather --interactive

# Run with LoRa hardware on /dev/ttyUSB0
python3 weather_bot.py --port /dev/ttyUSB0 --baud 9600 --channel weather

# Run without channel (default - broadcast to all)
python3 weather_bot.py --interactive
```

## Command Format

To request weather information, send a message in one of these formats:

- `wx [location]` - Example: `wx London`
- `weather [location]` - Example: `weather Manchester`

The bot will respond with current weather conditions for the specified location.

## MeshCore Integration

### meshcore.py

Core library for MeshCore mesh radio network communication. Provides:
- Message sending and receiving
- Message handler registration
- Node management
- **Channel-based broadcasting and filtering**

### Channel Support

MeshCore now supports broadcasting messages to specific channels. This allows you to:
- Send messages to specific channels for organized communication
- Filter incoming messages by channel
- Create separate communication streams (e.g., weather, news, alerts)

#### Broadcasting to a Channel

```python
from meshcore import MeshCore

mesh = MeshCore("my_node")
mesh.start()

# Send to a specific channel
mesh.send_message("Weather alert!", "text", channel="weather")

# Send without channel (broadcast to all)
mesh.send_message("General message", "text")
```

#### Filtering Messages by Channel

```python
# Listen only to messages on the 'weather' channel
mesh.set_channel_filter("weather")

# Listen to all channels (default)
mesh.set_channel_filter(None)
```

### meshcore_send.py

Command-line utility for sending messages via MeshCore:

```bash
# Send without channel (simulation mode)
python3 meshcore_send.py "wx London" --node-id sender_node

# Send to a specific channel (simulation mode)
python3 meshcore_send.py "Weather update" --node-id sender_node --channel weather

# Send via LoRa hardware
python3 meshcore_send.py "wx London" --node-id sender_node --port /dev/ttyUSB0 --channel weather
```

## Recommended Hardware for Raspberry Pi Zero 2 W

The Raspberry Pi Zero 2 W has a **micro USB OTG port** (the port closest to the centre of
the board) which can act as a USB host when used with a micro USB OTG adapter.  The other
micro USB port is power-only.

To connect a LoRa board via USB you need:
- A **micro USB OTG adapter** (male micro USB → female USB-A)
- A **USB-A to micro USB cable** to connect the LoRa board to the adapter

### Recommended board: LILYGO TTGO LoRa32

The **LILYGO TTGO LoRa32 V1.6.1** (SX1276, 868 MHz for UK/EU) is the recommended
choice for this project on a Pi Zero 2 W — it has official MeshCore firmware support,
connects over USB with no extra wiring, and is powered directly from the Pi:

| Feature | Detail |
|---------|--------|
| Chip | ESP32 + SX1276 |
| USB interface | CP2102 USB-to-UART (appears as `/dev/ttyUSB0`) |
| Frequency | 868 MHz (UK/EU) |
| MeshCore support | ✅ Official firmware available |
| Power via USB | ✅ Powered directly from the Pi OTG port |
| Form factor | Small – breadboard and case friendly |

Flash it with the [MeshCore firmware for TTGO LoRa32](https://github.com/ripplebiz/MeshCore)
before connecting to the Pi.

### Alternative: LILYGO T-Beam

The **LILYGO T-Beam v1.1** is another popular choice.  It adds an onboard GPS module
and battery connector, which is useful if you want the Pi Zero 2 W + LoRa node to be
portable.  It also uses a CP2102 or CH9102 chip so it shows up as `/dev/ttyUSB0`.

### Wiring

```
Pi Zero 2 W                      LILYGO TTGO LoRa32 / T-Beam
──────────────────────────────────────────────────────────────
micro USB OTG port
  └── micro USB OTG adapter
        └── USB-A to micro USB cable  ──►  micro USB port
                                            (powers the board and
                                             creates /dev/ttyUSB0)
```

### Starting the weather bot with the LoRa board attached

```bash
# 868 MHz UK band, default baud rate 9600
python3 weather_bot.py --port /dev/ttyUSB0 --baud 9600 --channel weather
```

If the device does not appear as `/dev/ttyUSB0` run `dmesg | tail` immediately after
plugging it in to see which port the kernel assigned (it may be `/dev/ttyACM0` on boards
that use the CH9102 chip).

You may also need to add your user to the `dialout` group so Python can open the port
without `sudo`:

```bash
sudo usermod -aG dialout $USER
# log out and back in for the change to take effect
```

## LoRa Radio Integration

The bot communicates over LoRa using a serial-connected LoRa module (e.g. LILYGO TTGO
LoRa32, LILYGO T-Beam, or any SX1276-based board) attached to the Raspberry Pi via USB
or UART.

### Message Format over LoRa

Messages are transmitted as newline-delimited JSON:

```json
{"sender":"weather_bot","content":"wx York","type":"text","timestamp":1234567890.0,"channel":"weather"}
```

### Connecting a LoRa Module

1. Connect your LoRa serial module to the Pi (e.g., `/dev/ttyUSB0` or `/dev/ttyAMA0`).
2. Start the weather bot with `--port` and, optionally, `--baud`:

```bash
# Listen for 'wx <location>' requests and reply – all over LoRa
python3 weather_bot.py --port /dev/ttyUSB0 --baud 9600 --channel weather

# From another node: send a weather query over LoRa
python3 meshcore_send.py "wx London" --port /dev/ttyUSB0 --channel weather --node-id user_node
```

3. When **`--port` is omitted** the bot starts in *simulation mode*: messages are logged
   but not transmitted over radio. This is ideal for testing without hardware.

## Examples

### Example 1: Get Weather for London
```bash
$ python3 weather_bot.py --location "London"
Weather for London, GB
Conditions: Partly cloudy
Temp: 12.5°C (feels like 11.2°C)
Humidity: 75%
Wind: 15.3 km/h at 230°
Precipitation: 0.0 mm
```

### Example 2: Interactive Session
```bash
$ python3 weather_bot.py --interactive
Weather Bot started. Send 'wx [location]' to get weather.
Example: wx London
Listening for messages...

Enter command (or 'quit' to exit): wx York

Weather for York, GB
Conditions: Clear sky
Temp: 10.2°C (feels like 8.9°C)
Humidity: 68%
Wind: 12.1 km/h at 180°
Precipitation: 0.0 mm
```

### Example 3: Broadcasting to a Channel
```bash
# Start weather bot broadcasting on 'weather' channel
$ python3 weather_bot.py --channel weather --interactive
Weather Bot started. Send 'wx [location]' to get weather.
Example: wx London
Listening for messages...

Enter command (or 'quit' to exit): wx London

Weather for London, GB
Conditions: Partly cloudy
Temp: 12.5°C (feels like 11.2°C)
Humidity: 75%
Wind: 15.3 km/h at 230°
Precipitation: 0.0 mm
# Response broadcast on 'weather' channel

# Send a message to the weather channel
$ python3 meshcore_send.py "wx Manchester" --channel weather --node-id user_node
```

## Raspberry Pi Zero 2 Setup

The bot is optimized for Raspberry Pi Zero 2:

1. Ensure you have Python 3.7+ installed:
```bash
python3 --version
```

2. Install dependencies:
```bash
sudo apt-get update
sudo apt-get install python3-pip
python3 -m pip install -r requirements.txt
```

3. Run the bot:
```bash
python3 weather_bot.py --interactive
```

4. (Optional) Set up as a systemd service for automatic startup:
```bash
sudo cp weather_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable weather_bot
sudo systemctl start weather_bot
```

## API Information

### Open-Meteo API

This bot uses the free Open-Meteo API:
- **Geocoding API**: https://geocoding-api.open-meteo.com/v1/search
- **Weather API**: https://api.open-meteo.com/v1/forecast

No API key required! The Open-Meteo API is free for non-commercial use.

### Weather Codes

The bot translates WMO weather codes to human-readable descriptions:
- 0: Clear sky
- 1-3: Clear to overcast
- 45-48: Fog
- 51-67: Drizzle and rain
- 71-77: Snow
- 80-86: Rain/snow showers
- 95-99: Thunderstorms

## Architecture

```
┌─────────────────┐
│  User Input     │
│  (wx London)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Weather Bot    │
│  weather_bot.py │
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌──────────────┐
│  Geocoding API  │  │  Weather API │
│  (Location →    │  │  (Coords →   │
│   Coordinates)  │  │   Weather)   │
└─────────────────┘  └──────────────┘
         │                  │
         └────────┬─────────┘
                  ▼
         ┌─────────────────┐
         │  MeshCore       │
         │  meshcore.py    │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Mesh Network   │
         │  (Radio TX/RX)  │
         └─────────────────┘
```

## Troubleshooting

### Location Not Found
If the bot can't find a location, try:
- Using the full city name
- Adding county or region (e.g., "York, UK")
- Checking spelling

### API Connection Issues
- Ensure you have internet connectivity
- Check that Open-Meteo API is accessible
- Verify firewall settings

### Raspberry Pi Performance
- The bot is lightweight and should run well on Pi Zero 2
- For best performance, ensure Python 3.7+ is installed
- Consider running in daemon mode for continuous operation

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Credits

- Weather data provided by [Open-Meteo](https://open-meteo.com/)
- Built for MeshCore mesh radio network

## Support

For issues or questions, please open an issue on GitHub.
