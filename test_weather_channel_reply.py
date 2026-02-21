#!/usr/bin/env python3
"""
Test specifically for --channel weather scenario from problem statement.
"""

import sys
from unittest.mock import MagicMock, patch
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_weather_channel():
    """Test bot with --channel weather"""
    print()
    print("=" * 70)
    print("TEST: Bot with --channel weather")
    print("=" * 70)
    print()
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock responses
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "Barnsley",
                "country": "United Kingdom",
                "latitude": 53.55,
                "longitude": -1.48333
            }]
        }
        
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 6.8,
                "apparent_temperature": 4.1,
                "relative_humidity_2m": 87,
                "wind_speed_10m": 10.3,
                "wind_direction_10m": 241,
                "precipitation": 0.0,
                "weather_code": 3
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Create bot with --channel weather (from problem statement)
        bot = WeatherBot(node_id="WX_BOT", debug=True, channel="weather")
        
        # Track messages
        sent_messages = []
        original_send = bot.mesh.send_message
        
        def track_send(content, message_type, channel=None, channel_idx=None):
            sent_messages.append({
                'content': content,
                'channel': channel,
                'channel_idx': channel_idx
            })
            return original_send(content, message_type, channel, channel_idx)
        
        bot.mesh.send_message = track_send
        bot.mesh.start()
        
        # Simulate exact message from problem statement logs
        msg = MeshCoreMessage(
            sender="M3UXC",
            content="Wx barnsley",
            message_type="text",
            channel=None,
            channel_idx=0
        )
        
        print("Scenario from problem statement:")
        print("  Command: python3 weather_bot.py --channel weather")
        print(f"  Receives: message from {msg.sender} on channel_idx {msg.channel_idx}")
        print(f"  Content: {msg.content}")
        print()
        
        sent_messages.clear()
        bot.handle_message(msg)
        
        print("Checking bot reply...")
        assert len(sent_messages) == 1
        
        sent = sent_messages[0]
        print(f"  Bot replied on: channel='{sent['channel']}', channel_idx={sent['channel_idx']}")
        print()
        
        if sent['channel_idx'] == 0:
            print("✅ SUCCESS!")
            print()
            print("Bot correctly replied on channel_idx 0 (where message came from)")
            print("User M3UXC will see the reply even though bot is configured for 'weather' channel")
            print("This ensures clients always receive responses regardless of channel configuration!")
            success = True
        else:
            print("❌ FAILED!")
            print(f"  Expected: channel_idx=0")
            print(f"  Got: channel_idx={sent['channel_idx']}")
            success = False
        
        bot.mesh.stop()
        return success


def main():
    """Run the test"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "Weather Channel Reply Test" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        success = test_weather_channel()
        
        print()
        print("=" * 70)
        if success:
            print("✅ TEST PASSED")
            print()
            print("The bot now correctly replies on the same channel where")
            print("the query came from, ensuring clients always see responses")
            print("even when bot is configured with a specific --channel")
        else:
            print("❌ TEST FAILED")
        print("=" * 70)
        print()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
