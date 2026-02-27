# Announcement Broadcasting Verification

## Summary

The Weather Bot correctly broadcasts announcements on the channel where users are active.

**Note:** `#wxtest` is just an example channel name used in documentation. You can use ANY channel name you create!

## Default Configuration

- **Channel**: Adapts to first received message (or channel 0 if no messages)
- **Interval**: Every 6 hours (21,600 seconds) for periodic announcements
- **Message**: "Hello this is the WX BoT. To get a weather update simply type WX and your location."
- **Behavior**: 
  - **ALWAYS** sends announcement on startup (if --announce flag is used)
  - Repeats every 6 hours while running (periodic announcements)
  - Automatically uses the channel where users send commands
  - Timestamp tracking only applies to periodic announcements, NOT startup

## How to Start Bot

### Default (works on all channels, announcements adapt to usage):
```bash
python3 weather_bot.py --port /dev/ttyUSB1 --baud 115200 -d --announce
```

### Specify announcement channel index (advanced):
```bash
python3 weather_bot.py --port /dev/ttyUSB1 --baud 115200 -d --announce --weather-channel-idx 2
```

### Without announcements (recommended for most users):
```bash
python3 weather_bot.py --port /dev/ttyUSB1 --baud 115200 -d
```

## Verification Output

When the bot starts, you should see:
```
[2026-02-21 21:31:28] WeatherBot: Sending announcement on channel 'wxtest'
[2026-02-21 21:31:28] MeshCore [WX_BOT]: Sending message on channel 'wxtest': {...}
[2026-02-21 21:31:28] MeshCore [WX_BOT]: Mapped channel 'wxtest' to channel_idx 1
[2026-02-21 21:31:28] MeshCore [WX_BOT]: LoRa TX channel msg (idx=1): Hello this is the WX BoT...

Hello this is the WX BoT. To get a weather update simply type WX and your location.
[Announcement on channel: 'wxtest']
```

## Diagnostic Tool

Run the diagnostic tool to verify announcement functionality:
```bash
python3 diagnose_announcement.py
```

This will test:
1. Announcement constants and configuration
2. Bot creation with wxtest channel
3. Announcement sending
4. Hardware detection

## Troubleshooting

If announcements are not being received on mesh devices:

### 1. Check Device Subscription
- Ensure receiving devices are subscribed to the 'wxtest' channel
- Verify channel name matches exactly (case-sensitive)

### 2. Check Channel Mapping
- In MeshCore app, verify 'wxtest' maps to correct channel_idx
- Default mapping: 'wxtest' → channel_idx 1

### 3. Check Radio Configuration
- Verify LoRa hardware is connected and working
- Check baud rate matches (default: 115200)
- Confirm serial port is correct (e.g., /dev/ttyUSB0 or /dev/ttyUSB1)

### 4. Check Bot Logs
Enable debug mode (`-d` flag) to see detailed logs:
- Message sending confirmation
- Channel mapping
- LoRa transmission status
- Message acknowledgments

## Code Location

The announcement functionality is implemented in `weather_bot.py`:

- **Constants** (lines 109-110): ANNOUNCE_INTERVAL, ANNOUNCE_MESSAGE
- **Startup Announcement** (lines 1130-1146): ALWAYS announces on boot when --announce is set
- **Periodic Announcements** (lines 1151-1154): Respects 3-hour interval
- **Timestamp Tracking** (lines 772-793): For periodic announcements only, not startup
- **CLI Options**: --announce flag, --weather-channel-idx to specify announcement channel

## Test Results

All tests pass, including:
- ✓ `test_announcement()` - Verifies announcement configuration and sending
- ✓ Command parsing tests
- ✓ MeshCore integration tests
- ✓ Channel reply tests

## Conclusion

The announcement code is **working correctly** and **broadcasting to #wxtest** as specified. No code changes are required.
