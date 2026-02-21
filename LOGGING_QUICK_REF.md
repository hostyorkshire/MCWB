# Logging & Channel Naming - Quick Reference

## 🔍 View Logs - Easy Commands

```bash
# List all available log files
./logs.sh list

# View last 50 lines of bot log
./logs.sh bot -n 50

# Follow bot log in real-time (Ctrl+C to stop)
./logs.sh bot -f

# View only errors
./logs.sh bot --errors

# Search for specific text
./logs.sh bot --grep "weather"

# View error log (errors + stack traces)
./logs.sh bot-error

# Clear all log files
./logs.sh clear
```

## 📁 Log Files Location

**Directory**: `logs/`

- `weather_bot.log` - Main log (all levels)
- `weather_bot_error.log` - Errors only

**Features**:
- Auto-rotation at 10MB
- Keeps 5 backup files
- Timestamps on every entry

## 🏷️ Channel Naming Convention

### ✅ CORRECT (Python code)

```python
# NO hash (#) in Python!
channel = "wxtest"
channel = "weather"
announce_channel = "alerts"
```

```bash
# Command line - NO hash
python3 weather_bot.py --channel weather
python3 weather_bot.py --announce-channel wxtest
```

### ❌ WRONG (Don't do this)

```python
# WITH hash - Wrong!
channel = "#wxtest"      # Creates channel named "#wxtest"
channel = "#weather"     # Creates channel named "#weather"
```

## 💡 Why?

- **Hash (#) is UI only** - MeshCore app shows `#weather` to users
- **Protocol uses no hash** - Actual channel name is `"weather"`
- **Python matches protocol** - Use `"weather"` not `"#weather"`

## 🔧 Common Tasks

### Check for errors after running
```bash
./logs.sh bot-error
```

### Verify bot started correctly
```bash
./logs.sh bot -n 20
```

### Monitor bot in real-time
```bash
# Terminal 1: Run bot
python3 weather_bot.py -n WX_BOT --port /dev/ttyUSB1 --baud 115200 -d

# Terminal 2: Follow logs
./logs.sh bot -f
```

### Debug specific issues
```bash
./logs.sh bot --grep "geocoding"    # Location lookups
./logs.sh bot --grep "API error"    # API problems
./logs.sh bot --grep "connection"   # Connection issues
./logs.sh bot --grep "channel"      # Channel operations
```

### View startup configuration
```bash
./logs.sh bot -n 20  # Shows node ID, port, channels, etc.
```

## 📚 Full Documentation

- **Logging System**: See `LOGGING_GUIDE.md`
- **Channel Naming**: See `CHANNEL_NAMING_CONVENTION.md`
- **Help**: Run `./logs.sh --help`

---

**Pro Tip**: Keep logs open in a second terminal while running the bot for real-time monitoring!
