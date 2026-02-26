# Demonstration: Encrypted Message Logging Fix

## Problem Statement

The bot was logging encrypted/garbled messages from other users, creating confusing log entries:

```
[21:53:23] channel_idx=6 unknown: يfa+E⯻ڳ@b]r⻭3NjJAC
[21:53:27] channel_idx=0 unknown: `^k$Y_J$Xj6f
[21:53:30] channel_idx=1 unknown: P`^k$Y_J$Xj6f
[21:53:32] channel_idx=1 unknown: /OT&tE%3GۺDl]7,lQ�T...
[21:53:35] channel_idx=6 unknown: %QKP`^k$Y_J$Xj6f
```

## Root Cause

MeshCore prepends "SenderName: " to all properly formatted channel messages. Encrypted messages from other users or binary data don't follow this format, so they don't contain the ": " separator.

The bot was treating all messages without the "SenderName: " format as having `sender="unknown"` and logging them with their garbled content.

## Solution

Modified `_handle_channel_message()` to:
1. Check if message has "SenderName: " format (contains ": ")
2. If not, skip the message with a debug log entry
3. Only log properly formatted messages

## Code Changes

### weather_bot.py (lines 286-296)

**Before:**
```python
# MeshCore prepends "SenderName: " to channel messages
colon = text.find(": ")
if colon > 0:
    sender = text[:colon]
    content = text[colon + 2:]
else:
    sender = "unknown"
    content = text

self._log(f"channel_idx={channel_idx} {sender}: {content}")
```

**After:**
```python
# MeshCore prepends "SenderName: " to channel messages
colon = text.find(": ")
if colon > 0:
    sender = text[:colon]
    content = text[colon + 2:]
else:
    # Messages without "SenderName: " format (colon + space) are likely encrypted
    # messages from other users. Skip them to avoid confusing logs.
    # This debug log only appears when debug mode is enabled.
    self._log(f"channel_idx={channel_idx} skipping message without SenderName: format")
    return

self._log(f"channel_idx={channel_idx} {sender}: {content}")
```

## Behavior Comparison

### Before Fix (Confusing Logs)

```
MCWB$ python3 weather_bot.py -d
[21:53:23] channel_idx=6 unknown: يfa+E⯻ڳ@b]r⻭3NjJAC
[21:53:27] channel_idx=0 unknown: `^k$Y_J$Xj6f
[21:53:27] channel_idx=0 M3UXC/M: WX Leeds
[21:53:30] channel_idx=1 unknown: P`^k$Y_J$Xj6f
```

### After Fix (Clean Logs)

```
MCWB$ python3 weather_bot.py -d
[21:53:23] channel_idx=6 skipping message without SenderName: format
[21:53:27] channel_idx=0 skipping message without SenderName: format
[21:53:27] channel_idx=0 M3UXC/M: WX Leeds
[21:53:30] channel_idx=1 skipping message without SenderName: format
```

### Without Debug Mode (Production)

```
MCWB$ python3 weather_bot.py
MCWB running. Send 'WX [location]' or 'weather [location]' on any channel.
Press Ctrl+C to stop.

WX request for 'Leeds' from M3UXC/M
Response:
Leeds, GB
☁️ Overcast
Temp: 9.8°C (feels 6.1°C)
Humid: 85%
Wind: 20.7 km/h at 239°
```

No confusing "unknown:" messages appear at all!

## Testing

### test_encrypted_message_logging.py

Created comprehensive test that verifies:
1. ✅ Encrypted messages (without "SenderName: ") are skipped
2. ✅ No "unknown:" entries appear in logs
3. ✅ Valid messages (with "SenderName: ") are logged normally
4. ✅ Debug mode shows skipped messages for troubleshooting
5. ✅ Production mode (no debug) shows no encrypted messages

### Results

```bash
$ python3 test_encrypted_message_logging.py
================================================================================
TEST: Encrypted Message Logging
================================================================================

================================================================================
RESULTS:
================================================================================
✓ Skipped encrypted message (debug log): [21:59:28] channel_idx=6 skipping message without SenderName: format
✓ Skipped encrypted message (debug log): [21:59:28] channel_idx=0 skipping message without SenderName: format
✓ Valid message logged: [21:59:28] channel_idx=0 M3UXC/M: WX Leeds
✓ Valid message logged: [21:59:28] channel_idx=1 Alice: Hello everyone

Skipped messages (with debug log): 2 (should be 2)
Messages with 'unknown:' logged: 0 (should be 0)
Valid messages logged: 2 (should be 2)

✅ Fix verified: Encrypted messages are skipped with debug log
================================================================================

✅ TEST PASSED!
```

### All Existing Tests Pass

- ✅ `test_weather_bot.py` - Core functionality intact
- ✅ `test_problem_scenario.py` - V3 format still works
- ✅ `test_invalid_channel_idx.py` - Channel validation intact
- ✅ `test_v3_format_detection.py` - Format detection still works
- ✅ `test_edge_cases.py` - Edge cases handled correctly

## Benefits

1. **Cleaner Logs**: No more confusing "unknown:" entries with garbled text
2. **Better UX**: Users see only meaningful messages
3. **Debug Support**: When needed, debug mode shows skipped messages
4. **Backward Compatible**: All valid messages continue to work
5. **Minimal Change**: Only 3 lines changed
6. **Well Tested**: New test + all existing tests pass

## Security

- ✅ CodeQL scan: No vulnerabilities detected
- ✅ No sensitive data logged
- ✅ Encrypted messages are properly ignored
- ✅ No impact on message security

## Impact

**Before**: Confusing logs with garbled text from encrypted messages  
**After**: Clean logs showing only valid, decodable messages  
**Result**: Better user experience and easier troubleshooting
