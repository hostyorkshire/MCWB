# Message Delivery Improvements

## Overview

This document describes improvements made to ensure reliable delivery of weather forecast messages.

## Issues Addressed

### 1. Missing Country Code in Outlook

**Problem:** When requesting weather for cities with ambiguous names (e.g., "wx york us"), the outlook message only showed the city name (e.g., "York 3-day:") without the country code. This could cause confusion about which location's forecast was being displayed.

**Solution:** The outlook message now includes the country code, matching the format of the weather response:
- Before: `York 3-day:`
- After: `York, US 3-day:` or `York, GB 3-day:`

This ensures users can clearly distinguish between forecasts for different countries.

### 2. First Message Sometimes Missed

**Problem:** The bot sends two messages for each weather request:
1. Current weather conditions
2. 3-day outlook

Sometimes the first message was not received by users, but the second message (outlook) was delivered. This is likely due to mesh network timing issues when messages are sent too quickly.

**Solutions Implemented:**

#### Increased Inter-Message Delay
- **Before:** 0.5 seconds between messages
- **After:** 2.0 seconds between messages

This gives the mesh network more time to process and transmit the first message before the second is queued.

#### Enhanced Logging
Added explicit logging for each message sent:
```
✓ First message (current weather) sent to channel_idx=1
✓ Second message (outlook) sent to channel_idx=2
```

This helps operators monitor message delivery and diagnose issues.

## Technical Details

### Message Sending Flow

```python
# Send current weather
self._send_channel_msg(response, channel_idx)
logger.info("First message (current weather) sent")

# Wait for transmission
time.sleep(2.0)  # Increased from 0.5s

# Send outlook
self._send_channel_msg(outlook_response, channel_idx)
logger.info("Second message (outlook) sent")
```

### Why Messages Can Be Lost

LoRa mesh networks have several characteristics that can affect message delivery:

1. **Radio Congestion:** Multiple nodes transmitting simultaneously
2. **Limited Bandwidth:** LoRa is designed for low data rates
3. **Message Queuing:** Companion radio has limited queue capacity
4. **Mesh Routing:** Messages may need to hop through multiple nodes

The increased delay helps reduce congestion by giving each message time to be transmitted before queuing the next.

## User Experience

### Example: Weather Request for York

**User sends:** `wx york us`

**Bot response (Message 1 - Current Weather):**
```
York, US
☁️ Overcast
Temp: 68°F (feels 65°F)
Humid: 72%
Wind: 12 mph at 180°
```

**Bot response (Message 2 - 3-Day Outlook):**
```
York, US 3-day:
02-25: Rain 55-70°F
02-26: Cloudy 58-73°F
02-27: Clear 52-68°F
https://mcwb.netlify.app
```

Note: Both messages now clearly show "York, US" so users know they're getting the forecast for York, Pennsylvania, not York, England.

### What If Messages Are Still Lost?

If you continue to experience message delivery issues despite these improvements:

1. **Check your mesh network:** Ensure good signal strength between nodes
2. **Reduce network traffic:** Avoid sending multiple requests simultaneously
3. **Monitor logs:** Check the bot logs for "First message sent" and "Second message sent" entries
4. **Try again:** Simply re-send the weather command

The bot logs all sent messages, so operators can verify that messages were transmitted even if they weren't received.

## Testing

All tests have been updated to verify:
- Country code is included in outlook messages
- Both messages are sent in correct order
- Delay between messages is appropriate

Run tests with:
```bash
python3 tests/test_weather_outlook.py
python3 tests/test_outlook_integration.py
```

## Future Improvements

Potential future enhancements could include:
- Monitoring for PUSH_SEND_CONFIRMED acknowledgments
- Retry logic if messages aren't acknowledged
- Combining weather and outlook into a single message (if message size permits)
- User-configurable delay between messages
