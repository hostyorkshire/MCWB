# Fix Summary: Weather Bot Channel_idx Parsing Issue

## Problem Statement

When users sent weather commands (WX/weather) to the weather bot on certain channels, the bot did not respond. The debug log showed errors like:

```
[20:58:10] RX code=0x88 len=61
[20:58:10] channel_idx=51 unknown: 1$
t3FV*о[ZTnSm:νGC
[20:58:11] RX code=0x88 len=40
_M1KI.i?%] channel_idx=49 unknown: ?)N~i"YK
```

The messages appeared garbled and the bot did not respond.

## Root Cause

The MeshCore firmware was sending channel messages in V3 format (which includes SNR - Signal to Noise Ratio), but the weather bot code only supported the old format. The format structures are:

- **Old format**: `code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text`
- **V3 format**: `code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text`

The bot was reading the SNR value (at byte position 1) as the channel_idx, resulting in:
- channel_idx values of 49 and 51 (which are actually SNR values in dB)
- Text being read from wrong offset (byte 8 instead of byte 11), causing garbled output
- Weather commands not being recognized due to garbled text
- Bot not responding

## Solution

Added intelligent format detection to `weather_bot.py` that handles both old and V3 formats:

### 1. Created `_parse_channel_message()` helper method

This method automatically detects which format to use based on heuristics:

- **If payload >= 12 bytes** (minimum for V3 format):
  - Check if SNR (byte 1) is in realistic range (20-60 dB) AND channel_idx (byte 4) is valid (0-7)
    → Use V3 format (channel_idx at byte 4, text at byte 11)
  - OR check if byte 1 > 7 (impossible as channel_idx in old format) AND byte 4 is valid channel_idx
    → Use V3 format
  - Otherwise → Use old format

- **If payload < 12 bytes**:
  → Use old format (channel_idx at byte 1, text at byte 8)

### 2. Updated message handlers

Both `_PUSH_CHAN_MSG` (0x88) and `_RESP_CHANNEL_MSG` (0x08) now use the new helper method.

### 3. Added module-level constants

```python
_OLD_FORMAT_HEADER_SIZE = 8   # Old format header size
_V3_FORMAT_HEADER_SIZE = 11   # V3 format header size
_MIN_REALISTIC_SNR = 20       # Minimum typical SNR (dB)
_MAX_REALISTIC_SNR = 60       # Maximum typical SNR (dB)
```

## Testing

Created comprehensive test suites:

1. **test_v3_format_detection.py** - Tests V3 format detection with high SNR values (49, 51)
2. **test_problem_scenario.py** - Reproduces the exact issue from the problem statement
3. **test_edge_cases.py** - Tests ambiguous cases and heuristic boundaries
4. All existing tests continue to pass (backward compatibility maintained)

### Test Results

✅ V3 format messages with SNR=49 and SNR=51 correctly parsed  
✅ Old format messages still work (backward compatible)  
✅ Bot correctly extracts channel_idx (1, 2, etc.) not SNR values (49, 51)  
✅ Text properly decoded ("WX Leeds", "weather Manchester")  
✅ Bot recognizes weather commands and responds  
✅ Responses sent on correct channels  
✅ All 8 valid channel indices (0-7) tested with various SNR values  
✅ Edge cases handled correctly (ambiguous payloads)  
✅ No security vulnerabilities (CodeQL clean)  

## Files Modified

- **weather_bot.py**: Added format detection logic, constants, and helper method
- **test_v3_format_detection.py**: New test file
- **test_problem_scenario.py**: New test file  
- **test_edge_cases.py**: New test file

## Impact

- ✅ Bot now responds to weather commands on ALL channels
- ✅ Handles both old and V3 format messages
- ✅ Backward compatible with older firmware
- ✅ Robust heuristics prevent false positives
- ✅ Clean, maintainable code with proper constants

## Manual Testing Needed

The automated tests successfully validate the parsing logic, but manual testing with actual MeshCore hardware is recommended to verify:

1. Bot responds to "WX [location]" commands on different channels
2. Responses appear on the correct channel where the command was received
3. No garbled messages in the debug output
4. channel_idx values are in valid range (0-7)

## Security Summary

- No security vulnerabilities introduced
- CodeQL scan: 0 alerts
- Input validation improved with SNR range checking
- All existing security measures maintained
