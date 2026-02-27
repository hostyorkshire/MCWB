# Quick Start Guide - MeshCore Weather Bot

**❓ Have questions?** Check the [FAQ](FAQ.md) for common setup questions including "where is the boot setup script?"

## Installation on Raspberry Pi Zero 2

**🍓 For headless setup with auto-start on boot, see [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)**

This is a quick manual installation guide. For automated installation with systemd service, use the installation script or see the full Raspberry Pi setup guide.

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
git clone https://github.com/yourusername/MCWB.git
cd MCWB
```

### 4. Install Python Dependencies

**Recommended: Use a virtual environment** (prevents PEP 668 errors on newer systems):
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Alternative: Install directly** (may fail on Debian 12+, Ubuntu 23.04+ with PEP 668):
```bash
pip3 install -r requirements.txt
# If this fails with "externally-managed-environment", use the virtual environment method above
```

### 5. Configure Radio Channels (Critical Step)

**Before running the bot with your radio, configure which channels it should monitor:**

```bash
# This step CANNOT be done in software - you must use the MeshCore app
```

**Using the MeshCore mobile app:**
1. Open the MeshCore app on your phone/tablet
2. Connect to your companion radio
3. Go to Channel Settings
4. Join/subscribe to channels you want the bot to use:
   - Common examples: `#weather`, `#wxtest`, `#forecast`
   - You can add multiple channels
5. Save your configuration

**Why this matters:**
- The bot cannot add channels for you
- Without this step, the bot won't receive messages from those channels
- This is a one-time setup (unless you want to add more channels later)

### 6. Test the Bot

**Option A: Quick Weather Lookup (No Radio Needed)**
```bash
# Test without connecting to radio hardware
python3 weather_bot.py --location London
python3 weather_bot.py --location Manchester
python3 weather_bot.py --location "York UK"
```

This will fetch and display weather without connecting to your MeshCore radio.

**Option B: Test with Radio Connected**
```bash
# Start the bot and it will listen for commands on any channel
python3 weather_bot.py

# Then send a weather command from your MeshCore app:
# wx London
# wx Manchester  
# wx York UK
```

### 6. Run as Background Service (Auto-Start on Boot)

**Option A: Automated Installation (Recommended)**
```bash
# Run the installation script
./install_service.sh

# The script will:
# - Configure the service for your user and paths
# - Install it to systemd
# - Enable auto-start on boot
# - Optionally start it immediately
```

**Option B: Manual Installation**
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

For complete headless setup instructions, troubleshooting, and advanced configuration, see **[RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)**.

## Usage Examples

### Command Line - One Shot
```bash
python3 weather_bot.py --location "London"
python3 weather_bot.py --location "Manchester"
python3 weather_bot.py --location "Edinburgh"
```

### Quick Weather Lookup (No Radio Needed)

Test the bot without connecting to hardware:

```bash
# Look up weather for any location
python3 weather_bot.py --location London
python3 weather_bot.py --location "York UK"
python3 weather_bot.py --location "Paris FR"
```

The bot will fetch and display weather, then exit. Use this to verify the bot is working before connecting your radio.

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
# Start bot and let it respond on ANY channel automatically (default)
python3 weather_bot.py

# Start bot with specific USB port
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200

# Restrict bot to only respond on channel index 1
python3 weather_bot.py --channel-idx 1

# Enable periodic announcements every 6 hours
python3 weather_bot.py --announce
```

## Running Tests

Verify the installation by running the test suite:

```bash
# Test basic functionality
python3 examples.py

# Test LoRa serial communication
python3 tests/test_lora_serial.py

# Test channel functionality
python3 tests/test_channel_functionality.py

# Test channel examples
python3 example_channels.py
```

All tests run in simulation mode (no hardware required) and should complete successfully.

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
- **First check:** Is the radio subscribed to the channels where users are sending messages?
- Use the MeshCore app to verify/add channel subscriptions
- After adding channels, restart the bot
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
# See detailed protocol frames and debugging info
python3 weather_bot.py --debug
```

### Filter Locations by Country
```bash
# Prefer UK cities when location is ambiguous
python3 weather_bot.py --country GB

# Prefer US cities
python3 weather_bot.py --country US
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
# Find the process and kill it
ps aux | grep weather_bot.py | grep -v grep
kill <PID>

# Or use pkill (if available)
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
