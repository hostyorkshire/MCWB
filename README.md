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
# Basic usage - accepts queries from all channels
python3 weather_bot.py

# With LoRa hardware
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d

# With debug output
python3 weather_bot.py -d
```

**Note:** The bot accepts weather queries from ALL channels and replies on the same channel where each query came from.

### Command Line Options

```
usage: weather_bot.py [-h] [-n NODE_ID] [-d] [-i] [-p PORT]
                      [-b BAUD] [-c CHANNEL] [-l LOCATION]

MeshCore Weather Bot - UK Weather via mesh radio network

options:
  -h, --help            show this help message and exit
  -n NODE_ID, --node-id NODE_ID
                        Node ID for this bot (default: weather_bot)
  -d, --debug           Enable debug output
  -i, --interactive     Run in interactive mode for testing
  -p PORT, --port PORT  Serial port for LoRa module (e.g., /dev/ttyUSB0).
                        When omitted the bot runs in simulation mode
                        (no radio hardware required).
  -b BAUD, --baud BAUD  Baud rate for LoRa serial connection (default: 9600)
  -c CHANNEL, --channel CHANNEL
                        Channel filter: only accept messages from specified
                        channel(s). Can be a single channel (e.g., 'weather')
                        or comma-separated list (e.g., 'weather,alerts').
                        When omitted, accepts messages from ALL channels.
  -l LOCATION, --location LOCATION
                        Get weather for a specific location and exit
```

#### How the Bot Handles Channels

The weather bot accepts queries from ALL channels and replies accordingly:

**✅ Accepts queries from ANY channel**
- Users can send "wx London" from the default channel (channel_idx 0)
- Users can send "wx London" from #weather channel
- Users can send "wx London" from any other channel
- The bot processes ALL weather queries regardless of channel

**✅ Replies on the SAME channel**
- If query came from channel_idx 0 (default), reply goes to channel_idx 0
- If query came from channel_idx 1, reply goes to channel_idx 1
- If query came from channel_idx 2, reply goes to channel_idx 2
- This ensures users always receive their responses on the channel they used

**How it works:**
The bot uses the `channel_idx` from the incoming message to send replies. This works 
regardless of how different nodes map channel names to indices, because the reply uses 
the exact same numeric index that the query came from.

**Example:**
```bash
# Run the bot
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d

# ✅ User1 sends "wx London" from default channel → Gets reply on default channel
# ✅ User2 sends "wx York" from #weather → Gets reply on #weather
# ✅ User3 sends "wx Leeds" from #alerts → Gets reply on #alerts
# All queries are processed, all users get their replies!
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
Weather Bot started. Accepts queries from ALL channels.
Send 'wx [location]' to get weather.
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
