# Quick Start Guide

## TL;DR

```bash
# Run the weather bot (that's it!)
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d
```

No `--channel` parameter needed. The bot automatically:
- ✅ Accepts weather queries from **all channels**
- ✅ Replies on the **same channel** where each query came from
- ✅ Ensures users receive responses regardless of their channel setup

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
1. Bot is running: `python3 weather_bot.py -d`
2. Your radio is connected to the mesh network
3. Query format is correct: `wx [location]` or `weather [location]`

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
