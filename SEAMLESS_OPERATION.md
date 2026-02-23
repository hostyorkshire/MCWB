# Seamless Channel Operation

## How It Works

The weather bot is designed to **work seamlessly** with your MeshCore radio's channel configuration. No manual configuration is needed in the bot itself!

## Key Concepts

### 1. Encryption Happens at the Radio Level

- MeshCore uses **Diffie-Hellman key exchange** for channel encryption
- All encryption/decryption is handled by the **radio firmware**
- The bot receives **plain text** for channels your radio has keys for
- The bot receives **garbled data** for channels your radio doesn't have keys for

### 2. The Bot Automatically Adapts

```
┌─────────────────────────────────────────────────────────┐
│  Your MeshCore Radio                                    │
│  • Subscribed to #weather (channel 1) ✓                 │
│  • Subscribed to #alerts (channel 2) ✓                  │
│  • NOT subscribed to #private (channel 3) ✗             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Weather Bot (Automatic Behavior)                       │
│  • Receives "WX Leeds" on channel 1 → Responds ✓        │
│  • Receives "weather York" on channel 2 → Responds ✓    │
│  • Receives garbled data on channel 3 → Silently skip   │
└─────────────────────────────────────────────────────────┘
```

### 3. Silent Operation

By default, the bot:
- ✅ **Processes** messages on channels where your radio has valid keys
- ✅ **Silently skips** encrypted messages from channels without keys
- ✅ **No log spam** - encrypted messages don't clutter your logs
- ✅ **Just works** - no configuration needed!

## Setup Instructions

### For End Users

1. **Configure your radio FIRST** (BEFORE connecting to PC/Pi or starting the bot):
   - Open MeshCore mobile app
   - Connect to your companion radio
   - Go to Channel Settings  
   - Join/subscribe to channels you want (#weather, #alerts, etc.)
   - Your radio performs Diffie-Hellman key exchange automatically
   - **Important:** This step MUST be done through the MeshCore app - the bot cannot configure channels for you

2. **Connect your radio** to your PC/Pi via USB

3. **Run the bot** - that's it!
   ```bash
   python3 weather_bot.py
   ```

4. **Send weather commands** on any channel your radio is subscribed to:
   ```
   WX Leeds
   weather London
   ```

The bot automatically works on all channels your radio can decrypt!

## No Configuration Needed

❌ **You DON'T need to:**
- Tell the bot which channels to listen on
- Configure channel indices manually
- Match channel numbers between devices
- Update bot configuration when adding new channels

✅ **The bot automatically:**
- Detects which channels your radio can decrypt
- Responds on those channels
- Ignores encrypted messages from other channels
- Adapts when you add/remove channel subscriptions

## Troubleshooting (Optional)

If you want to **verify** which channels are working, use diagnostic mode:

```bash
python3 weather_bot.py --verify-channels
```

This will show you on exit:
- Which channels received successfully decrypted messages
- Which channels received encrypted messages (radio doesn't have keys)
- Guidance on how to add more channels if needed

**Note:** This is optional! Most users don't need it.

## Why This Approach?

### The Technical Reality

- **Protocol limitation**: The MeshCore companion radio protocol does NOT provide commands to query or configure channel subscriptions
- **Security design**: Diffie-Hellman key exchange happens at the firmware level for security
- **No programmatic access**: The bot cannot read, set, or modify channel keys

### The Practical Solution

Instead of fighting these limitations, we embrace them:

1. **Users configure channels in the MeshCore app** (where it's designed to be done)
2. **The bot adapts to whatever channels are configured** (seamless integration)
3. **Encrypted messages are silently filtered** (clean operation)

This is how other successful MeshCore bots (like Jeff's ping bot) work too!

## Example Scenarios

### Scenario 1: Single Channel Setup

```
User's radio: Subscribed to #weather (channel 1)
Bot's radio: Subscribed to #weather (channel 1)

Result: Everything works! ✓
```

### Scenario 2: Multi-Channel Setup

```
User's radio: Subscribed to #weather, #alerts, #news
Bot's radio: Subscribed to #weather, #alerts

Result: 
- Weather commands on #weather work ✓
- Weather commands on #alerts work ✓  
- Commands on #news are silently ignored (bot's radio doesn't have keys)
```

### Scenario 3: Adding a New Channel

```
1. User adds #forecast channel in MeshCore app on their radio
2. Bot operator adds #forecast channel in MeshCore app on bot's radio
3. Both radios perform Diffie-Hellman key exchange
4. Bot automatically starts responding on #forecast

No bot restart or configuration change needed!
```

## Best Practices

### For Bot Operators

1. **Subscribe to common channels** your users will likely use:
   - #weather (primary)
   - #wx, #wxtest (alternatives)
   - #general (backup)

2. **Run without restrictions** (default behavior):
   ```bash
   python3 weather_bot.py
   ```
   This lets the bot respond on ALL subscribed channels.

3. **Coordinate with your mesh community**:
   - Agree on channel names
   - Ensure everyone subscribes to the same channels
   - Document which channels the bot monitors

### For Users

1. **Subscribe to the same channels** the bot is on
2. **Send weather commands** on those channels
3. **If it doesn't work**, check your channel subscriptions in the MeshCore app

## Comparison to Manual Configuration

### ❌ Old Way (Manual)
```bash
# Configure channel indices manually
python3 weather_bot.py --channel-idx 1

# Problem: Only works if everyone's channel 1 is the same channel
# Problem: Breaks if users have #weather on different indices
# Problem: Requires coordination and documentation
```

### ✅ New Way (Seamless)
```bash
# Just run it!
python3 weather_bot.py

# Works on all subscribed channels automatically
# Adapts to each user's channel configuration
# No coordination needed beyond channel names
```

## Summary

**The bot seamlessly works with whatever channels your radio is subscribed to.**

No manual configuration. No channel indices. No hassle. Just configure your radio once in the MeshCore app, and the bot automatically adapts!
