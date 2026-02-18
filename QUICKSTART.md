# Quick Start Guide - MeshCore Weather Bot

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
python3 meshcore_send.py "wx London" --node-id my_node
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
