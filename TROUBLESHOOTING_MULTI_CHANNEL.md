# Troubleshooting Multi-Channel Support

## Problem: Bot Not Responding on Some Channels

If your weather bot responds on some channels but not others, here are the most common causes and solutions.

### Quick Diagnosis

Run the bot with debug mode enabled:
```bash
python3 weather_bot.py -d
```

Watch for these messages in the log:
- `Old format: Message appears encrypted/garbled (channel_idx=X)` - Channel X is encrypted
- `Old format: Invalid channel_idx=X` - Invalid channel configuration
- `V3 format: Message appears encrypted/garbled (channel_idx=X)` - Channel X is encrypted (V3 firmware)
- `Ignoring message from channel_idx=X (filter=Y)` - Channel filtering is active

### Common Causes

#### 1. Encrypted Channels

**Symptom:** Bot works on one channel (e.g., channel 0 / wxtest) but not others.

**Cause:** Other channels in your MeshCore network are encrypted. The bot cannot decrypt encrypted messages and will silently ignore them.

**Debug log shows:**
```
[HH:MM:SS] RX code=0x88 len=40
[HH:MM:SS] Old format: Message appears encrypted/garbled (channel_idx=1)
[HH:MM:SS] TX: 0a
```

**Solution:**
- Configure your mesh network so the weather channel is **not encrypted**
- OR move the weather bot to a specific unencrypted channel
- OR configure the bot to only listen on an unencrypted channel using `--channel-idx`

**Example:**
```bash
# Only listen and respond on channel 0 (wxtest)
python3 weather_bot.py -d --channel-idx 0
```

#### 2. Channel Index Filtering

**Symptom:** Bot ignores messages from certain channels even though they're visible in the log.

**Cause:** You've configured channel filtering with `--channel-idx` option.

**Debug log shows:**
```
[HH:MM:SS] channel_idx=2 M3UXC: wx Leeds
[HH:MM:SS] Ignoring message from channel_idx=2 (filter=0)
```

**Solution:**
- Remove the `--channel-idx` option to accept messages from all channels
- OR change the `--channel-idx` value to the channel you want to monitor

**Default behavior (no filtering):**
```bash
python3 weather_bot.py -d
# Accepts messages from ALL channels
```

**With filtering:**
```bash
python3 weather_bot.py -d --channel-idx 0
# Only accepts messages from channel 0
```

#### 3. Invalid Channel Configuration

**Symptom:** Some received messages are never logged with a channel_idx.

**Cause:** Messages have invalid channel indices (> 7) or are malformed.

**Debug log shows:**
```
[HH:MM:SS] RX code=0x88 len=40
[HH:MM:SS] Old format: Invalid channel_idx=15 (valid range: 0-7)
[HH:MM:SS] TX: 0a
```

**Solution:**
- Check your MeshCore firmware version
- Verify channel configuration in your mesh network
- Report issue to MeshCore developers if problem persists

### Checking Your Channel Configuration

To understand which channels are in your mesh network:

1. **Check MeshCore app:** Look at your channel list in the mobile app
2. **Check encryption:** Each channel shows if it's encrypted or not
3. **Test each channel:** Send a test message "wx test" on each channel

### Expected Behavior

**Without filtering (default):**
- ✅ Bot accepts messages from ALL unencrypted channels (0-7)
- ✅ Bot replies on the same channel where the request came from
- ❌ Bot ignores encrypted messages (cannot decrypt)
- ❌ Bot ignores messages with invalid channel_idx (> 7)

**With channel filtering (`--channel-idx N`):**
- ✅ Bot only accepts messages from channel N
- ✅ Bot replies on channel N
- ❌ Bot ignores all other channels
- ❌ Bot still ignores encrypted messages

### Testing Multi-Channel Support

You can test if the bot accepts messages from different channels:

```bash
# Run the test
python3 test_no_channel_filtering.py
```

This test verifies that the bot accepts plaintext messages from channels 0, 1, 2, and 5.

### Recommended Setup

For best compatibility:

1. **Create a dedicated weather channel** that is **NOT encrypted**
2. **Configure it as channel 0** or note which channel index it uses
3. **Run the bot without filtering** to accept requests from any channel:
   ```bash
   python3 weather_bot.py -d
   ```

OR run the bot listening only on your weather channel:
   ```bash
   python3 weather_bot.py -d --channel-idx 0  # Replace 0 with your weather channel index
   ```

### Still Having Issues?

If you've followed the troubleshooting steps and the bot still doesn't respond:

1. **Capture the debug log** showing the problem
2. **Note which channels work and which don't**
3. **Check encryption status** of each channel in MeshCore app
4. **Share the log** with maintainers for further diagnosis

The debug log will now show exactly why each message is accepted or rejected, making it much easier to diagnose the issue.
