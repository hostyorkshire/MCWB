# Manual Test: Weather Bot Channel Reply Fix

## Test Scenario 1: Bot with --channel weather
```bash
python3 weather_bot.py -n WX_BOT --channel weather -d
```

**Expected Behavior:**
- Bot receives message on channel_idx 0
- Bot replies on 'weather' channel (NOT channel_idx 0)
- Users monitoring 'weather' channel see the reply

**Test Command:**
Simulate a message from USER1 on channel_idx 0: "Wx barnsley"

**Expected Log Output:**
```
[...] WeatherBot: Replying on channel 'weather': Weather for Barnsley...
[...] MeshCore: Sending message on channel 'weather': {...}
[Broadcast on channels: 'weather']
```

## Test Scenario 2: Bot with --channel alerts
```bash
python3 weather_bot.py -n WX_BOT --channel alerts -d
```

**Expected Behavior:**
- Bot receives message on channel_idx 0
- Bot replies on 'alerts' channel (NOT channel_idx 0)
- Users monitoring 'alerts' channel see the reply

**Test Command:**
Simulate a message from USER1 on channel_idx 0: "Wx Birmingham"

**Expected Log Output:**
```
[...] WeatherBot: Replying on channel 'alerts': Weather for Birmingham...
[...] MeshCore: Sending message on channel 'alerts': {...}
[Broadcast on channels: 'alerts']
```

## Test Scenario 3: Bot without --channel (backward compatibility)
```bash
python3 weather_bot.py -n WX_BOT -d
```

**Expected Behavior:**
- Bot receives message on channel_idx 0
- Bot replies on channel_idx 0 (where message came from)
- Standard behavior for unconfigured bot

**Test Command:**
Simulate a message from USER1 on channel_idx 0: "Wx Leeds"

**Expected Log Output:**
```
[...] WeatherBot: Replying on default channel (channel_idx 0): Weather for Leeds...
[...] MeshCore: Sending message (idx=0): {...}
[Reply on channel_idx: 0 (default)]
```

## Verification
All three scenarios have been tested and verified through automated tests.
The fix ensures that bots configured with --channel always reply on the configured channel.
