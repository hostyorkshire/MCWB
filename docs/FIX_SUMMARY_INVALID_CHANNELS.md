# Fix Summary: Invalid Channel Index Filtering

## Problem Statement

The weather bot was receiving encrypted/garbled messages from channels it doesn't have decryption keys for. These messages were being parsed with invalid channel indices (e.g., 49, 50) that are outside the valid range of 0-7, and the garbled text was being logged, creating confusing output:

```
[21:37:00] channel_idx=49 unknown: p j6LH
[21:37:09] channel_idx=50 unknown: Y/7*M.R·S
```

## Root Cause

In the `_parse_channel_message()` method in `weather_bot.py`, when falling back to old format parsing, the channel index was extracted from `payload[1]` without validation. For encrypted/garbled messages, this byte can be any value (0-255), resulting in invalid channel indices that would then be logged along with garbled text.

## Solution

Added validation to ensure channel indices are in the valid range (0-7):

1. **Added constant**: `_MAX_VALID_CHANNEL_IDX = 7` for better maintainability
2. **Old format validation**: Return `(None, None)` if channel_idx is outside valid range
3. **V3 format validation**: Only process messages if channel_idx is valid
4. **Improved heuristics**: Better distinguish between old format with invalid channel_idx and V3 format

## Code Changes

### weather_bot.py

1. Added `_MAX_VALID_CHANNEL_IDX = 7` constant (line 53)
2. Updated `_parse_channel_message()` to validate channel indices:
   - Old format parsing now checks `0 <= channel_idx <= _MAX_VALID_CHANNEL_IDX`
   - V3 format heuristics use the constant
3. Updated `_RESP_CHANNEL_MSG_V3` handler to validate channel_idx

## Testing

Created comprehensive test coverage:

### test_invalid_channel_idx.py
- Tests all valid channel indices (0-7) are accepted
- Tests invalid channel indices (8, 10, 49, 50, 100, 255) are rejected
- Tests V3 format with valid and invalid channel indices
- Tests simulated encrypted/garbled messages

### demo_invalid_channel_fix.py
- Demonstrates the fix with real-world scenarios from the issue log
- Shows that valid messages (channel 0) are processed correctly
- Shows that garbled messages (channels 49, 50) are blocked

## Verification

All tests pass:
- ✅ `test_invalid_channel_idx.py` - New test for this fix
- ✅ `test_v3_format_detection.py` - V3 format detection still works
- ✅ `test_edge_cases.py` - Edge cases handled correctly
- ✅ `test_weather_bot.py` - Main bot functionality intact
- ✅ CodeQL security scan - No vulnerabilities

## Impact

**Before the fix:**
```
[21:37:00] channel_idx=49 unknown: p j6LH  ← Confusing!
[21:37:09] channel_idx=50 unknown: Y/7*M  ← Confusing!
```

**After the fix:**
```
(no garbled messages in logs)  ← Clean!
```

Users will no longer see confusing garbled messages in the logs. The bot now silently filters out messages with invalid channel indices, which are typically encrypted messages from channels the bot doesn't have keys for.

## Backward Compatibility

This fix maintains full backward compatibility:
- All valid channel messages (0-7) continue to work
- Both old format and V3 format messages are supported
- No changes to the API or command-line interface

## Security

- CodeQL scan: ✅ No vulnerabilities detected
- The fix improves robustness by rejecting malformed messages
- No sensitive data is logged from invalid messages
