# Channel Expiration and Timestamp Display - Implementation Summary

## Overview
Implemented automatic channel expiration (72-hour TTL) and timestamp display to show when each channel was last used on the dashboard.

## Problem
Previously, channels persisted indefinitely once used, leading to:
- Stale channels appearing as "active" even if unused for days/weeks
- Misleading dashboard showing channels that are no longer in use
- No way to know when a channel was last active

## Solution

### 1. Channel Expiration (72 hours)
**Changed in `meshcore.py`:**
- `_active_channels` changed from `set()` to `dict()` storing timestamps
- Added `_cleanup_expired_channels()` method to remove channels older than 72 hours
- Cleanup automatically runs before `get_active_channels()` and `save_active_channels()`
- Timestamps update each time a channel is used (send or receive)

**Format:**
```python
# Before
self._active_channels = set()  # {1, 2, 3}

# After
self._active_channels = {}  # {1: 1772051604.0, 2: 1772051605.0}
```

### 2. Timestamp Display on Dashboard
**Changed in `web_dashboard.py`:**
- API endpoint `/api/channels` now returns channel objects with timestamps
- Format: `{"name": "#weather", "last_used": "2026-02-25 20:33:24", "last_used_timestamp": 1772051604.0}`

**Changed in `templates/index.html`:**
- Updated `loadChannels()` function to display timestamps below channel names
- Shows "Last used: YYYY-MM-DD HH:MM:SS" in smaller text

**Changed in `website/js/dashboard.js` and `website/index.html`:**
- Updated to handle new channel object format
- Backward compatible with old string format

### 3. channels.json Format
```json
{
  "channels": [
    {
      "channel_idx": 1,
      "channel_name": "weather",
      "last_used": 1772051604.17659
    }
  ],
  "last_updated": "2026-02-25T20:33:24.377670"
}
```

## Dashboard Display

### Before
```
📡 Active Channels
  📡 #public
  📡 #weather
  📡 #alerts
```

### After
```
📡 Active Channels
  📡 #public
     Last used: 2026-02-25 20:33:24
  📡 #weather
     Last used: 2026-02-25 20:33:24
  📡 #alerts
     Last used: 2026-02-25 20:33:24
```

## Behavior

### Fresh Channels
- Channels used within the last 72 hours display normally
- Timestamp shows exact date/time of last use
- Timestamp updates each time the channel is used

### Expired Channels
- Channels not used for >72 hours are automatically removed
- Removal happens silently during `get_active_channels()` call
- Optional debug logging when channels expire

### Backward Compatibility
- Old channels.json files without timestamps work (treated as fresh)
- Static website handles both old (string) and new (object) formats
- No breaking changes to existing API consumers

## Testing

### New Tests (`test_channel_expiration.py`)
1. ✅ Fresh channels are not expired
2. ✅ Expired channels are removed after 72 hours
3. ✅ 72-hour threshold works precisely
4. ✅ channels.json includes timestamps
5. ✅ Multiple uses update timestamp
6. ✅ Cleanup on get and save operations

### Existing Tests
- ✅ All existing channel tests still pass
- ✅ Error logging tests pass
- ✅ Dashboard display tests pass

## Configuration
The expiration time is configurable via `_channel_expiry_hours`:
```python
self._channel_expiry_hours = 72  # Default: 72 hours
```

To change it, modify this value in `meshcore.py` `__init__()` method.

## Files Changed
1. `meshcore.py` - Core expiration logic
2. `web_dashboard.py` - API endpoint updates
3. `templates/index.html` - Dashboard UI updates
4. `website/js/dashboard.js` - Static site JS updates
5. `website/index.html` - Static site HTML updates
6. `tests/test_channel_expiration.py` - New comprehensive tests

## Impact
- **Improved accuracy**: Dashboard only shows recently active channels
- **Better visibility**: Users can see when each channel was last used
- **Automatic cleanup**: No manual intervention needed
- **No breaking changes**: Fully backward compatible
