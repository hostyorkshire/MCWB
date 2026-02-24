# Weather Outlook Feature

## Overview

The weather bot now supports weather outlook/forecast requests! After providing the current weather, the bot asks if you'd like to see a 3-day outlook.

## User Experience

### Step 1: Request Weather

Send a weather command on any channel:
```
wx York
```

### Step 2: Bot Responds with Current Weather + Prompt

The bot sends two messages:

**Message 1 - Current Weather:**
```
York, GB
Overcast
Temp: 11.2°C (feels 9.5°C)
Humid: 78%
Wind: 16.5 km/h at 240°
https://mcwb.netlify.app
```

**Message 2 - Outlook Prompt:**
```
Thanks for that, would you like to see the outlook? (y/n)
```

### Step 3: User Responds

**Option A: Say Yes**

Respond with: `y`, `Y`, `yes`, or `YES`

The bot sends a 3-day outlook:
```
York 3-day:
02-25: Overcast 6-13°C
02-26: Rain 8-14°C
02-27: Cloudy 5-12°C
```

**Option B: Say No (or anything else)**

Respond with: `n` or any other text

The bot does nothing and clears the pending request.

## Technical Details

### Message Size

All messages fit comfortably within MeshCore's 200 character limit:
- Weather response: ~100-120 characters
- Outlook prompt: 57 characters
- Outlook response: ~80-100 characters

### State Management

- The bot tracks pending outlook requests per (sender, channel) combination
- Requests expire after 5 minutes to prevent stale state
- State is automatically cleaned up after user responds

### Compact Outlook Format

The outlook uses abbreviated format to minimize message size:
- Only 3 days shown (not 7)
- Short date format: `02-25` instead of `2026-02-25`
- Abbreviated conditions: `Rain` instead of `Moderate rain`
- No precipitation or wind details (just temperature range and condition)

### API Usage

The outlook uses Open-Meteo's forecast API with the `daily` parameter:
```
daily=temperature_2m_max,temperature_2m_min,weather_code
forecast_days=3
```

## Examples

### Example 1: User Gets Outlook
```
User: wx London
Bot:  London, GB
      Partly cloudy
      Temp: 14.2°C (feels 12.8°C)
      Humid: 72%
      Wind: 18 km/h at 230°
      https://mcwb.netlify.app

Bot:  Thanks for that, would you like to see the outlook? (y/n)

User: y
Bot:  London 3-day:
      02-25: Cloudy 8-15°C
      02-26: Rain 9-16°C
      02-27: Overcast 7-14°C
```

### Example 2: User Declines Outlook
```
User: wx Manchester
Bot:  Manchester, GB
      Slight rain
      ...

Bot:  Thanks for that, would you like to see the outlook? (y/n)

User: n
      (Bot does nothing)
```

### Example 3: User Ignores Prompt
```
User: wx Leeds
Bot:  Leeds, GB
      ...

Bot:  Thanks for that, would you like to see the outlook? (y/n)

User: (says nothing or sends different command)
      (After 5 minutes, the pending request expires)
```

## Implementation Notes

- The feature is backward compatible - existing weather commands work exactly as before
- Each user can have a pending outlook request (tracked per sender + channel)
- Multiple users can request weather simultaneously without conflicts
- The state automatically cleans up expired requests

## Testing

New tests added:
- `tests/test_weather_outlook.py` - Unit tests for outlook feature
- `tests/test_outlook_integration.py` - Integration tests showing complete flow

All existing tests continue to pass.
