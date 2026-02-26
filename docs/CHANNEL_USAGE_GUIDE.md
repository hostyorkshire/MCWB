# Channel Usage Guide: Use ANY Channel You Want

## Key Point: wxtest is Just an Example

**#wxtest is NOT special, required, or default.** It's just a testing/example channel name used in documentation.

You can create and use **ANY channel name** you want:
- `#weather`
- `#mybot`
- `#sensors`
- `#alerts`
- `#mycustomchannel`
- Or ANY other name you choose!

## How Channel IDs Work

The bot **automatically assigns channel IDs dynamically** as channels are used:

```
Your channels:          Bot assigns:
─────────────          ─────────────
(none specified)    →  channel_idx 0 (default)
#weather           →  channel_idx 1 (first named channel)
#alerts            →  channel_idx 2 (second named channel)
#sensors           →  channel_idx 3 (third named channel)
... and so on up to channel_idx 7
```

### Dynamic Assignment Example

```python
# Example 1: User creates channels in this order
1. Create #myweather in MeshCore app  → Gets channel_idx 1
2. Create #myalerts in MeshCore app   → Gets channel_idx 2
3. Bot automatically works on both!

# Example 2: Different user, different order
1. Create #testing in MeshCore app    → Gets channel_idx 1
2. Create #production in MeshCore app → Gets channel_idx 2
3. Bot automatically works on both!
```

**The bot doesn't care what you name your channels!**

## Bot Behavior (Default)

When you run the bot without any flags:

```bash
python3 weather_bot.py
```

The bot will:
- ✅ Accept wx commands from **ANY channel** (0-7)
- ✅ Reply on the **SAME channel** where the command came from
- ✅ Work with **ANY channel name** you create
- ✅ Automatically handle channel ID mapping

## Why Documentation Mentions wxtest

In examples and tests, we needed to use **some** channel name, so we picked "wxtest" as a consistent example. That's it!

You'll see it in:
- Documentation examples (just showing how to use a channel)
- Test scripts (tests need a channel name to test with)
- Troubleshooting guides (using wxtest as the example channel)

**But you should use whatever channel name makes sense for YOUR setup!**

## Creating Your Own Channels

### Step 1: Choose Your Channel Name

Pick any name that makes sense for you:
- Weather bot? → `#weather` or `#wx` or `#forecast`
- Testing? → `#test` or `#dev` or `#staging`
- Production? → `#prod` or `#live` or `#main`
- Specific location? → `#london-weather` or `#nyc-wx`

### Step 2: Create Channel in MeshCore App

**IMPORTANT:** Do this BEFORE starting the bot!

1. Open MeshCore app on your phone/tablet
2. Connect to your companion radio (the one that will be connected to your bot)
3. Go to Channels section
4. Create new channel with your chosen name
5. Join/subscribe to the channel
6. MeshCore automatically assigns it a channel_idx (1-7)
7. Save your configuration

**Note:** The bot cannot create or subscribe to channels automatically. This must be done through the MeshCore app.

### Step 3: Use the Bot

Just run the bot - no special configuration needed!

```bash
python3 weather_bot.py
```

Send commands on your channel:
```
You on #myweather: "wx London"
Bot replies on #myweather: "London, GB\nPartly cloudy\n..."

You on #testing: "wx Paris"  
Bot replies on #testing: "Paris, FR\nClear sky\n..."
```

## Advanced: Restricting to Specific Channels

If you want the bot to ONLY work on specific channels:

```bash
# Only respond on channel index 2
python3 weather_bot.py --channel-idx 2

# Only respond on named channel(s)
python3 weather_bot.py --channel weather

# Only respond on multiple named channels
python3 weather_bot.py --channel "weather,alerts,forecast"
```

But most users don't need this! The default (no restrictions) works great.

## Advanced: Announcement Channel

By default, announcements use the channel of the first message received. To specify a particular channel index for announcements:

```bash
# Send announcements on channel index 2
python3 weather_bot.py --weather-channel-idx 2 --announce
```

This is optional - most users don't need it!

## Summary

| Question | Answer |
|----------|--------|
| Can I use my own channel name? | ✅ YES! Use any name you want |
| Do I need to configure channel IDs? | ❌ NO! Bot assigns them automatically |
| Is wxtest special? | ❌ NO! It's just an example in docs |
| Can I create multiple channels? | ✅ YES! Bot works on all of them |
| Do I need special flags? | ❌ NO! Default works on all channels |

## Common Scenarios

### Scenario 1: Single Weather Channel
```bash
# Create #wx in MeshCore app
# Run bot:
python3 weather_bot.py

# Users send on #wx, bot replies on #wx
# Done!
```

### Scenario 2: Multiple Channels
```bash
# Create #weather and #testing in MeshCore app
# Run bot:
python3 weather_bot.py

# Bot automatically works on both channels
# Done!
```

### Scenario 3: Custom Channel Name
```bash
# Create #london-forecast in MeshCore app
# Run bot:
python3 weather_bot.py

# Bot works on your custom channel
# Done!
```

## Related Documentation

- `README.md` - Main documentation
- `QUICK_ANSWER_HASHTAG_CHANNELS.md` - Proof bot works on any channel
- `CHANNEL_GUIDE.md` - Technical details on channel implementation
