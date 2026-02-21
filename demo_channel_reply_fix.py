#!/usr/bin/env python3
"""
Demonstration of the channel reply fix for the problem statement.

This demonstrates:
- Bot started with --channel weather
- Receives message on channel_idx 0
- Correctly replies on the configured 'weather' channel (not channel_idx 0)
"""

import sys
from unittest.mock import MagicMock, patch
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def demo():
    """Demonstrate the fix"""
    print()
    print("=" * 70)
    print("DEMONSTRATION: Weather Bot Channel Reply Fix")
    print("=" * 70)
    print()
    print("Problem Statement:")
    print("  'when i run the command with weather channel the bot replies")
    print("   in the wxtest channel but not in the weather channel.")
    print("   I would like it to run in weather channel.'")
    print()
    print("-" * 70)
    print()
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "Leeds",
                "country": "United Kingdom",
                "latitude": 53.79648,
                "longitude": -1.54785
            }]
        }
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 8.5,
                "apparent_temperature": 5.3,
                "relative_humidity_2m": 80,
                "wind_speed_10m": 13.9,
                "wind_direction_10m": 253,
                "precipitation": 0.0,
                "weather_code": 3
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Create bot with configured channel 'weather'
        print("Step 1: Start bot with --channel weather")
        print("  Command: python3 weather_bot.py --channel weather")
        bot = WeatherBot(node_id="WX_BOT", debug=False, channel="weather")
        print(f"  ✓ Bot configured with channel: {bot.channels}")
        print()
        
        # Track what channel the bot uses
        sent_messages = []
        original_send = bot.mesh.send_message
        
        def track_send(content, message_type, channel, channel_idx=None):
            sent_messages.append({
                'channel': channel,
                'channel_idx': channel_idx
            })
            return original_send(content, message_type, channel, channel_idx)
        
        bot.mesh.send_message = track_send
        bot.mesh.start()
        
        # Simulate receiving a message on channel_idx 0 (like in the log)
        print("Step 2: User sends 'Wx leeds' on channel_idx 0")
        print("  (This is what happened in the problem statement log)")
        msg = MeshCoreMessage(
            sender="M3UXC",
            content="Wx leeds",
            message_type="text",
            channel=None,  # No channel name (default channel)
            channel_idx=0  # Incoming on channel_idx 0
        )
        print(f"  Message received: from {msg.sender} on channel_idx {msg.channel_idx}")
        print()
        
        # Process the message
        sent_messages.clear()
        bot.handle_message(msg)
        
        # Check what channel was used
        print("Step 3: Bot sends reply")
        if sent_messages:
            sent = sent_messages[0]
            print(f"  Reply sent on: channel='{sent['channel']}', channel_idx={sent['channel_idx']}")
            print()
            
            if sent['channel'] == 'weather':
                print("✅ SUCCESS: Bot correctly replied on 'weather' channel!")
                print()
                print("The fix works! When bot is started with --channel weather,")
                print("it now replies on the 'weather' channel regardless of where")
                print("the incoming message came from.")
            else:
                print(f"❌ FAIL: Bot replied on '{sent['channel']}' instead of 'weather'")
        else:
            print("❌ No messages sent")
        
        bot.mesh.stop()
    
    print()
    print("=" * 70)
    print()
    print("Explanation:")
    print("  BEFORE: Bot would reply on channel_idx 0 (where message came from)")
    print("  AFTER:  Bot replies on configured 'weather' channel")
    print()
    print("This matches the expected behavior from the problem statement:")
    print("  'I would like it to run in weather channel'")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    demo()
