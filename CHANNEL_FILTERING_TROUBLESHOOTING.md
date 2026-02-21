# Channel Filtering Troubleshooting Guide

## Problem: Bot Not Responding on Channels Other Than wxtest

### Quick Diagnosis

Run this command to check your configuration:
```bash
python3 diagnose_channels.py
```

### Common Issues

#### Issue 1: Channel Filter is Accidentally Enabled

**Symptom:** Bot only responds on one specific channel (e.g., "weather" or "wxtest")

**Cause:** The `--channel` parameter is set in the startup command

**Check:**
```bash
# Check your service file
cat /etc/systemd/system/weather_bot.service | grep ExecStart

# Check if bot is running with channel filter
journalctl -u weather_bot -n 50 | grep "Channel filter"
```

**Fix:**
```bash
# Edit service file
sudo nano /etc/systemd/system/weather_bot.service

# Make sure ExecStart does NOT have --channel parameter:
# CORRECT:
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --port auto --baud 115200 -d

# WRONG:
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --port auto --baud 115200 --channel weather -d

# Then restart
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
```

#### Issue 2: Confusion Between Announce Channel and Channel Filter

**Important:** These are TWO DIFFERENT things:

1. **`--announce-channel`** (default: wxtest)
   - Controls WHERE periodic announcements are sent
   - Does NOT affect which channels the bot listens to
   - Does NOT affect where responses are sent
   - Only affects bot-initiated announcements every 3 hours

2. **`--channel`** (default: none/disabled)
   - Controls WHICH channels the bot accepts queries FROM
   - When set: Bot ONLY accepts queries from specified channel(s)
   - When NOT set: Bot accepts queries from ALL channels
   - Bot ALWAYS replies on the same channel_idx where query came from

**Example:**
```bash
# This accepts queries from ALL channels, but sends announcements to wxtest
python3 weather_bot.py --port auto --baud 115200 --announce-channel wxtest -d

# This ONLY accepts queries from 'weather' channel (and will ignore others!)
python3 weather_bot.py --port auto --baud 115200 --channel weather -d
```

### How the Bot Should Work

#### Default Behavior (NO --channel parameter):

```
User on channel 0 sends "wx London" → Bot replies on channel 0
User on channel 1 sends "wx York"   → Bot replies on channel 1
User on channel 2 sends "wx Leeds"  → Bot replies on channel 2
Every 3 hours                       → Bot announces on wxtest channel
```

#### With Channel Filter (--channel weather):

```
User on channel 0 sends "wx London" → Bot IGNORES (not on 'weather' channel)
User on channel 1 sends "wx York"   → Bot IGNORES (not on 'weather' channel)
User on 'weather' channel           → Bot replies on 'weather' channel
Every 3 hours                       → Bot announces on wxtest channel
```

### Testing

#### Test 1: Check Current Configuration

```bash
# Check service file
cat /etc/systemd/system/weather_bot.service

# Check running process
ps aux | grep weather_bot

# Check logs
journalctl -u weather_bot -n 100 | grep -E "(Channel filter|accepts queries)"
```

You should see:
```
Weather Bot started. Accepts queries from ALL channels.
```

You should NOT see:
```
Channel filter enabled: 'weather' (only accepts messages from these channels)
```

#### Test 2: Interactive Mode

```bash
python3 weather_bot.py --interactive
```

Then type:
```
wx London
```

If it works in interactive mode but not over the radio, the issue is with the radio configuration, not the bot.

#### Test 3: Simulate Different Channels

```bash
python3 test_response_channels.py
```

This will test that the bot accepts and responds correctly on channels 0, 1, and 2.

### Verifying the Fix

After making changes:

1. Restart the service:
```bash
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
```

2. Check the logs:
```bash
journalctl -u weather_bot -f
```

3. Look for:
```
Weather Bot started. Accepts queries from ALL channels.
```

4. Send a test query from a different channel and verify the bot responds.

### Still Having Issues?

If the bot is configured correctly but still not responding on other channels:

1. **Check Physical Radio Configuration:**
   - Verify your radio device has the channels configured
   - Check that channel indices match between sender and bot

2. **Check USB Connection:**
   - With auto-detection: `journalctl -u weather_bot | grep "auto-detected"`
   - Should see: `LoRa connected on /dev/ttyUSBX at XXXXX baud (auto-detected)`

3. **Check for Errors:**
   ```bash
   journalctl -u weather_bot -n 100 | grep -i error
   ```

4. **Check Message Reception:**
   - Enable debug mode: `-d` flag
   - Check logs for incoming messages: `journalctl -u weather_bot -f`
   - You should see: `LoRa RX channel msg from USER on channel_idx X: wx Location`

### Summary

**To accept queries from ALL channels:**
- ✅ Do NOT use `--channel` parameter
- ✅ Service file should use: `--port auto --baud 115200 -d`
- ✅ Bot will accept queries from any channel
- ✅ Bot will reply on the same channel_idx where query came from

**The `--announce-channel` parameter:**
- Only affects periodic announcements (every 3 hours)
- Does NOT affect which channels bot listens to
- Does NOT affect where responses are sent
- Safe to use with any value or default (wxtest)
