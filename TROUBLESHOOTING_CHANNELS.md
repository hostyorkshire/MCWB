# Troubleshooting: Bot Not Responding to Messages

## Problem: Bot is listening but not responding to messages sent on a channel

If your weather bot is running but not responding to weather queries sent on a specific channel (like "#wxtest"), this guide will help you diagnose and fix the issue.

## Understanding How MeshCore Channels Work

### Key Concepts

1. **Channel Names are Local**: Each MeshCore device has its own mapping of channel names (like "#wxtest") to numeric channel indices (0-7).

2. **Channel Indices Vary**: The same channel name may map to different indices on different devices:
   - Device A: #wxtest → channel_idx 1
   - Device B: #wxtest → channel_idx 2
   - Device C: #wxtest → channel_idx 3

3. **Hardware Configuration Required**: The companion radio device must be configured to JOIN/SUBSCRIBE to channels using the MeshCore app or device configuration interface.

4. **Software Cannot Configure Channels**: The companion radio protocol API does NOT provide commands to subscribe to channels. This must be done through the device's own interface.

## Diagnostic Steps

### Step 1: Verify Bot is Running

Check the bot startup messages:
```
Weather Bot started. Accepts queries from ALL channels.
Send 'wx [location]' to get weather.
Example: wx London
Listening for messages...
```

If you see this, the bot software is running correctly.

### Step 2: Check for Incoming Messages in Logs

With debug mode enabled (`-d` flag), you should see incoming messages:
```
[2026-02-21 21:06:54] MeshCore [WX_BOT]: LoRa RX channel msg from USER on channel_idx X: wx London
```

**If you DON'T see this log:**
- No messages are being received from the companion radio hardware
- This indicates a hardware configuration issue, NOT a software bug

### Step 3: Verify Companion Radio Channel Configuration

The companion radio device needs to be subscribed to the appropriate channels. How to configure this depends on your setup:

#### Option A: Using MeshCore Mobile App

1. Open the MeshCore app
2. Go to Channel Settings
3. Ensure you have JOINED the "#wxtest" channel (or whatever channel you're using)
4. Note which channel index it's mapped to
5. Verify the radio is connected and active

#### Option B: Using Device Web Interface

1. Access the companion radio's web interface (if available)
2. Navigate to Channel Configuration
3. Subscribe to the desired channels
4. Save settings and restart if needed

#### Option C: Manual Device Configuration

Some devices require button presses or AT commands to configure channels. Refer to your device's documentation.

### Step 4: Verify Channel Index Consistency

The challenge: Different devices map the same channel name to different indices.

**When the bot sends an announcement on "wxtest":**
- Bot maps wxtest → channel_idx 1 (first channel it uses)
- Bot sends announcement on channel_idx 1

**When a user sends a message on "#wxtest":**
- User's device might have wxtest → channel_idx 2 or 3
- Message is transmitted on that channel_idx
- Bot's companion radio must be listening on that channel_idx to receive it

**Solution:**
- Ensure the companion radio is subscribed to ALL channels users might send from
- Or coordinate channel assignments across all devices
- Or use the default channel (channel_idx 0) which all devices monitor

### Step 5: Test with Default Channel

To rule out channel mapping issues, test with the default channel:

```bash
# Stop the bot
# Restart without any channel specification
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d

# Send a test message on the default channel (no channel specified)
# The bot should respond on channel_idx 0
```

If this works, the issue is definitely channel-related.

## Common Issues and Solutions

### Issue 1: No Messages Received At All

**Symptoms:**
- Bot shows "Listening for messages..." but no incoming message logs
- Only ACKs and "message queue empty" appear in logs

**Causes:**
- Companion radio not subscribed to any channels except default
- No other devices are actually sending messages
- Radio hardware connection issue

**Solutions:**
1. Configure the companion radio to join the wxtest channel (or other channels) using the MeshCore app/device interface
2. Verify other devices are actually sending messages
3. Check radio hardware connection and power

### Issue 2: Messages Sent But Not Reaching Bot

**Symptoms:**
- Other users report sending messages
- Bot shows no incoming messages in logs

**Causes:**
- Channel index mismatch between sender and receiver
- Companion radio not subscribed to the channel index where messages are being sent

**Solutions:**
1. Have all users check which channel_idx their "#wxtest" maps to in their device
2. Ensure companion radio is subscribed to ALL those channel indices
3. Consider using a coordinated channel configuration across all devices

### Issue 3: Bot Announcement Not Seen by Users

**Symptoms:**
- Bot sends announcement successfully (shows in logs)
- Users don't see the announcement

**Causes:**
- Bot's channel_idx 1 doesn't match users' "#wxtest" channel_idx
- Users not monitoring the channel where announcement was sent

**Solutions:**
1. Send announcements on multiple channel indices to reach all users
2. Send announcements on default channel (channel_idx 0) which all devices monitor
3. Coordinate channel assignments across all devices

## Best Practices

### For Bot Operators

1. **Run without channel filtering** (no `-c` flag) to accept queries from ALL channels:
   ```bash
   python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d
   ```

2. **Configure companion radio** to join/subscribe to commonly used channels in the MeshCore app

3. **Use default channel for announcements** to ensure they reach everyone:
   ```bash
   python3 weather_bot.py --port /dev/ttyUSB0 --announce-channel ""
   ```

4. **Enable debug logging** (`-d`) to monitor incoming messages and diagnose issues

### For Users

1. **Join the weather channel** in your MeshCore app before sending queries

2. **Note your channel index** - check which channel_idx your device assigns to "#wxtest"

3. **Try the default channel** if having issues - send queries without specifying a channel

4. **Coordinate with bot operator** - ensure your channel configuration matches

## Testing Your Configuration

### Step-by-Step Test

1. **Start bot in debug mode:**
   ```bash
   python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d
   ```

2. **Watch for startup messages** - verify bot starts successfully

3. **Send a test message** from another device: "wx London"

4. **Check bot logs** - you should see:
   ```
   [timestamp] MeshCore [WX_BOT]: LoRa RX channel msg from USER on channel_idx X: wx London
   [timestamp] WeatherBot: Processing message from USER: wx London
   [timestamp] WeatherBot: Weather request for location: London
   ```

5. **If you DON'T see these logs** - the problem is with receiving messages from the hardware

6. **Configure companion radio** - join appropriate channels in MeshCore app

7. **Test again** - repeat from step 3

## Still Having Issues?

If you've followed all these steps and still have problems:

1. **Check hardware connection:**
   - Verify serial port (`/dev/ttyUSB0`) is correct
   - Check baud rate (common: 9600, 115200)
   - Ensure radio has power and antenna

2. **Review logs carefully:**
   - Look for any error messages
   - Check if ANY messages are being received (not just weather queries)
   - Verify the binary protocol is working (see CMD messages in debug output)

3. **Test with another app:**
   - Use `meshcore_send.py` to send test messages
   - Verify the companion radio is functioning correctly

4. **Check firmware version:**
   - Ensure companion radio firmware is up to date
   - Verify compatibility with the bot's protocol version (V3)

## Understanding the Logs

### Good Startup (Working):
```
[2026-02-21 21:06:54] MeshCore [WX_BOT]: Registered handler for message type: text
[2026-02-21 21:06:54] MeshCore [WX_BOT]: LoRa connected on /dev/ttyUSB0 at 115200 baud
[2026-02-21 21:06:54] MeshCore [WX_BOT]: LoRa listener thread started
[2026-02-21 21:06:54] MeshCore [WX_BOT]: MeshCore started
```

### Message Received (Working):
```
[2026-02-21 21:07:10] MeshCore [WX_BOT]: Binary frame: CHANNEL_MSG_V3 on channel_idx 1
[2026-02-21 21:07:10] MeshCore [WX_BOT]: LoRa RX channel msg from USER on channel_idx 1: wx London
[2026-02-21 21:07:10] MeshCore [WX_BOT]: Received message from USER (channel_idx=1): wx London
[2026-02-21 21:07:10] WeatherBot: Processing message from USER: wx London
```

### No Messages Received (Problem):
```
[2026-02-21 21:06:58] MeshCore [WX_BOT]: MeshCore: message acknowledgment received
[2026-02-21 21:06:58] MeshCore [WX_BOT]: MeshCore: message queue empty
[2026-02-21 21:07:01] MeshCore [WX_BOT]: MeshCore: message acknowledgment received
[2026-02-21 21:07:01] MeshCore [WX_BOT]: MeshCore: message queue empty
```
(Only ACKs and empty queue, no actual message reception)

## Summary

The key points to remember:

1. **Channel subscriptions are configured on the hardware device, not in Python code**
2. **The companion radio must be subscribed to channels using the MeshCore app/device interface**
3. **Different devices may have different channel index mappings**
4. **The bot accepts messages from all channels when no filter is set**
5. **If no messages appear in logs, it's a hardware configuration issue, not a software bug**

For most users, the solution is: **Configure the companion radio device to join the appropriate channels using the MeshCore app.**
