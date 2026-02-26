# Weather Outlook Feature

## Overview

The weather bot automatically provides a 3-day outlook after sending the current weather! No user interaction required - you get both current conditions and the forecast in one go.

## User Experience

### Request Weather

Send a weather command on any channel:
```
wx York
```

### Bot Automatically Responds with Weather + Outlook

The bot sends two messages automatically:

**Message 1 - Current Weather:**
```
York, GB
☁️ Overcast
Temp: 11.2°C (feels 9.5°C)
Humid: 78%
Wind: 16.5 km/h at 240°
```

**Message 2 - 3-Day Outlook (sent automatically):**
```
York 3-day:
02-25: Overcast 6-13°C
02-26: Rain 8-14°C
02-27: Cloudy 5-12°C
https://mcwb.netlify.app
```

## Technical Details

### Message Size

All messages fit comfortably within MeshCore's 200 character limit:
- Weather response: ~100-120 characters
- Outlook response: ~110-130 characters (including link)

### Compact Outlook Format

The outlook uses abbreviated format to minimize message size:
- Only 3 days shown (not 7)
- Short date format: `02-25` instead of `2026-02-25`
- Abbreviated conditions: `Rain` instead of `Moderate rain`
- No precipitation or wind details (just temperature range and condition)
- Includes link to documentation at bottom

### API Usage

The outlook uses Open-Meteo's forecast API with the `daily` parameter:
```
daily=temperature_2m_max,temperature_2m_min,weather_code
forecast_days=3
```

## Example

### Complete Weather Request
```
User: wx London
Bot:  London, GB
      ⛅ Partly cloudy
      Temp: 14.2°C (feels 12.8°C)
      Humid: 72%
      Wind: 18 km/h at 230°


Bot:  London 3-day:
      02-25: Cloudy 8-15°C
      02-26: Rain 9-16°C
      02-27: Overcast 7-14°C
      https://mcwb.netlify.app
```

## Implementation Notes

- The feature is fully automatic - no user prompts or interaction needed
- Outlook is sent immediately after weather response with a 0.5s delay
- Each weather request automatically includes outlook
- Multiple users can request weather simultaneously without conflicts
- Link to documentation website included at bottom of every outlook

## Testing

Tests updated:
- `tests/test_weather_outlook.py` - Unit tests for automatic outlook sending
- `tests/test_outlook_integration.py` - Integration tests showing complete flow

All tests pass with the new automatic behavior.

