# FAQ: Why Does the Bot Only Work on Some Channels?

## Question
"My weather bot only works on the #wxtest channel (channel_idx=0), but not on other channels. Why?"

## Short Answer
The bot **does work on all channels** - it's just that some channels are **encrypted** or **not subscribed to by your bot's radio**. When you enable debug mode (`-d`), you'll see helpful diagnostic messages explaining why messages from certain channels are being ignored.

## Understanding the Issue

### What You See in the Logs

**Working channel (channel_idx=0):**
```
[06:17:35] channel_idx=0 M3UXC: Wx barnsley 
WX request for 'barnsley' from M3UXC
Response:
Barnsley, GB
Clear sky
```

**Non-working channel (channel_idx=1):**
```
[06:17:36] channel_idx=1 channel: Mj#s*;(�%WPWD
[06:17:36] Invalid channel_idx=129 (valid range: 0-7) - message is likely encrypted or corrupted
[06:17:36] If this channel should work, check: 1) Channel is not encrypted, 2) Bot's radio is subscribed to this channel
```

### What's Happening

The garbled text `Mj#s*;(�%WPWD` indicates that channel_idx=1 is **encrypted**. When the bot tries to parse the message, it sees an invalid channel index (> 7), which is a signature of encrypted or corrupted data.

## Common Scenarios

### Scenario 1: Encrypted Channels

**Symptom:** Messages on certain channels appear as garbled text in debug logs.

**Cause:** Those channels are configured with encryption in the MeshCore app.

**Solution:**
1. **Option A**: Disable encryption on that channel in the MeshCore app (if appropriate)
2. **Option B**: Use only unencrypted channels for the bot (like #wxtest)
3. **Option C**: Configure your bot's companion radio with the encryption key (requires radio firmware support)

### Scenario 2: Unsubscribed Channels

**Symptom:** No messages appear from certain channels at all (not even garbled ones).

**Cause:** Your bot's companion radio is not subscribed to those channels.

**Solution:** In the MeshCore app, subscribe your bot's radio to the channels you want it to monitor.

### Scenario 3: Channel Index Mismatch

**Symptom:** Bot announcements are sent but users don't see them, or vice versa.

**Cause:** Different devices map the same channel name (e.g., "#wxtest") to different indices.

**Solution:** 
- The bot automatically replies on the same channel_idx where queries come from
- For bot-initiated announcements, use `--weather-channel-idx` to specify the correct index
- Or coordinate channel assignments across all devices

## Bot's Default Behavior

**Important:** When you run the bot without any channel configuration:

```bash
python3 weather_bot.py -d
```

The bot:
- ✅ Listens to **ALL channel indices** (0-7)
- ✅ Replies on the **SAME channel_idx** where each query came from
- ✅ Automatically works with any channel configuration

## Troubleshooting Steps

### Step 1: Enable Debug Mode

Always run with `-d` flag to see diagnostic messages:

```bash
python3 weather_bot.py -d
```

### Step 2: Check the Logs

Look for these diagnostic messages:

```
[06:17:36] Invalid channel_idx=129 (valid range: 0-7) - message is likely encrypted or corrupted
[06:17:36] If this channel should work, check: 1) Channel is not encrypted, 2) Bot's radio is subscribed to this channel
```

This tells you:
- The message was received
- But it couldn't be parsed because it's encrypted or corrupted

### Step 3: Verify Channel Configuration

**In the MeshCore app:**

1. Open Channel Settings
2. Check which channels your bot's radio is subscribed to
3. Note which channels have encryption enabled
4. For the bot to work, channels must be:
   - ✅ Subscribed (bot's radio is a member)
   - ✅ Unencrypted (or bot has the encryption key)

### Step 4: Test with a Known-Good Channel

If you have a channel that works (like #wxtest):

1. Verify it's unencrypted
2. Note its channel_idx (e.g., 0)
3. Send "wx London" on that channel
4. Confirm the bot responds

## Why #wxtest Works

Your #wxtest channel works because:
1. ✅ It's configured as channel_idx=0
2. ✅ It's unencrypted
3. ✅ Your bot's radio is subscribed to it

Other channels don't work because one or more of these conditions aren't met.

## Solution Summary

To make the bot work on more channels:

### For Operators

```bash
# Run with debug mode to see diagnostic messages
python3 weather_bot.py -d
```

**In MeshCore app:**
1. Ensure bot's radio is subscribed to desired channels
2. Use unencrypted channels for the bot
3. Or configure bot with encryption keys (if supported)

### For Users

Send weather queries on channels that are:
- Subscribed to by the bot's radio
- Unencrypted (or bot has the key)
- Properly configured in the MeshCore app

## Technical Details

### How Encryption Detection Works

The bot detects encrypted messages by checking the parsed channel_idx:

```python
# Valid channel_idx range: 0-7
if not (0 <= channel_idx <= 7):
    # Invalid = likely encrypted or corrupted
    log("Message is likely encrypted or corrupted")
    return (None, None)
```

When a message is encrypted, the bytes don't correspond to valid protocol values, resulting in channel indices like 129, 42, etc. (way outside the valid 0-7 range).

### Message Parsing Flow

```
1. Receive binary frame from radio
2. Extract message payload
3. Try to parse as V3 format (with SNR)
4. Fall back to old format
5. Validate channel_idx (0-7)
   ├─ Valid: Process the message
   └─ Invalid: Log diagnostic, reject message
```

## Conclusion

**The bot is NOT limited to channel_idx=0.** It works on any channel that is:
- Unencrypted
- Subscribed to by the bot's companion radio
- Configured in the MeshCore app

When you see "only works on #wxtest," it means #wxtest meets these requirements while other channels don't. Enable debug mode (`-d`) to see specific diagnostic messages explaining why each channel works or doesn't work.
