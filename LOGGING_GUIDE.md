# Logging System Documentation

## Overview

The MCWB Weather Bot now includes a comprehensive file-based logging system that captures all execution details and errors to log files in the `logs/` directory.

## Log Files

The system creates the following log files:

- **`weather_bot.log`** - Main application log (INFO, DEBUG, WARNING, ERROR, CRITICAL)
- **`weather_bot_error.log`** - Error-only log (ERROR and CRITICAL messages with full stack traces)
- **`meshcore.log`** - MeshCore library log (if/when implemented)
- **`meshcore_error.log`** - MeshCore errors (if/when implemented)

## Viewing Logs

### Quick Command

Use the `logs.sh` script for easy log viewing:

```bash
# List all available log files
./logs.sh list

# View bot log (last 50 lines)
./logs.sh bot -n 50

# Follow bot log in real-time (like tail -f)
./logs.sh bot -f

# View only errors
./logs.sh bot --errors

# Search for specific text
./logs.sh bot --grep "weather"

# View error log
./logs.sh bot-error

# Clear all logs
./logs.sh clear
```

### Python Command

Or use the Python script directly:

```bash
python3 viewlogs.py list
python3 viewlogs.py bot -n 100
python3 viewlogs.py bot -f
```

### Manual Viewing

You can also view logs manually:

```bash
# View latest log
cat logs/weather_bot.log

# Follow log in real-time
tail -f logs/weather_bot.log

# View last 100 lines
tail -n 100 logs/weather_bot.log

# Search for errors
grep -i "error" logs/weather_bot.log

# View errors only
cat logs/weather_bot_error.log
```

## Log Format

Logs use the following format:

```
[YYYY-MM-DD HH:MM:SS] logger_name [LEVEL]: message
```

Example:
```
[2026-02-21 21:37:57] weather_bot [INFO]: Weather Bot Starting
[2026-02-21 21:37:57] weather_bot [ERROR]: Geocoding error: Connection timeout
```

### Log Levels

- **DEBUG** - Detailed diagnostic information (only when `-d` flag is used)
- **INFO** - General informational messages
- **WARNING** - Warning messages (potential issues)
- **ERROR** - Error messages (failures that don't stop the bot)
- **CRITICAL** - Critical failures (severe issues)

## What Gets Logged

### Startup Information
- Bot configuration (node ID, serial port, baud rate)
- Channel settings
- Timestamp and version

### Weather Requests
- Location geocoding attempts
- API requests and responses
- Successful weather data retrieval
- Location not found warnings

### Errors
- API connection failures
- Geocoding errors
- Weather data fetch errors
- Serial port issues
- Any unexpected exceptions (with full stack traces)

### Debug Information (when `-d` flag is used)
- Message processing details
- Channel mapping information
- LoRa transmission details
- MeshCore protocol messages

## Log Rotation

Logs are automatically rotated to prevent files from growing too large:

- **Max file size**: 10 MB
- **Backup files kept**: 5
- **Naming**: `weather_bot.log.1`, `weather_bot.log.2`, etc.

When a log reaches 10 MB, it's renamed to `.log.1` and a new `.log` file is created. Older backups are shifted (`.log.1` → `.log.2`) and the oldest is deleted.

## Clearing Logs

To clear all log files:

```bash
# Interactive (asks for confirmation)
./logs.sh clear

# Non-interactive (skips confirmation)
./logs.sh clear -y
```

Or manually:

```bash
rm logs/*.log*
```

## Examples

### Monitor bot in real-time

```bash
# Terminal 1: Run the bot
python3 weather_bot.py -n WX_BOT --port /dev/ttyUSB1 --baud 115200 -d

# Terminal 2: Follow the log
./logs.sh bot -f
```

### Check for errors after running

```bash
# View all errors
./logs.sh bot-error

# Or search main log for errors
./logs.sh bot --errors
```

### Debug a specific issue

```bash
# Search for geocoding issues
./logs.sh bot --grep "geocoding"

# Search for API errors
./logs.sh bot --grep "api error"

# View last 200 lines
./logs.sh bot -n 200
```

### View startup configuration

```bash
# Shows bot config at startup
./logs.sh bot -n 20
```

## Integration with Weather Bot

The logging system is automatically integrated into the Weather Bot:

```python
from weather_bot import WeatherBot

# Logging is automatically set up
bot = WeatherBot(node_id="WX_BOT", debug=True)  # debug=True enables DEBUG level
bot.start()

# All operations are logged:
# - Startup info
# - Message processing
# - API requests
# - Errors with stack traces
```

## Troubleshooting

### Log file not found

If you see "Log file not found", the bot hasn't run yet. Logs are created when the bot starts.

### Permission denied

Make sure the `logs/` directory is writable:

```bash
chmod 755 logs/
```

### Logs too large

If logs grow too large, they're automatically rotated. You can also manually clear them:

```bash
./logs.sh clear
```

### Can't view logs

Make sure the scripts are executable:

```bash
chmod +x logs.sh
chmod +x viewlogs.py
```

## Advanced Usage

### Grep with context

```bash
# View 5 lines before and after each error
grep -B 5 -A 5 "ERROR" logs/weather_bot.log
```

### Follow multiple logs

```bash
# Follow bot log and error log simultaneously
tail -f logs/weather_bot.log logs/weather_bot_error.log
```

### Search across all logs

```bash
# Search for text in all log files
grep -r "connection" logs/
```

### Filter by date/time

```bash
# View logs from specific time
grep "2026-02-21 14:" logs/weather_bot.log
```

## Log Analysis Tips

### Find most common errors

```bash
grep "ERROR" logs/weather_bot.log | sort | uniq -c | sort -rn
```

### Count errors by type

```bash
grep "ERROR" logs/weather_bot.log | cut -d: -f4 | sort | uniq -c
```

### View only successful weather requests

```bash
grep "Weather data received successfully" logs/weather_bot.log
```

### Check bot uptime

```bash
grep "Weather Bot Starting" logs/weather_bot.log | wc -l
```

## File Locations

- **Log directory**: `logs/`
- **Log viewer script**: `viewlogs.py`
- **Quick script**: `logs.sh`
- **Logging config**: `logging_config.py`

---

**Need help?** Run `./logs.sh --help` for usage information.
