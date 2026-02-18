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

## Basic Usage

### Sending Messages to a Channel

```bash
# Send a message to the 'weather' channel
python3 meshcore_send.py "Sunny today!" --channel weather

# Send a message without a channel (broadcast to all)
python3 meshcore_send.py "Hello everyone!"
```

### Running Weather Bot on a Channel

```bash
# Weather bot broadcasts responses on 'weather' channel
python3 weather_bot.py --channel weather --interactive

# Weather bot without channel (default behavior)
python3 weather_bot.py --interactive
```

## Python API

### Sending Messages

```python
from meshcore import MeshCore

mesh = MeshCore("my_node")
mesh.start()

# Send to a specific channel
mesh.send_message("Weather update!", "text", channel="weather")

# Send without channel (broadcast)
mesh.send_message("General message", "text")

mesh.stop()
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

# Message with channel
msg = MeshCoreMessage(
    sender="weather_station",
    content="Temperature: 15°C",
    message_type="text",
    channel="weather"
)

# Message without channel
msg = MeshCoreMessage(
    sender="my_node",
    content="Hello!",
    message_type="text"
)
```

## Use Cases

### 1. Dedicated Weather Service

```bash
# Start weather bot on dedicated channel
python3 weather_bot.py --channel weather --node-id weather_service

# Users query weather on the weather channel
python3 meshcore_send.py "wx London" --channel weather --node-id user1
```

### 2. Multiple Information Streams

```python
# Weather station
weather_mesh = MeshCore("weather_station")
weather_mesh.start()
weather_mesh.send_message("Temp: 15°C", "text", channel="weather")

# News station
news_mesh = MeshCore("news_station")
news_mesh.start()
news_mesh.send_message("Event at 3pm", "text", channel="news")

# Alert system
alert_mesh = MeshCore("alert_station")
alert_mesh.start()
alert_mesh.send_message("Storm warning", "text", channel="alerts")
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

2. **Document Your Channels**: Keep a list of channels and their purposes

3. **Don't Overuse Channels**: Too many channels can be confusing. Start with a few common ones.

4. **Backward Compatibility**: Not all nodes may support channels. Messages without channels work everywhere.

5. **Channel Naming Convention**: Use simple, single-word channel names when possible

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
python3 test_channel_functionality.py

# Interactive testing
python3 weather_bot.py --channel weather --interactive
```

## Troubleshooting

**Q: My messages aren't being received**
- Check that the receiver isn't filtering on a different channel
- Verify the channel name matches exactly (case-sensitive)

**Q: Can I send to multiple channels at once?**
- No, each message can only be on one channel. Send separate messages for multiple channels.

**Q: What if I don't specify a channel?**
- Messages without a channel are broadcast to everyone (except nodes filtering on a specific channel)

**Q: Are channels secure?**
- No, channels are just labels. They organize messages but don't provide encryption or access control.

## More Information

- See `README.md` for general usage
- See `QUICKSTART.md` for quick setup instructions
- Run `python3 example_channels.py` for working examples
- Run `python3 test_channel_functionality.py` for feature tests
