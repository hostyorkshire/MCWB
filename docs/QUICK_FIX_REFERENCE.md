# Quick Reference: Low SNR Fix

## What Was Fixed

The bot now responds to weather requests **regardless of signal strength**.

Previously, messages with weak signals (low SNR values 0-7) were not processed correctly, causing:
- Garbled message text
- No weather responses
- User confusion

## How It Works Now

The bot correctly handles:
- ✅ **Strong signals** (SNR 20-60) - Always worked
- ✅ **Weak signals** (SNR 0-19) - **NOW FIXED**
- ✅ **OLD format** messages - Still supported
- ✅ **V3 format** messages - All SNR values

## For Users

No changes needed! Just use the bot as normal:
```
WX London
weather Leeds  
WX your location
```

The bot will respond even if you have:
- Weak radio signal
- Low SNR readings
- Noisy RF environment
- Distant nodes

## Technical Details

See `FIX_SUMMARY_LOW_SNR.md` for complete technical documentation.

## Testing

If you want to verify the fix, look for these log patterns:

**Before fix (broken):**
```
[06:03:24] channel_idx=0 channel: yqTk3bȧcMC  # Garbled
# No response
```

**After fix (working):**
```
[06:10:32] channel_idx=0 channel: WX Leeds   # Clean
WX request for 'Leeds' from channel
Response: Leeds, GB
Clear sky
Temp: 12°C (feels 11°C)
...
```

## Support

If you still experience issues:
1. Enable debug mode: `python3 weather_bot.py -d`
2. Check the logs for message reception
3. Verify the bot sees "WX" or "weather" in the message
4. Report any issues with full debug logs
