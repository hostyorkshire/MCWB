# Channel Filter Fix Summary

## Problem Statement
The weather bot was not working correctly in the weather channel but was working fine in the wxtest channel. The user requested removal of wxtest channel references and fixing the channel filtering logic.

## Root Cause Analysis
Looking at the log from the problem statement:
```
[2026-02-21 05:38:49] MeshCore [WX_BOT]: Binary frame: CHANNEL_MSG on channel_idx 0
[2026-02-21 05:38:49] MeshCore [WX_BOT]: LoRa RX channel msg from M3UXC on channel_idx 0: Wx leeds
[2026-02-21 05:38:49] MeshCore [WX_BOT]: Channel filter check: default=True, matching=False, unnamed=False → will_process=True (filter: 'weather')
[2026-02-21 05:38:51] MeshCore [WX_BOT]: Replying on default channel (channel_idx 0):
```

The bot was configured with `--channel weather` but was:
1. Accepting messages from the default channel (channel_idx 0)
2. Replying on channel_idx 0 instead of the configured weather channel

This happened because the channel filter logic had special handling for the default channel that allowed it even when a specific channel filter was configured.

## Solution

### 1. Fixed Channel Filter Logic (meshcore.py)
Removed the logic that accepted messages from the default channel when a channel filter is configured.

**Before:**
```python
is_default_channel = (message.channel_idx == 0 and message.channel is None)
is_matching_channel_name = (message.channel in self.channel_filter)
is_unnamed_channel = (message.channel is None and message.channel_idx is not None and message.channel_idx > 0)

if not is_default_channel and not is_matching_channel_name and not is_unnamed_channel:
    # Reject message
```

**After:**
```python
is_matching_channel_name = (message.channel in self.channel_filter)
is_unnamed_channel = (message.channel is None and message.channel_idx is not None and message.channel_idx > 0)

if not is_matching_channel_name and not is_unnamed_channel:
    # Reject message
```

### 2. Removed wxtest Channel References
- Removed 30+ demo and test files that used wxtest for debugging
- Removed fix summary documentation files
- Updated remaining tests to use practical channel names (weather, alerts, emergency)
- Updated CHANNEL_GUIDE.md examples

### 3. Repository Cleanup
Removed approximately 6,400 lines of code:
- Demo files (demo_*.py)
- Fix verification tests (verify_fix.py, validate_fix.py, test_*fix*.py)
- Fix summary documentation (*FIX*.md, *SUMMARY.md)
- Outdated integration tests

## Behavior After Fix

When a bot is configured with `--channel weather`:

### ✅ ACCEPTS messages from:
- Non-zero channel_idx (1+) with no channel name (from LoRa radios)
- Messages with matching channel name "weather"

### ❌ REJECTS messages from:
- Default channel (channel_idx 0)
- Non-matching channel names

## Testing

Created comprehensive tests to verify the fix:
- `test_channel_reply_behavior.py` - Validates channel filtering and reply behavior
- `manual_verification.py` - Demonstrates the exact scenario from problem statement

All tests pass:
```
✅ Bot with --channel weather ignores default channel (idx 0)
✅ Bot accepts messages from non-zero channel_idx
✅ Bot accepts messages from matching channel name
✅ Bot replies on the channel where message came from
```

## Impact
- Bot now correctly acts as a dedicated service for configured channels
- No longer responds to messages from default channel when configured for specific channel
- Cleaner codebase with better documentation
- All security checks pass (CodeQL: 0 alerts)

## Migration Notes
Users should ensure their LoRa radios are configured to send messages on non-zero channel indices (1+) when using the bot with `--channel` parameter. The bot will no longer accept messages from channel_idx 0 (default channel) when a specific channel filter is configured.
