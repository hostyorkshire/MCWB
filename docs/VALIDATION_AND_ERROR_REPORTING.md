# Validation and Error Reporting Guide

This guide covers configuration validation, error handling, and troubleshooting tips for the MeshCore Weather Bot.

## Table of Contents

- [Channel Configuration Validation](#channel-configuration-validation)
- [Theme Configuration](#theme-configuration)
- [API Error Responses](#api-error-responses)
- [Debugging and Logging](#debugging-and-logging)
- [Common Configuration Errors](#common-configuration-errors)
- [Troubleshooting Tips](#troubleshooting-tips)

---

## Channel Configuration Validation

### Valid Channel Indices

MeshCore supports **8 channels** (indices 0-7):
- Channel 0: Default/Public channel
- Channels 1-7: Custom channels you configure in the MeshCore app

### Configuration Parameters

#### `--channel-idx` (Message Filtering)
Controls which channel the bot accepts messages from:

```bash
# Valid examples
python3 weather_bot.py --channel-idx 0  # Only respond to channel 0
python3 weather_bot.py --channel-idx 1  # Only respond to channel 1 (#weather)
python3 weather_bot.py --channel-idx 7  # Only respond to channel 7

# INVALID - will cause an error
python3 weather_bot.py --channel-idx 8   # ❌ Out of range (max is 7)
python3 weather_bot.py --channel-idx -1  # ❌ Negative not allowed
```

**Error Message Example:**
```
❌ ERROR: Invalid channel index: 8. 
Channel index must be between 0 and 7.
  Valid channel indices: 0, 1, 2, 3, 4, 5, 6, 7
  Your value: 8
  Tip: Check your --channel-idx parameter value.
```

#### `--weather-channel-idx` (Announcement Channel)
Controls which channel the bot sends announcements to:

```bash
# Valid examples
python3 weather_bot.py --weather-channel-idx 1  # Announce on channel 1
python3 weather_bot.py --weather-channel-idx 0  # Announce on channel 0

# INVALID - will cause an error
python3 weather_bot.py --weather-channel-idx 10  # ❌ Out of range
```

**Error Message Example:**
```
❌ ERROR: Invalid weather channel index: 10.
Channel index must be between 0 and 7.
  Valid channel indices: 0, 1, 2, 3, 4, 5, 6, 7
  Your value: 10
  Tip: Check your --weather-channel-idx parameter value.
```

#### `--channel` (Channel Names)
Specify channel names for filtering (without # prefix):

```bash
# Correct ✓
python3 weather_bot.py --channel weather
python3 weather_bot.py --channel weather,alerts
python3 weather_bot.py --channel "weather,forecast,sensors"

# Incorrect (but will work with a warning)
python3 weather_bot.py --channel "#weather"  # ⚠️ Don't use # prefix
python3 weather_bot.py --channel ""          # ⚠️ Empty string
```

**Warning Message Example:**
```
⚠️  WARNING: Channel name '#weather' starts with '#'.
  Channel names should NOT include the '#' prefix.
  Use 'weather' instead of '#weather'.
```

### Validation at Startup

The bot validates all channel parameters when it starts:

```
✓ Validated channel index filter: channel_idx=1
✓ Validated weather channel index: channel_idx=1
✓ Validated channel names: weather, alerts
```

If validation fails, the bot will:
1. Print an error message to the console
2. Log the error to `logs/weather_bot_error.log`
3. Exit with an error code

---

## Theme Configuration

### Web Dashboard Themes

The web dashboard supports two themes:
- **Dark theme** (default) - Best for low-light environments
- **Light theme** - Best for bright environments

### How Themes Work

Themes are managed client-side using JavaScript and browser localStorage:

1. **Default**: Dark theme is applied on first visit
2. **User Selection**: Clicking the theme toggle button saves the preference
3. **Persistence**: Theme preference is stored in browser localStorage
4. **Auto-load**: Saved theme is automatically applied on subsequent visits

### Theme Storage

Theme preference is stored at:
```
localStorage.getItem('theme')  // Returns 'dark' or 'light'
```

### Troubleshooting Theme Issues

#### Theme Not Persisting
**Symptom**: Theme resets to dark on every page load

**Solutions**:
1. Check if browser localStorage is enabled:
   ```javascript
   // Open browser console (F12) and run:
   localStorage.setItem('test', '1');
   console.log(localStorage.getItem('test')); // Should print '1'
   ```

2. Clear browser cache and localStorage:
   - Chrome/Edge: Settings → Privacy → Clear browsing data
   - Firefox: Settings → Privacy → Clear Data
   - Safari: Preferences → Privacy → Manage Website Data

3. Check browser privacy settings:
   - Ensure "Block third-party cookies" is not enabled
   - Disable private/incognito mode (doesn't persist localStorage)

#### Theme Toggle Button Not Working
**Symptom**: Clicking theme button doesn't change theme

**Solutions**:
1. Check browser console for JavaScript errors (F12)
2. Verify JavaScript is enabled in browser settings
3. Try a hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
4. Check if `/static/img/emoji/*.svg` files are accessible

---

## API Error Responses

### Standardized Error Format

All API endpoints return errors in a consistent format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2026-02-27T23:54:58.196Z",
  "details": {
    "additional_info": "value",
    "tip": "Helpful troubleshooting tip"
  }
}
```

### Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `INVALID_LOG_TYPE` | Invalid log type requested | 400 |
| `CHANNELS_FILE_NOT_FOUND` | No channels.json file | 404 |
| `CHANNELS_FILE_CORRUPT` | Cannot parse channels.json | 500 |
| `CHANNELS_FILE_READ_ERROR` | Cannot read channels.json | 500 |
| `STATS_RESET_FAILED` | Failed to reset statistics | 500 |
| `LOG_CLEAR_FAILED` | Failed to clear log files | 500 |

### Example API Errors

#### Invalid Log Type
```bash
curl http://localhost:5000/api/logs/invalid
```
Response:
```json
{
  "success": false,
  "error": "Invalid log type: 'invalid'",
  "error_code": "INVALID_LOG_TYPE",
  "timestamp": "2026-02-27T23:54:58.196Z",
  "details": {
    "valid_log_types": ["bot", "bot_error", "meshcore", "meshcore_error"],
    "tip": "Use one of: bot, bot_error, meshcore, meshcore_error"
  }
}
```

#### Channels File Not Found
```bash
curl http://localhost:5000/api/channels
```
Response (if no channels detected yet):
```json
{
  "success": false,
  "error": "Channels file not found",
  "error_code": "CHANNELS_FILE_NOT_FOUND",
  "timestamp": "2026-02-27T23:54:58.196Z",
  "details": {
    "file_path": "/home/pi/MCWB/logs/channels.json",
    "tip": "The bot needs to receive at least one message to detect channels. Ensure the bot is running and connected to your radio."
  }
}
```

### Success Responses

Successful operations return:
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "timestamp": "2026-02-27T23:54:58.196Z",
  "data": {
    "key": "value"
  }
}
```

---

## Debugging and Logging

### Enable Debug Mode

Start the bot with debug logging:
```bash
python3 weather_bot.py --debug
```

Debug mode provides:
- Verbose logging of all operations
- Detailed error messages
- Protocol-level message information
- LED activity logging (when enabled)

### Log Files

The bot maintains four log files in the `logs/` directory:

| Log File | Purpose |
|----------|---------|
| `weather_bot.log` | General bot activity |
| `weather_bot_error.log` | Error messages only |
| `meshcore.log` | MeshCore protocol messages |
| `meshcore_error.log` | MeshCore errors |

### Viewing Logs

**Command line:**
```bash
# View latest log entries
tail -f logs/weather_bot.log

# View errors only
tail -f logs/weather_bot_error.log

# Search logs for specific errors
grep -i "error\|warning" logs/weather_bot.log
```

**Web Dashboard:**
- Navigate to the dashboard (default: `http://localhost:5000`)
- Click "View Logs" to see all log files
- Logs auto-refresh every 5 seconds

**Python script:**
```bash
python3 viewlogs.py
```

### Channel Validation Logging

When channels are validated at startup, you'll see:
```
2026-02-27 23:54:58 INFO: ✓ Validated channel index filter: channel_idx=1
2026-02-27 23:54:58 INFO: ✓ Validated weather channel index: channel_idx=1
2026-02-27 23:54:58 INFO: ✓ Validated channel names: weather, alerts
```

If validation fails:
```
2026-02-27 23:54:58 ERROR: Invalid channel index: 8. Channel index must be between 0 and 7.
```

---

## Common Configuration Errors

### Error 1: Invalid Channel Index

**Symptom:**
```
❌ ERROR: Invalid channel index: 8.
Channel index must be between 0 and 7.
```

**Cause:** Using a channel index outside the valid range (0-7)

**Solution:**
```bash
# Wrong
python3 weather_bot.py --channel-idx 8

# Correct
python3 weather_bot.py --channel-idx 1
```

### Error 2: Channel Name with # Prefix

**Symptom:**
```
⚠️  WARNING: Channel name '#weather' starts with '#'.
  Channel names should NOT include the '#' prefix.
  Use 'weather' instead of '#weather'.
```

**Cause:** Including the `#` symbol in the channel name parameter

**Solution:**
```bash
# Wrong (but will work with warning)
python3 weather_bot.py --channel "#weather"

# Correct
python3 weather_bot.py --channel "weather"
```

### Error 3: Empty Channel Name

**Symptom:**
```
⚠️  WARNING: --channel parameter provided but contains no valid channel names.
  The bot will respond on ALL channels by default.
```

**Cause:** Passing an empty string or only whitespace to `--channel`

**Solution:**
```bash
# Wrong
python3 weather_bot.py --channel ""
python3 weather_bot.py --channel "  "

# Correct
python3 weather_bot.py --channel "weather"
# Or omit --channel entirely to respond on all channels
python3 weather_bot.py
```

### Error 4: Channels Not Detected

**Symptom:** API returns "Channels file not found" error

**Cause:** Bot hasn't received any messages yet, or radio not connected

**Solution:**
1. Verify radio is connected:
   ```bash
   ls -la /dev/ttyUSB* /dev/ttyACM*
   ```

2. Check bot is running:
   ```bash
   systemctl status weather_bot.service
   # or
   ps aux | grep weather_bot
   ```

3. Send a test message from your radio:
   ```
   wx London
   ```

4. Check if channels.json was created:
   ```bash
   cat logs/channels.json
   ```

---

## Troubleshooting Tips

### Quick Diagnostics

Run these commands to diagnose issues:

```bash
# 1. Check bot is running
systemctl status weather_bot.service

# 2. Check for recent errors
tail -n 50 logs/weather_bot_error.log

# 3. Check channel detection
cat logs/channels.json

# 4. Test bot without radio (offline test)
python3 weather_bot.py --location "London" --debug
```

### Enable Verbose Logging

For maximum debugging information:

```bash
# Start bot with debug logging
python3 weather_bot.py --debug

# Watch logs in real-time
tail -f logs/weather_bot.log

# In another terminal, send test messages from your radio
```

### Verify Channel Configuration

Check which channels the bot is listening on:

```bash
# Check bot startup messages
grep "channel" logs/weather_bot.log | head -20

# Look for lines like:
# "✓ Validated channel names: weather, alerts"
# "Using configured weather channel: channel_idx=1"
# "Bot will respond on ALL channels"
```

### Test Channel Validation

Test validation without starting the bot:

```bash
# Valid configuration (will start successfully)
python3 weather_bot.py --channel-idx 1 --weather-channel-idx 1 --location "London"

# Invalid configuration (will fail with error)
python3 weather_bot.py --channel-idx 10 --location "London"
```

### Dashboard Troubleshooting

If the web dashboard isn't working:

1. **Check dashboard is running:**
   ```bash
   curl http://localhost:5000/api/status
   ```

2. **Test specific API endpoints:**
   ```bash
   # Test channels endpoint
   curl http://localhost:5000/api/channels
   
   # Test logs endpoint
   curl http://localhost:5000/api/logs/bot
   
   # Test stats endpoint
   curl http://localhost:5000/api/stats
   ```

3. **Check for firewall issues:**
   ```bash
   # Verify port 5000 is listening
   netstat -tlnp | grep 5000
   
   # Or use ss
   ss -tlnp | grep 5000
   ```

4. **View dashboard logs:**
   ```bash
   journalctl -u mcwb-dashboard.service -n 50
   ```

### Get Help

If you're still experiencing issues:

1. **Enable debug mode** and collect logs:
   ```bash
   python3 weather_bot.py --debug > bot_output.log 2>&1
   ```

2. **Check existing documentation:**
   - [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - General troubleshooting
   - [CHANNEL_TROUBLESHOOTING.md](CHANNEL_TROUBLESHOOTING.md) - Channel-specific issues
   - [FAQ.md](../FAQ.md) - Frequently asked questions

3. **Report an issue:**
   - Include your configuration (with sensitive info removed)
   - Attach relevant log excerpts
   - Describe what you expected vs. what happened
   - Mention any recent changes to your setup

---

## Best Practices

### Configuration Tips

1. **Start Simple:**
   ```bash
   # Run with zero configuration first
   python3 weather_bot.py
   # The bot auto-detects everything and works on all channels
   ```

2. **Add Configuration as Needed:**
   ```bash
   # Only add flags if you need specific behavior
   python3 weather_bot.py --channel-idx 1  # If you only want channel 1
   python3 weather_bot.py --weather-channel-idx 1  # If announcements should go to channel 1
   ```

3. **Use Debug Mode During Setup:**
   ```bash
   python3 weather_bot.py --debug
   # Watch for validation messages and errors
   ```

4. **Verify Configuration:**
   ```bash
   # Check logs for validation messages
   grep "Validated" logs/weather_bot.log
   ```

### Monitoring Tips

1. **Set up log rotation** to prevent disk space issues
2. **Monitor dashboard regularly** for errors and statistics
3. **Check logs periodically** for warnings
4. **Test after configuration changes** before deploying to production

### Security Tips

1. **Validate inputs** - The bot automatically validates channel indices
2. **Review logs** - Check for unusual error patterns
3. **Keep updated** - Update to the latest version for security fixes
4. **Limit access** - Use firewall rules to restrict dashboard access

---

## Summary

The MeshCore Weather Bot includes comprehensive validation and error reporting:

✅ **Channel validation** at startup prevents configuration errors
✅ **Informative error messages** help diagnose issues quickly
✅ **Standardized API errors** make debugging easier
✅ **Comprehensive logging** tracks all bot activity
✅ **Web dashboard** provides real-time monitoring
✅ **Troubleshooting guides** help resolve common issues

For more help, see:
- [README.md](../README.md) - Main documentation
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - General troubleshooting
- [FAQ.md](../FAQ.md) - Common questions
