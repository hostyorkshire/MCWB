# Channel Naming Convention Guide

## The Definitive Answer

**In Python code, channel names should be WITHOUT the hash (#) prefix.**

```python
# ✅ CORRECT
channel = "wxtest"
channel = "weather"
channel = "alerts"
announce_channel = "wxtest"

# ❌ WRONG
channel = "#wxtest"
channel = "#weather"
channel = "#alerts"
announce_channel = "#wxtest"
```

## Why No Hash in Python?

The hash (#) is a **UI convention** used by the MeshCore mobile/desktop app to visually indicate channels to users (similar to hashtags on social media). It is **not part of the actual channel name** in the underlying protocol.

### How It Works

1. **MeshCore App (User Interface):**
   - Users see: `#weather`, `#wxtest`, `#alerts`
   - The hash is displayed for visual clarity
   - The hash helps users recognize channel names

2. **MeshCore Protocol (Backend/Python):**
   - Channel names: `"weather"`, `"wxtest"`, `"alerts"` (no hash)
   - The protocol only uses the name without the hash
   - Python code should match the protocol

3. **LoRa Transmission (Radio):**
   - Only sends `channel_idx` (0-7)
   - Does not send channel names at all
   - Channel name mapping happens locally

## Examples

### Correct Usage

```python
from weather_bot import WeatherBot

# Weather Bot with announcement channel
bot = WeatherBot(
    node_id="WX_BOT",
    announce_channel="wxtest"  # ✅ No hash
)

# Weather Bot with channel filter
bot = WeatherBot(
    node_id="WX_BOT", 
    channel="weather"  # ✅ No hash
)

# Multiple channels
bot = WeatherBot(
    node_id="WX_BOT",
    channel="weather,alerts,news"  # ✅ No hash on any
)
```

```python
from meshcore import MeshCore

mesh = MeshCore("my_node")
mesh.start()

# Send message to channel
mesh.send_message("Update", "text", channel="weather")  # ✅ No hash

# Set channel filter
mesh.set_channel_filter("weather")  # ✅ No hash
mesh.set_channel_filter(["weather", "alerts"])  # ✅ No hash

mesh.stop()
```

### Wrong Usage

```python
# ❌ This will NOT work correctly
bot = WeatherBot(
    node_id="WX_BOT",
    announce_channel="#wxtest"  # Wrong - has hash
)

# ❌ This creates a channel named "#weather" (with hash in the name)
mesh.send_message("Update", "text", channel="#weather")  # Wrong

# ❌ This filters for a channel literally named "#weather" 
mesh.set_channel_filter("#weather")  # Wrong
```

## Command Line Usage

When starting the Weather Bot from command line:

```bash
# ✅ CORRECT - No hash
python3 weather_bot.py -n WX_BOT --port /dev/ttyUSB1 --baud 115200 \
        --announce-channel wxtest -d

python3 weather_bot.py --channel weather --interactive

python3 weather_bot.py --channel "weather,alerts,news" -d

# ❌ WRONG - Has hash (may appear to work but creates wrong channel name)
python3 weather_bot.py --announce-channel "#wxtest"  # Wrong
python3 weather_bot.py --channel "#weather"  # Wrong
```

## Why This Matters

If you use the hash in your Python code:

1. **Channel mismatch**: The Python code creates a channel named `"#weather"` (with hash as part of name)
2. **App shows**: `##weather` (double hash) or might not recognize it
3. **No communication**: Your bot will be on a different channel than users expect
4. **Confusion**: Users on `#weather` won't see messages sent to `"#weather"`

### Example of the Problem

```python
# User A in MeshCore app
# Joins channel: #weather (app shows #weather, internally uses "weather")

# Bot configured wrong
bot = WeatherBot(channel="#weather")  # This creates channel named "#weather"

# Result:
# - User A is on channel "weather" 
# - Bot is on channel "#weather"
# - They are on DIFFERENT channels
# - No communication happens ❌
```

```python
# CORRECT configuration
bot = WeatherBot(channel="weather")  # This uses channel named "weather"

# Result:
# - User A is on channel "weather"
# - Bot is on channel "weather"  
# - They are on the SAME channel
# - Communication works ✅
```

## Testing the Convention

To verify correct usage:

```python
from weather_bot import WeatherBot

# Test 1: Channel without hash
bot1 = WeatherBot(node_id="TEST1", announce_channel="wxtest")
print(f"Bot1 channel: '{bot1.announce_channel}'")  # Should print: wxtest

# Test 2: Channel with hash (wrong but shows what happens)
bot2 = WeatherBot(node_id="TEST2", announce_channel="#wxtest")
print(f"Bot2 channel: '{bot2.announce_channel}'")  # Will print: #wxtest

# Test 3: Compare
print(f"Are they equal? {bot1.announce_channel == bot2.announce_channel}")  
# Prints: False - they are DIFFERENT channels!
```

## Summary

| Context | Format | Example |
|---------|--------|---------|
| **MeshCore App UI** | With hash `#` | `#weather`, `#wxtest`, `#alerts` |
| **Python Code** | Without hash | `"weather"`, `"wxtest"`, `"alerts"` |
| **Command Line Args** | Without hash | `--channel weather` |
| **LoRa Protocol** | channel_idx only | `0`, `1`, `2`, etc. |

## Quick Reference

```python
# ✅ DO THIS
announce_channel = "wxtest"
channel = "weather"
mesh.send_message("msg", "text", channel="alerts")
mesh.set_channel_filter("weather")

# ❌ NOT THIS  
announce_channel = "#wxtest"  # Wrong
channel = "#weather"  # Wrong
mesh.send_message("msg", "text", channel="#alerts")  # Wrong
mesh.set_channel_filter("#weather")  # Wrong
```

---

**Bottom Line:** Always use channel names **without the hash (#)** in your Python code. The hash is only for display in the MeshCore app UI.
