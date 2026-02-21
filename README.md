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

# Enable debug output
python3 weather_bot.py -d

# Enable periodic announcements every 3 hours
python3 weather_bot.py --announce

# Quick weather lookup (no radio hardware needed)
python3 weather_bot.py --location Leeds
```

### Command line options

```
  -p PORT, --port PORT    Serial port (auto-detects if omitted)
  -b BAUD, --baud BAUD    Baud rate (default: 115200)
  -d, --debug             Enable debug output
  -a, --announce          Send periodic announcements every 3 hours
  -l LOCATION, --location LOCATION
                          Look up weather and exit (no radio needed)
```

## Running as a systemd service

```bash
sudo cp weather_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable weather_bot
sudo systemctl start weather_bot
```

## How it works

MCWBv2 speaks the MeshCore companion radio binary protocol directly over the
USB serial port.  When a channel message arrives the bot checks whether it
starts with `wx ` or `weather ` (case-insensitive) and, if so, looks up the
location with Open-Meteo's geocoding API, fetches the current conditions, and
sends the formatted response back on the **same channel slot** the query came
from.  No external custom libraries are required – everything is in the single
`weather_bot.py` file.


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

## LoRa Radio Integration

The bot communicates over LoRa using a serial-connected LoRa module (e.g. EBYTE E32,
SX1276-based boards) attached to the Raspberry Pi via USB or UART.

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
# Bot accepts queries from ALL channels
python3 weather_bot.py --port /dev/ttyUSB0 --baud 9600

# From another node: send a weather query over LoRa (on any channel)
python3 meshcore_send.py "wx London" --port /dev/ttyUSB0 --node-id user_node
# Or on a specific channel
python3 meshcore_send.py "wx London" --port /dev/ttyUSB0 --channel weather --node-id user_node
```

3. When **`--port` is omitted** the bot starts in *simulation mode*: messages are logged
   but not transmitted over radio. This is ideal for testing without hardware.

## Examples

### Example 1: Get Weather for London
```bash
$ python3 weather_bot.py --location "London"
London, GB
Conditions: Partly cloudy
Temp: 12.5°C (feels like 11.2°C)
Humidity: 75%
Wind: 15.3 km/h at 230°
Precipitation: 0.0 mm
```

### Example 2: Interactive Session
```bash
$ python3 weather_bot.py --interactive
Weather Bot started. Accepts queries from ALL channels.
Send 'wx [location]' to get weather.
Example: wx London
Listening for messages...

Enter command (or 'quit' to exit): wx York

York, GB
Conditions: Clear sky
Temp: 10.2°C (feels like 8.9°C)
Humidity: 68%
Wind: 12.1 km/h at 180°
Precipitation: 0.0 mm
```

### Example 3: Using with LoRa Hardware
```bash
# Start weather bot - accepts queries from all channels
$ python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d
Weather Bot started. Accepts queries from ALL channels.
Send 'wx [location]' to get weather.
Example: wx London
Listening for messages...

# Send a message from any channel from another node
$ python3 meshcore_send.py "wx Manchester" --channel weather --node-id user_node --port /dev/ttyUSB0
# OR from default channel
$ python3 meshcore_send.py "wx Manchester" --node-id user_node --port /dev/ttyUSB0
# OR from any other channel
$ python3 meshcore_send.py "wx Manchester" --channel alerts --node-id user_node --port /dev/ttyUSB0
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
# Interactive mode for testing
python3 weather_bot.py --interactive

# Or with LoRa hardware (auto-detect port)
python3 weather_bot.py --port auto --baud 115200 -d
```

4. (Optional) Set up as a systemd service for automatic startup:
```bash
sudo cp weather_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable weather_bot
sudo systemctl start weather_bot
```

**Note:** The included `weather_bot.service` file uses `--port auto` to automatically detect USB ports after reboots.

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

## Testing

The project includes comprehensive test suites to verify functionality:

### Run All Tests

```bash
# Test LoRa serial communication
python3 test_lora_serial.py

# Test channel functionality
python3 test_channel_functionality.py

# Test weather bot features
python3 test_weather_bot.py

# Run example demonstrations
python3 examples.py
python3 example_channels.py
```

### Test Coverage

- **test_lora_serial.py**: Tests LoRa serial port communication, message transmission/reception, RTS/DTR control, baud rate validation
- **test_channel_functionality.py**: Tests channel-based broadcasting and filtering
- **test_weather_bot.py**: Tests weather bot message handling and command parsing
- **examples.py**: Demonstrates basic usage patterns
- **example_channels.py**: Demonstrates channel-based communication

All tests use mock objects and simulation mode, so no hardware is required.

## Troubleshooting

### USB Port Issues After Reboot
If your bot stops listening after a reboot, the USB port may have changed:
- **Solution:** Use `--port auto` to automatically detect available USB ports
- Update your systemd service file to use `--port auto` instead of a specific port
- The bot will automatically find and connect to available USB serial devices (ttyUSB*, ttyACM*, ttyAMA*)

Example:
```bash
# Check available ports
ls -l /dev/ttyUSB* /dev/ttyACM*

# Use auto-detection
python3 weather_bot.py --port auto --baud 115200 -d

# Or specify a port manually
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d
```

For systemd service, update `/etc/systemd/system/weather_bot.service`:
```
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --port auto --baud 115200 -d
```

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
