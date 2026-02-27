# Announcement Channel Fix - Summary

## Problem
The bot was announcing on the wrong channel instead of the #weather channel.

## Root Cause
Lines 658-660 in `weather_bot.py` contained a problematic fallback that updated the announcement channel to ANY channel that received messages, even if it wasn't the weather channel:

```python
elif self.weather_channel_idx is None and not self._weather_channel_detected:
    # Fallback: remember this channel only if no weather channel detected yet
    self._announce_channel_idx = channel_idx  # BUG!
```

This caused announcements to be sent to whatever channel received messages first, not the #weather channel.

## Solution
Removed the problematic fallback logic at lines 658-660. 

### New Behavior
- Bot starts with default channel 0 for announcements (if not configured)
- Auto-detects the #weather channel from:
  - Hashtags in messages: `#weather`, `#wx`, "weather channel"
  - Weather commands: `wx London`, `weather Leeds`, etc.
- Updates announcement channel ONLY when weather channel is detected
- Does NOT update announcement channel for non-weather messages

## Configuration for Your Radio

Since your #weather channel is on **channel index 1**, you have two options:

### Option 1: Explicit Configuration (Recommended)
Start the bot with the `--weather-channel-idx 1` flag:

```bash
python3 weather_bot.py --announce --weather-channel-idx 1
```

**Advantages:**
- Announcements start immediately on channel 1
- No waiting for auto-detection
- Guaranteed to use channel 1 from startup

### Option 2: Auto-Detection
Start the bot without specifying the channel:

```bash
python3 weather_bot.py --announce
```

The bot will automatically detect channel 1 when:
- Someone sends a message with `#weather` or `#wx` hashtag on channel 1
- Someone sends a weather command (`wx London`) on channel 1

**Advantages:**
- Zero configuration needed
- Works automatically after first weather command
- Persists across restarts (saved to `logs/.last_weather_channel`)

## For Systemd Service Users

If you're running the bot as a systemd service, update your service file:

### For Raspberry Pi (weather_bot.service)
Edit `/etc/systemd/system/weather_bot.service`:

```ini
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --announce --weather-channel-idx 1
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
```

## Verification

After starting the bot, you should see in the logs:
```
Sent startup announcement to channel_idx=1 (configured)
```

Or if using auto-detection, after the first weather command:
```
Auto-detected #weather channel from WX command on channel_idx=1
Announcements will be sent to channel_idx=1 (detected from weather requests)
```

## Testing

Run the test suite to verify the fix:
```bash
# Test announcements on channel 1
python3 tests/test_announcement_on_channel_1.py

# Test general announcement behavior
python3 tests/test_announcement_channel.py

# Test auto-detection
python3 tests/test_auto_detect_weather_channel.py
```

All tests should pass, confirming that announcements will go to the correct channel.
