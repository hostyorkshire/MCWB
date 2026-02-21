# Fix Summary: Bot Not Responding to Messages

## Problem Statement
The weather bot was not sending back responses when users sent "wx leeds" or other weather commands on the wxtest channel.

## Root Cause Analysis

### Symptom
From the logs, the bot was:
- ✅ Successfully sending announcements
- ✅ Receiving message acknowledgments (ACKs)
- ❌ **NOT receiving or processing actual user messages**

No logs showed:
- "Binary frame: CHANNEL_MSG..."
- "LoRa RX channel msg from..."
- "Processing message from..."

### The Bug
An **off-by-one error** in the V3 message frame parsing code at line 679 of `meshcore.py`:

```python
# BUGGY CODE (before fix)
text = payload[12:].decode("utf-8", "ignore")
```

This caused the first character of every incoming message to be **cut off**.

### Why This Broke Message Recognition

When a user sent:
```
wx leeds
```

The bot received:
```
x leeds
```

The weather bot's command parser uses this regex:
```python
pattern = r'^(?:wx|weather)\s+(.+)$'
```

Since "x leeds" doesn't start with "wx" or "weather", it failed to match and the bot ignored the message.

## The Fix

Changed line 679 in `meshcore.py`:
```python
# FIXED CODE (after fix)
text = payload[11:].decode("utf-8", "ignore")
```

### Technical Explanation

The V3 message frame format is:
```
SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
```

Byte-by-byte breakdown:
- `payload[0]`: frame code (0x11 = RESP_CHANNEL_MSG_V3)
- `payload[1]`: SNR value
- `payload[2-3]`: reserved (2 bytes)
- `payload[4]`: channel_idx
- `payload[5]`: path_len
- `payload[6]`: txt_type
- `payload[7-10]`: timestamp (4 bytes)
- `payload[11+]`: **text starts HERE**

The original code incorrectly started reading text at position 12 instead of 11, skipping the first character.

### Why Only V3 Was Affected

The bot requests V3 format during initialization (line 436 in meshcore.py):
```python
self._send_command(b"\x01\x03      MCWB")
#                       ^^^
#                       app_ver = 0x03 (requests V3 format with SNR field)
```

The non-V3 format (RESP_CHANNEL_MSG, 0x08) was correctly parsed at line 666:
```python
text = payload[8:].decode("utf-8", "ignore")  # Correct!
```

## Testing

### Test Cases Created

1. **test_message_reception.py**
   - Verifies both V3 and non-V3 message reception
   - Confirms handlers are triggered correctly

2. **test_wx_leeds_fix.py**
   - Specifically tests the "wx leeds" use case
   - Demonstrates before/after behavior
   - Verifies complete weather request flow

### Results
✅ All existing tests pass
✅ New tests pass
✅ "wx leeds" command now recognized correctly
✅ Bot responds with weather data

## Impact

### Before Fix
- ❌ Commands like "wx leeds" were ignored
- ❌ Any command starting with 'w' would fail
- ❌ Users would see no response from the bot

### After Fix
- ✅ All weather commands work correctly
- ✅ "wx leeds", "wx London", "weather Sheffield" all work
- ✅ Bot responds with weather data on the correct channel

## Files Changed

1. **meshcore.py** (line 679)
   - Changed `payload[12:]` to `payload[11:]`
   - 1 line changed

## Verification Commands

To verify the fix works:

```bash
# Run the specific test for this bug
python3 test_wx_leeds_fix.py

# Run all message reception tests
python3 test_message_reception.py

# Run full weather bot test suite
python3 test_weather_bot.py
```

## Security Summary

✅ No security vulnerabilities introduced
✅ CodeQL analysis: 0 alerts
✅ Code review: No issues found

The fix is a simple correction of an indexing error and does not introduce any new code paths or security concerns.

## Deployment Notes

This is a critical bug fix that should be deployed immediately. The fix:
- ✅ Is minimal (1 line change)
- ✅ Has no breaking changes
- ✅ Fixes a complete loss of functionality
- ✅ Is thoroughly tested

## Related Issues

This bug would have affected:
- All weather command requests
- Any V3 format channel message
- Messages from users on any channel the bot monitors

The bug only appeared when:
- Using MeshCore companion radio hardware
- With V3 message format enabled (default for this bot)
- Receiving channel messages (not contact/DM messages)
