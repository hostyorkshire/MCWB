# Fix Summary: Garbled Message Logging from Non-#wxtest Channels

## Problem Statement
When running the weather bot with debug mode (`-d` flag), messages from channels other than #wxtest were displaying garbled/encrypted content that corrupted the terminal output:

```
[07:21:43] channel_idx=0 message without SenderName: prefix, using sender='channel'
gF:D%?;ȧcMCchannel_idx=0 channel: |y
```

## Root Cause Analysis
The issue had multiple contributing factors:

1. **Insufficient UTF-8 Validation**: The `_is_valid_message_bytes` method was counting individual bytes in UTF-8 ranges (0x80-0xF4) as "valid" without checking if they formed valid UTF-8 sequences. Encrypted data with random bytes could pass this check.

2. **No Control Character Filtering**: Garbled messages containing terminal control characters (carriage returns, escape codes, etc.) were logged directly, causing terminal corruption.

3. **V3 Format False Positives**: The V3 format detection heuristic would incorrectly parse old format messages with zero timestamps as V3 format, leading to incorrect text extraction.

## Solution

### 1. Improved UTF-8 Validation (`_is_valid_message_bytes`)
**Changes**:
- Use strict UTF-8 decoding (`errors='strict'`) to reject invalid UTF-8 sequences
- Check decoded string for control character ratio (reject if > 10% control chars)
- Verify printable character ratio (must be >= 70%)
- Check Unicode character codes, not raw bytes

**Benefits**:
- Rejects messages with NULL bytes, invalid UTF-8 sequences
- Catches encrypted/garbled data that happens to have valid-looking bytes
- More accurate detection based on character-level analysis

### 2. Log Sanitization (`_sanitize_for_log`)
**Changes**:
- Added new method to sanitize text before logging
- Removes control characters (except newline, tab, carriage return)
- Converts control chars to hex notation (e.g., `\x1b` for ESC)
- Limits log length to 200 characters to prevent spam

**Benefits**:
- Prevents terminal corruption from control characters
- Makes garbled content visible in hex form for debugging
- Reduces log spam from long encrypted messages

### 3. Fixed V3 Format Detection
**Changes**:
- Added SNR > 0 check to Heuristic 3 for V3 format detection
- Prevents false positives with zero timestamps in old format messages

**Benefits**:
- More accurate format detection
- Fixes test failures with synthetic payloads

## Files Modified

### weather_bot.py
- `_is_valid_message_bytes()`: Improved validation logic
- `_sanitize_for_log()`: New method for log sanitization
- `_handle_channel_message()`: Apply sanitization to logged content
- `_parse_channel_message()`: Fixed V3 format detection

### meshcore.py
- `_is_valid_message_bytes()`: Improved validation logic (same as weather_bot.py)
- `_sanitize_for_log()`: New method for log sanitization
- `_dispatch_channel_message()`: Apply sanitization to logged content
- `_parse_channel_message()`: Fixed V3 format detection

### Tests Updated/Added
- `test_encrypted_detection.py`: Updated test expectations for stricter validation
- `test_invalid_channel_idx.py`: Fixed to use realistic timestamps
- `test_garbled_channel_messages.py`: New comprehensive test for the fix

## Testing Results

### Before Fix
- Garbled messages were logged with corrupted terminal output
- Terminal control characters caused formatting issues
- Debug logs showed meaningless encrypted text

### After Fix
- Encrypted/garbled messages are silently filtered (no log output)
- Valid messages are logged with sanitized content
- Terminal remains stable with clean debug output
- All existing tests pass

### Test Coverage
✅ `test_garbled_channel_messages.py` - Verifies fix for the reported issue
✅ `test_encrypted_detection.py` - Validates encrypted message filtering
✅ `test_invalid_channel_idx.py` - Checks channel index validation
✅ `test_weather_bot.py` - Ensures no regression in core functionality
✅ `test_channel_functionality.py` - Validates channel handling

## Code Quality

### Code Review
✅ Passed - Addressed all review feedback:
- Extracted `_MAX_LOG_LENGTH` constant
- Clarified Unicode threshold comment
- Cleaned up redundant code

### Security Scan
✅ Passed - No security vulnerabilities detected by CodeQL

## Migration Notes
- **No breaking changes** - This is a bug fix that improves logging behavior
- **No configuration changes required** - Works with existing bot setup
- **Debug mode behavior change**: Encrypted/garbled messages are now silently filtered instead of being logged

## Recommendations

### For Users
1. Continue using the bot as before - no action required
2. Debug mode (`-d`) will now show cleaner output
3. Valid messages from all channels will continue to work

### For Developers
1. The improved validation is more accurate but slightly more strict
2. Test payloads should use realistic timestamps to avoid V3 format confusion
3. Control characters in test messages will be sanitized in logs

## Example: Before vs After

### Before (Problematic)
```
[07:21:43] RX code=0x88 len=40
[07:21:43] channel_idx=0 message without SenderName: prefix, using sender='channel'
gF:D%?;ȧcMCchannel_idx=0 channel: |y
[07:21:43] TX: 0a
```

### After (Fixed)
```
[07:21:43] RX code=0x88 len=40
[07:21:43] TX: 0a
```
(Garbled message is silently filtered - no log output)

## Conclusion
The fix successfully resolves the terminal corruption issue caused by garbled/encrypted messages from non-#wxtest channels. The improved validation and log sanitization provide a more robust and user-friendly debug experience while maintaining full functionality for valid messages.
