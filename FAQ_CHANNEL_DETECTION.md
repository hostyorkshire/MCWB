# Channel Index Detection: FAQ

## Question: Can the bot automatically detect which channel index #weather is on?

**Short Answer: No, automatic detection is not possible with the current MeshCore protocol.**

## Why Automatic Detection Doesn't Work

### What the Protocol Provides

When the bot receives a message through the MeshCore companion radio, it gets:
- **channel_idx**: A numeric value (0-7) indicating which slot the message arrived on
- **message content**: The text of the message (e.g., "SenderName: wx London")
- **timestamp**: When the message was sent

### What the Protocol Does NOT Provide

The protocol does not include:
- ❌ Channel name (e.g., "weather", "alerts", "news")
- ❌ Channel configuration information
- ❌ Mapping of channel names to indices
- ❌ Commands to query channel configuration from the radio

### Why This Matters

Each MeshCore device has its own local mapping of channel names to indices:

```
Device A:                Device B:                Device C:
#weather → index 1      #weather → index 2      #weather → index 3
#alerts  → index 2      #news    → index 1      #alerts  → index 1
#news    → index 3      #alerts  → index 3      #news    → index 2
```

**The bot cannot determine these mappings automatically** because:
1. The protocol only sends numeric indices, not names
2. There's no command to query the radio for its channel configuration
3. The mappings are device-specific and configured in the MeshCore app

## How to Find Your Weather Channel Index

### Method 1: Check Your MeshCore App

1. Open your MeshCore app (mobile or web interface)
2. Navigate to **Channel Settings** or **Channel Configuration**
3. Look for your #weather channel
4. Note the **channel number** or **slot** assigned to it (usually 0-7)
5. Use this number with `--weather-channel-idx`

Example:
```bash
# If your MeshCore app shows #weather is on slot 2
python3 weather_bot.py --weather-channel-idx 2 --announce
```

### Method 2: Use Debug Mode to Discover

If you're unsure which index corresponds to #weather, you can use debug mode to discover it:

1. **Start the bot in debug mode without any channel filter:**
   ```bash
   python3 weather_bot.py --debug
   ```

2. **Send a test message on your #weather channel** from another device:
   ```
   wx test
   ```

3. **Look at the debug output** for the channel_idx:
   ```
   [17:45:32] RX code=0x88 len=27
   [17:45:32] channel_idx=2 SomeUser: wx test
   ```
   In this example, `channel_idx=2` tells you the #weather channel is on index 2.

4. **Restart the bot with the discovered index:**
   ```bash
   python3 weather_bot.py --weather-channel-idx 2 --announce
   ```

### Method 3: Trial and Error

If methods 1 and 2 don't work, you can try different indices:

```bash
# Try index 1
python3 weather_bot.py --weather-channel-idx 1 --announce

# If that doesn't work, try index 2
python3 weather_bot.py --weather-channel-idx 2 --announce

# Continue with indices 0-7 until you find the right one
```

Send a test message on your #weather channel and see if the bot responds.

## Best Practice: Document Your Configuration

Once you've determined the correct channel index, document it for your setup:

```bash
# Create a start script
cat > start_weather_bot.sh << 'EOF'
#!/bin/bash
# Weather channel is on index 2 for this device
python3 weather_bot.py --weather-channel-idx 2 --announce --port /dev/ttyUSB0
EOF

chmod +x start_weather_bot.sh
```

## Technical Background

### The MeshCore Protocol

The companion radio binary protocol is documented at:
https://github.com/meshcore-dev/MeshCore/wiki/Companion-Radio-Protocol

**Available Commands:**
- `0x01` - CMD_APP_START: Initialize session
- `0x03` - CMD_SEND_CHAN_MSG: Send message on a channel (requires channel_idx)
- `0x05` - CMD_GET_DEVICE_TIME: Radio requests time
- `0x08` - RESP_CHANNEL_MSG: Receive message (includes channel_idx)
- `0x0A` - CMD_SYNC_NEXT_MSG: Get next queued message

**Notable Absence:**
- No command to query channel configuration
- No command to get channel name from index
- No command to get index from channel name

### Message Frame Structure

When receiving a channel message, the protocol provides:
```
Byte 0:    Code (0x08, 0x11, or 0x88)
Byte 1:    channel_idx (0-7)          ← Only numeric index, no name
Byte 2:    path_len
Byte 3:    txt_type
Bytes 4-7: timestamp
Bytes 8+:  message text
```

**The channel name is not included in the frame.**

## Why `--weather-channel-idx` is Necessary

Since automatic detection is impossible, the bot needs explicit configuration:

```bash
# Tell the bot which index to use
python3 weather_bot.py --weather-channel-idx 2
```

This ensures:
- ✅ Bot listens only on the correct channel
- ✅ Announcements are sent to the correct channel from startup
- ✅ Responses are sent to the correct channel
- ✅ Works consistently regardless of device configuration

## Future Possibilities

For automatic detection to work, the MeshCore protocol would need to be enhanced with:

1. **Channel metadata in messages**: Include channel name along with channel_idx
2. **Configuration query command**: Allow apps to query the radio's channel configuration
3. **Channel announcement**: Radio could broadcast its channel mappings on connection

Until then, manual configuration with `--weather-channel-idx` is required.

## Summary

| Question | Answer |
|----------|--------|
| Can the bot auto-detect which index #weather is on? | **No** |
| Why not? | Protocol only provides numeric indices, not names |
| What's the solution? | Use `--weather-channel-idx` to explicitly configure it |
| How do I find the right index? | Check MeshCore app, use debug mode, or trial-and-error |
| Is this a bot limitation? | No, it's a protocol limitation |
| Will this change in the future? | Only if the MeshCore protocol is enhanced |

## Related Documentation

- `README.md` - Main documentation with usage examples
- `CHANNEL_GUIDE.md` - Comprehensive guide to channels
- `TROUBLESHOOTING_CHANNELS.md` - Troubleshooting channel issues
- `SOLUTION_WEATHER_CHANNEL_CONFIG.md` - Implementation details
