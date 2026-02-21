# MCWB Weather Bot Troubleshooting Guide

This guide helps you troubleshoot common issues with the MeshCore Weather Bot.

## Issue: "No messages are showing and bot is not answering back"

### Understanding the Log Output

When you run the weather bot with the `-d` (debug) flag, you'll see various log messages:

#### Normal Startup Messages
```
[2026-02-21 05:24:49] MeshCore [WX_BOT]: Mapped channel 'weather' to channel_idx 1
[2026-02-21 05:24:49] MeshCore [WX_BOT]: Channel filter set to: 'weather'
[2026-02-21 05:24:49] MeshCore [WX_BOT]: LoRa connected on /dev/ttyUSB1 at 115200 baud
[2026-02-21 05:24:49] MeshCore [WX_BOT]: MeshCore started
```
✅ These are good - they mean the bot started successfully.

#### Protocol Messages
```
[2026-02-21 05:24:49] MeshCore [WX_BOT]: MeshCore: device time requested, responding…
[2026-02-21 05:25:12] MeshCore [WX_BOT]: MeshCore: message acknowledgment received
[2026-02-21 05:25:13] MeshCore [WX_BOT]: MeshCore: message queue empty
```
✅ These are normal - the bot is communicating with the LoRa radio.

#### Data Filtering (Removed - Now Silent)

Previously, the bot would log "Ignoring non-JSON LoRa data" for protocol messages and noise. This was confusing users who thought their commands were being ignored. **This message has been removed** - non-message data is now silently filtered without cluttering the logs.

If you see NO log messages at all after commands are sent, see the troubleshooting steps below.

### What You Should See When a Message Arrives

When someone sends "wx London" to the bot, you should see:

```
[2026-02-21 05:25:30] MeshCore [WX_BOT]: Binary frame: CHANNEL_MSG_V3 on channel_idx 2
[2026-02-21 05:25:30] MeshCore [WX_BOT]: LoRa RX channel msg from M3UXC on channel_idx 2: wx London
[2026-02-21 05:25:30] MeshCore [WX_BOT]: Channel filter check: default=False, matching=False, unnamed=True → will_process=True (filter: 'weather')
[2026-02-21 05:25:30] MeshCore [WX_BOT]: Received message from M3UXC: wx London
[2026-02-21 05:25:30] WeatherBot: Processing message from M3UXC: wx London
[2026-02-21 05:25:30] WeatherBot: Weather request for location: London
[2026-02-21 05:25:30] WeatherBot: Replying on channel_idx 2: Weather for London, GB...
```

If you don't see these messages, it means:
1. No one has sent a "wx [location]" command yet, OR
2. The messages are not reaching your bot's radio

### Troubleshooting Steps

#### 1. Verify Someone is Actually Sending Commands

**Action**: Use another radio or the MeshCore app to send "wx London" on any channel.

**Expected**: You should see "LoRa RX channel msg" in the logs.

**If you don't see it**: The message is not reaching your radio. Check:
- Is the sending radio within range?
- Is the sending radio powered on and transmitting?
- Are both radios on the same frequency/band?
- Check radio configuration (LoRa settings, encryption, etc.)

#### 2. Check Channel Configuration

The bot with `--channel weather` will accept messages from:
- **Default channel** (channel_idx 0) - Always accepted
- **Any non-default channel** (channel_idx 1-7) - Always accepted when no specific channel name is set
- **Named "weather" channel** - Always accepted

This means the bot should respond to messages on ANY channel! The `--channel` parameter mainly affects WHERE the bot SENDS its responses.

**What this means**: 
- If you send "wx London" on channel_idx 0 (default), the bot will receive and respond
- If you send "wx London" on channel_idx 1, the bot will receive and respond
- If you send "wx London" on channel_idx 2, the bot will receive and respond
- And so on...

The bot replies on the SAME channel_idx it received the message on.

#### 3. Check Message Format

The bot looks for commands matching:
- `wx [location]` (e.g., "wx London", "wx Manchester", "wx New York")
- `weather [location]` (e.g., "weather London")

**Case insensitive**: "WX LONDON" and "wx london" both work.

**Won't match**:
- "weather" (no location specified)
- "wxLondon" (no space)
- "what's the weather" (wrong format)

#### 4. Check Internet Connection

The weather bot needs internet access to query the weather API.

**Test**: Run in test mode:
```bash
python3 weather_bot.py -l London -d
```

If this shows "Error: requests library not found" or connection errors, your network is not working.

#### 5. Enable Full Debug Logging

Run with the `-d` flag to see all internal processing:

```bash
python3 weather_bot.py -n WX_BOT --port /dev/ttyUSB1 --baud 115200 --channel weather -d
```

Look for:
- "Binary frame: CHANNEL_MSG" - means a message arrived
- "LoRa RX channel msg from [sender]" - shows who sent what
- "Channel filter check" - shows if the message passed filtering
- "Processing message from [sender]" - shows the bot is handling it
- "Weather request for location: [location]" - shows the command was recognized

### Common Scenarios

#### Scenario 1: Everything Starts Fine, But No Messages

**Symptoms**:
```
[2026-02-21 05:24:49] MeshCore [WX_BOT]: MeshCore started
Weather Bot started. Send 'wx [location]' to get weather.
Listening for messages...
[2026-02-21 05:25:12] MeshCore [WX_BOT]: MeshCore: message queue empty
[2026-02-21 05:25:13] MeshCore [WX_BOT]: MeshCore: message queue empty
```

**Diagnosis**: The bot is working correctly and waiting for messages. No one has sent a command yet.

**Action**: Send "wx London" from another radio and watch the logs. You should see "Binary frame: CHANNEL_MSG" when a message arrives.

#### Scenario 2: Messages Received But Not Processed

**Symptoms**:
```
[2026-02-21 05:25:30] MeshCore [WX_BOT]: LoRa RX channel msg from M3UXC: hello world
[2026-02-21 05:25:30] WeatherBot: Processing message from M3UXC: hello world
[2026-02-21 05:25:30] WeatherBot: Not a weather command: hello world
```

**Diagnosis**: The bot received the message but it doesn't match the "wx [location]" pattern.

**Action**: Send a properly formatted command like "wx London".

## Getting Help

If you're still having issues after following this guide:

1. **Capture a full debug log**: Run with `-d` and save the output
2. **Note what you sent**: Record exactly what command you sent and from which radio
3. **Look for channel message logs**: Search for "Binary frame: CHANNEL_MSG" or "LoRa RX channel msg" to see if messages are arriving
4. **Open an issue**: Include the above information in a GitHub issue

## Advanced Debugging

### Checking Serial Port

Verify your serial port is working:

```bash
ls -l /dev/ttyUSB*
# Should show your device

# Check permissions
sudo chmod 666 /dev/ttyUSB1  # Or add your user to the dialout group
```

### Testing Without Radio

Test the bot logic without hardware:

```bash
python3 weather_bot.py -i -d
```

This starts interactive mode where you can type commands directly.

### Monitoring Serial Data

Use a serial monitor to see raw data:

```bash
# Install screen or minicom
screen /dev/ttyUSB1 115200
# or
minicom -D /dev/ttyUSB1 -b 115200
```

Press Ctrl+A then K to exit screen.

## Understanding Channel Behavior

### Bot Configuration: `--channel weather`

This configuration means:
- **RECEIVING**: Accept messages from ALL channels (see channel filter logic above)
- **SENDING**: When broadcasting (not replying), send on the "weather" channel (mapped to channel_idx 1)
- **REPLYING**: Always reply on the same channel the message came from

### Example Flow

1. User on channel_idx 3 sends: "wx London"
2. Bot receives on channel_idx 3 (accepted because it's non-default)
3. Bot processes the command
4. Bot replies on channel_idx 3 (same as received)
5. User sees the response on their channel

This design ensures the bot works with any channel configuration!
