# Weather Bot Quick Reference

## What to Look For in Logs

### ✅ Good Signs (Message Being Processed)

```
[2026-02-21 05:25:30] MeshCore [WX_BOT]: Binary frame: CHANNEL_MSG_V3 on channel_idx 2
[2026-02-21 05:25:30] MeshCore [WX_BOT]: LoRa RX channel msg from USER1 on channel_idx 2: wx London
[2026-02-21 05:25:30] MeshCore [WX_BOT]: Channel filter check: default=False, matching=False, unnamed=True → will_process=True
[2026-02-21 05:25:30] WeatherBot: Processing message from USER1: wx London
[2026-02-21 05:25:30] WeatherBot: Weather request for location: London
[2026-02-21 05:25:30] WeatherBot: Replying on channel_idx 2: Weather for London...
```

### ⚠️ Waiting for Messages

```
[2026-02-21 05:25:12] MeshCore [WX_BOT]: MeshCore: message queue empty
[2026-02-21 05:25:13] MeshCore [WX_BOT]: MeshCore: message queue empty
```
**Diagnosis**: No one has sent a message yet. This is normal when waiting.

### ℹ️ Message Received But Not Weather Command

```
[2026-02-21 05:25:30] MeshCore [WX_BOT]: LoRa RX channel msg from USER1: hello
[2026-02-21 05:25:30] WeatherBot: Processing message from USER1: hello
[2026-02-21 05:25:30] WeatherBot: Not a weather command: hello
```
**Diagnosis**: Message received but doesn't match "wx [location]" format.

## Quick Commands

### Start Bot (Debug Mode)
```bash
python3 weather_bot.py -n WX_BOT --port /dev/ttyUSB1 --baud 115200 --channel weather -d
```

### Test Without Radio
```bash
python3 weather_bot.py -i -d
# Then type: wx London
```

### One-Shot Weather Check
```bash
python3 weather_bot.py -l London -d
```

### View Demo
```bash
python3 demo_improved_logging.py
```

## Troubleshooting Steps

1. **Check if bot started**: Look for "MeshCore started" in logs
2. **Check if messages arrive**: Look for "Binary frame: CHANNEL_MSG"
3. **Check if processed**: Look for "Processing message from"
4. **Check command format**: Must be "wx [location]" or "weather [location]"
5. **See full guide**: Read TROUBLESHOOTING.md

## Command Format

### ✅ Valid Commands
- `wx London`
- `wx Manchester`  
- `weather London`
- `WX LONDON` (case insensitive)

### ❌ Invalid Commands
- `weather` (no location)
- `wxLondon` (no space)
- `what's the weather` (wrong format)

## Channel Behavior

Bot with `--channel weather` accepts messages from:
- ✅ Default channel (channel_idx 0)
- ✅ Any channel (channel_idx 1-7)
- ✅ Named "weather" channel

Bot replies on the **same channel** it received the message on.

## Getting Help

1. Check TROUBLESHOOTING.md
2. Run demo_improved_logging.py
3. Open GitHub issue with:
   - Full debug log (run with `-d`)
   - Exact command sent
   - What you expected vs what happened

## Common Myths

❌ **Myth**: "Ignoring non-JSON LoRa data" means my commands are being ignored
✅ **Reality**: This message has been removed! It was just protocol noise.

❌ **Myth**: Bot only responds to messages on the "weather" channel
✅ **Reality**: Bot responds to messages on ANY channel when using `--channel weather`

❌ **Myth**: Bot isn't working because I see "message queue empty"
✅ **Reality**: This is normal - it means no messages are waiting. Send a command!
