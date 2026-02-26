# MeshCore Channel Guide

## Overview

MeshCore now supports channel-based broadcasting, allowing organized communication streams across your mesh network. This guide explains how to use channels effectively.

## What are Channels?

Channels are named communication streams that help organize messages on your mesh network. Think of them like radio channels or chat rooms:

- **weather** - For weather updates and forecasts
- **news** - For news and announcements
- **alerts** - For emergency or important notifications
- **general** - For general communication

You can use any channel name you want. Channels are optional - messages without a channel are broadcast to everyone.

## Channel Index (MESHCORE_CHANNEL_IDX)

Every named channel is transmitted over a specific **channel slot** on the companion radio, identified by a numeric **channel index** (`channel_idx`, also referred to as `MESHCORE_CHANNEL_IDX` in the MeshCore protocol).

| Concept | Type | Description |
|---------|------|-------------|
| `channel` (name) | `str` | Human-readable label (e.g. `"weather"`, `"alerts"`) |
| `channel_idx` | `int` (0–7) | Numeric slot on the companion radio hardware |

Key rules:
- The companion radio supports **8 channel slots** (indices `0`–`7`).
- **Slot 0** is the default channel used when no channel name is given. In MeshCore firmware, slot 0 typically uses a well-known PSK for broad accessibility, while slots 1-7 (hashtag channels) use unique PSKs for encrypted communication.
- Named channels are mapped to slots `1`–`7` automatically, or you can specify the index directly.
- The channel index in a **received** message tells you exactly which slot it arrived on; replies should use the same index to reach the same audience.

### How `channel_idx` is used

**Receiving:** Every incoming channel message carries a `channel_idx` byte in the binary frame.
The bot reads this byte to know which slot the message arrived on.

**Sending:** When you send a reply, you pass back the same `channel_idx` so the radio
transmits on the correct slot.

```
Received frame: PUSH_CHAN_MSG
  payload[1] = channel_idx  ← which slot this came from

Send frame: CMD_SEND_CHAN_MSG
  payload[2] = channel_idx  ← which slot to transmit on
```

### Why does the index matter?

If your companion radio has its `#weather` channel configured as slot 1, you **must** send
on `channel_idx=1` to reach the same audience.  Using slot 0 or any other slot will transmit
on a different frequency plan and the target devices will not receive the message.

Check your MeshCore firmware/app configuration to see which slot number each named channel
uses on your specific device.

## Basic Usage

### Sending Messages to a Channel

```bash
# Send on channel slot 1 directly (MESHCORE_CHANNEL_IDX = 1)
python3 meshcore_send.py "Sunny today!" --channel-idx 1

# Send by channel name (name is mapped to a slot automatically)
python3 meshcore_send.py "Sunny today!" --channel weather

# Send on slot 1 AND record it as the 'weather' channel
python3 meshcore_send.py "Sunny today!" --channel weather --channel-idx 1

# Send a message without a channel (slot 0 – broadcast to all)
python3 meshcore_send.py "Hello everyone!"
```

### Running Weather Bot on Channels

```bash
# Weather bot broadcasts responses on a single channel
python3 weather_bot.py --channel weather --interactive

# Weather bot listens and responds only on channel slot 1
python3 weather_bot.py --channel-idx 1

# Weather bot without channel (default behavior - broadcast to all)
python3 weather_bot.py --interactive
```

## Python API

### Sending Messages

```python
from meshcore import MeshCore

mesh = MeshCore("my_node")
mesh.start()

# Send to channel slot 1 directly (MESHCORE_CHANNEL_IDX = 1)
mesh.send_message("Weather update!", "text", channel_idx=1)

# Send by name (mapped to a slot internally)
mesh.send_message("Weather update!", "text", channel="weather")

# Send without channel (slot 0 – broadcast)
mesh.send_message("General message", "text")

mesh.stop()
```

### Receiving Messages

Incoming messages expose both the channel name (if mapped) and the raw index:

```python
from meshcore import MeshCore, MeshCoreMessage

mesh = MeshCore("my_node")

def message_handler(message: MeshCoreMessage):
    print(f"Received: {message.content}")
    if message.channel:
        print(f"  Channel name : {message.channel}")
    if message.channel_idx is not None:
        print(f"  Channel index: {message.channel_idx}  (MESHCORE_CHANNEL_IDX)")
    # Reply on the exact same slot
    mesh.send_message(f"Echo: {message.content}", "text",
                      channel_idx=message.channel_idx)

mesh.register_handler("text", message_handler)
mesh.start()
```

### Filtering Received Messages

```python
from meshcore import MeshCore, MeshCoreMessage

mesh = MeshCore("my_node")

def message_handler(message):
    print(f"Received: {message.content}")
    if message.channel:
        print(f"  Channel: {message.channel}")

mesh.register_handler("text", message_handler)
mesh.start()

# Listen only to 'weather' channel
mesh.set_channel_filter("weather")

# Listen to all channels (default)
mesh.set_channel_filter(None)
```

### Creating Messages with Channels

```python
from meshcore import MeshCoreMessage

# Message with channel name
msg = MeshCoreMessage(
    sender="weather_station",
    content="Temperature: 15°C",
    message_type="text",
    channel="weather"
)

# Message with explicit channel index (MESHCORE_CHANNEL_IDX = 1)
msg = MeshCoreMessage(
    sender="weather_station",
    content="Temperature: 15°C",
    message_type="text",
    channel_idx=1
)

# Message without channel (broadcast on slot 0)
msg = MeshCoreMessage(
    sender="my_node",
    content="Hello!",
    message_type="text"
)
```

## Use Cases

### 1. Dedicated Weather Service

```bash
# Start weather bot listening only on channel slot 1
python3 weather_bot.py --channel-idx 1 --node-id weather_service

# Users send queries on slot 1
python3 meshcore_send.py "wx London" --channel-idx 1 --node-id user1
```

### 2. Multiple Information Streams

```python
# Weather station – broadcasts on slot 1
weather_mesh = MeshCore("weather_station")
weather_mesh.start()
weather_mesh.send_message("Temp: 15°C", "text", channel_idx=1)

# News station – broadcasts on slot 2
news_mesh = MeshCore("news_station")
news_mesh.start()
news_mesh.send_message("Event at 3pm", "text", channel_idx=2)

# Alert system – broadcasts on slot 3
alert_mesh = MeshCore("alert_station")
alert_mesh.start()
alert_mesh.send_message("Storm warning", "text", channel_idx=3)
```

### 3. Selective Listening

```python
# User only interested in weather and alerts
user_mesh = MeshCore("user1")
user_mesh.register_handler("text", my_handler)
user_mesh.start()

# Listen to weather
user_mesh.set_channel_filter("weather")
# ... later switch to alerts
user_mesh.set_channel_filter("alerts")
# ... or listen to everything
user_mesh.set_channel_filter(None)
```

## Best Practices

1. **Use Descriptive Channel Names**: Use clear, lowercase names like `weather`, `news`, `alerts`

2. **Match the radio slot configuration**: Check your MeshCore firmware / app to find out which numeric slot your named channels are configured on, then use `--channel-idx` to target that slot precisely.

3. **Reply on the received slot**: Always send replies using `channel_idx=message.channel_idx` so the response reaches the same audience.

4. **Don't Overuse Channels**: Too many channels can be confusing. Start with a few common ones.

5. **Backward Compatibility**: Not all nodes may support channels. Messages without channels work everywhere.

6. **Channel Naming Convention**: Use simple, single-word channel names when possible.

7. **Avoid the `#` prefix**: Channel names in Python should NOT include the `#` prefix – that is only used in the MeshCore app UI. Use `"weather"` not `"#weather"`.

## Channel Examples

Common channel names you might use:

- `weather` - Weather information and forecasts
- `news` - News and announcements
- `alerts` - Emergency and important notifications
- `chat` - General conversation
- `data` - Sensor data and telemetry
- `control` - Command and control messages
- `status` - System status updates

## Testing Channels

Run the included examples to see channels in action:

```bash
# Test basic channel functionality
python3 example_channels.py

# Test with channel tests
python3 tests/test_channel_functionality.py

# Interactive testing
python3 weather_bot.py --channel weather --interactive
```

## Troubleshooting

**Q: My messages aren't being received**
- Check that the receiver isn't filtering on a different channel
- Verify the channel name matches exactly (case-sensitive)
- If using `--channel-idx`, verify the slot number matches what the radio has configured

**Q: Can I send to multiple channels at once?**
- For individual messages in code, send separate `send_message()` calls to different
  `channel_idx` values or channel names as needed.
- For the weather bot, use one bot instance per channel slot (start with different
  `--channel-idx` values) or remove the filter to respond on all channels.

**Q: What if I don't specify a channel?**
- Messages without a channel are broadcast on slot 0 (the default channel, which typically uses a well-known PSK for broad accessibility).

**Q: What is `MESHCORE_CHANNEL_IDX`?**
- It is the numeric slot index (0–7) used in the MeshCore binary protocol to identify which
  physical channel slot a message is sent on or received from.  Use `--channel-idx` on the
  CLI or `channel_idx=` in the Python API to work with it directly.

**Q: Are channels secure?**
- In MeshCore, hashtag channels (channels 1-7, e.g., #weather, #wxtest, #alerts) **are encrypted** using channel-specific Pre-Shared Keys (PSKs). Only channel 0 (the default/public channel) typically uses a well-known PSK, making it effectively public. Channels organize messages AND provide encryption when configured with proper PSKs in the MeshCore firmware.

## More Information

- See `README.md` for general usage
- See `QUICKSTART.md` for quick setup instructions
- Run `python3 example_channels.py` for working examples
- Run `python3 tests/test_channel_functionality.py` for feature tests

