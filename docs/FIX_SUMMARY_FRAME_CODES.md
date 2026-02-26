# Fix Summary: Unhandled Frame Code Errors

## Problem
When testing the weather bot on different hashtag channels, users encountered "Unhandled frame code" errors in the logs:
```
[07:38:11] Unhandled frame code 0x8a
[07:38:11] Unhandled frame code 0x90
[07:38:50] Unhandled frame code 0x80
```

## Root Cause
The weather bot was missing handlers for three MeshCore protocol frame codes:
- **0x80 (PUSH_BASE)**: Base push notification frame that may occur on some firmware versions
- **0x8a (PUSH_NO_MORE_MSGS)**: Push notification indicating no more messages in queue (0x80 | 0x0a)
- **0x90 (PUSH_CONTACT_MSG_V3)**: Push notification for inline contact (direct) messages with SNR info (0x80 | 0x10)

These frame codes follow the MeshCore protocol pattern where push notifications are indicated by setting bit 7 (0x80) of the response code.

## Solution
Added proper handlers for these frame codes in `weather_bot.py`:

1. **Frame code definitions added:**
   - `_RESP_CONTACT_MSG_V3 = 0x10` (base code for contact messages V3)
   - `_PUSH_BASE = 0x80` (base push notification flag)
   - `_PUSH_NO_MORE_MSGS = 0x8A` (push: no more messages)
   - `_PUSH_CONTACT_MSG_V3 = 0x90` (push: contact message V3)

2. **Handler implementations:**
   - **0x80**: Handled silently (pass) - may occur on some firmware
   - **0x8a**: Handled silently (pass) - queue empty, nothing to do
   - **0x90**: Handled with informational log message - weather bot doesn't process contact (direct) messages

## Changes Made
- Modified `weather_bot.py`:
  - Added 4 new frame code constants
  - Added 3 new handler clauses in the `_dispatch()` method
- Created `test_new_frame_codes.py`:
  - Comprehensive tests for all three new frame codes
  - Tests verify no "Unhandled frame code" errors are logged
  - Tests verify appropriate behavior for each code

## Testing
All tests pass successfully:
- ✅ `test_new_frame_codes.py` - All 4 test cases pass
- ✅ `test_frame_codes.py` - Existing tests continue to pass
- ✅ Manual verification confirms fix works as expected
- ✅ CodeQL security scan: No vulnerabilities found
- ✅ Code review: Minor documentation suggestion noted

## Impact
After this fix:
- No more "Unhandled frame code" errors in logs for codes 0x80, 0x8a, and 0x90
- Weather bot continues to function normally on all channels (wxtest, hashtag channels, etc.)
- Contact messages (0x90) are properly logged as ignored (expected behavior for a channel-focused bot)
- Push notifications are handled correctly per the MeshCore protocol specification

## Verification
To verify the fix works in your environment:
```bash
python3 test_new_frame_codes.py
python3 verify_frame_code_fix.py
```

Both scripts should complete successfully without any "Unhandled frame code" errors.
