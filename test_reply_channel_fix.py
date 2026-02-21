#!/usr/bin/env python3
"""
Test to verify the weather bot now replies to the channel where messages come from.

This addresses the issue where the bot was broadcasting to a hardcoded channel
instead of replying to the channel where the incoming message originated.
"""

import sys
from unittest.mock import MagicMock, patch
from meshcore import MeshCore, MeshCoreMessage
from weather_bot import WeatherBot


def test_reply_to_incoming_channel():
    """Test that bot replies to the channel the message came from"""
    print("=" * 70)
    print("TEST: Bot Replies to Incoming Message Channel")
    print("=" * 70)
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
                "temperature_2m": 8.9,
                "apparent_temperature": 5.3,
                "relative_humidity_2m": 78,
                "wind_speed_10m": 16.7,
                "wind_direction_10m": 264,
                "precipitation": 0.0,
                "weather_code": 3
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Create bot with a configured channel
        bot = WeatherBot(node_id="WX_BOT", debug=True, channel="wxtest")
        
        # Mock the mesh send_message to track what channel it sends to
        sent_messages = []
        original_send = bot.mesh.send_message
        
        def track_send(content, message_type, channel):
            sent_messages.append({
                'content': content,
                'type': message_type,
                'channel': channel
            })
            return original_send(content, message_type, channel)
        
        bot.mesh.send_message = track_send
        bot.mesh.start()
        
        print("Scenario 1: Message comes from a specific channel")
        print("-" * 70)
        
        # Simulate receiving a message from channel 'weather'
        msg = MeshCoreMessage(
            sender="M3UXC",
            content="Weather leeds",
            message_type="text",
            channel="weather"  # Message came from 'weather' channel
        )
        
        print(f"Incoming: '{msg.content}' from {msg.sender} on channel '{msg.channel}'")
        print()
        
        # Process the message
        sent_messages.clear()
        bot.handle_message(msg)
        
        # Verify the bot replied to the 'weather' channel, not 'wxtest'
        assert len(sent_messages) == 1, f"Expected 1 message sent, got {len(sent_messages)}"
        sent = sent_messages[0]
        
        print(f"✓ Bot sent reply to channel: '{sent['channel']}'")
        
        # The key assertion: bot should reply to 'weather', not the configured 'wxtest'
        assert sent['channel'] == 'weather', \
            f"Expected reply on 'weather' channel, got '{sent['channel']}'"
        
        print(f"✓ Bot correctly replied to incoming channel 'weather' (not configured 'wxtest')")
        print()
        
        print("Scenario 2: Message comes without a channel, bot uses configured channels")
        print("-" * 70)
        
        # Mock again for second request
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Simulate receiving a message without a channel
        msg2 = MeshCoreMessage(
            sender="M3UXC",
            content="wx barnsley",
            message_type="text",
            channel=None  # No channel specified
        )
        
        print(f"Incoming: '{msg2.content}' from {msg2.sender} with no channel")
        print()
        
        # Process the message
        sent_messages.clear()
        bot.handle_message(msg2)
        
        # When no incoming channel, should use configured channel
        assert len(sent_messages) == 1, f"Expected 1 message sent, got {len(sent_messages)}"
        sent = sent_messages[0]
        
        print(f"✓ Bot sent to channel: '{sent['channel']}'")
        assert sent['channel'] == 'wxtest', \
            f"Expected broadcast on 'wxtest' (configured), got '{sent['channel']}'"
        
        print(f"✓ Bot correctly used configured channel 'wxtest' as fallback")
        print()
        
        bot.mesh.stop()


def test_no_configured_channel():
    """Test bot without configured channels - should broadcast"""
    print("=" * 70)
    print("TEST: Bot Without Configured Channels")
    print("=" * 70)
    print()
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "York",
                "country": "United Kingdom",
                "latitude": 53.95997,
                "longitude": -1.08781
            }]
        }
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 10.5,
                "apparent_temperature": 8.2,
                "relative_humidity_2m": 70,
                "wind_speed_10m": 12.0,
                "wind_direction_10m": 180,
                "precipitation": 0.0,
                "weather_code": 1
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Create bot WITHOUT configured channels
        bot = WeatherBot(node_id="WX_BOT", debug=True, channel=None)
        
        # Track sent messages
        sent_messages = []
        original_send = bot.mesh.send_message
        
        def track_send(content, message_type, channel):
            sent_messages.append({
                'content': content,
                'type': message_type,
                'channel': channel
            })
            return original_send(content, message_type, channel)
        
        bot.mesh.send_message = track_send
        bot.mesh.start()
        
        print("Scenario: Message with channel, bot has no configured channel")
        print("-" * 70)
        
        # Simulate message from a channel
        msg = MeshCoreMessage(
            sender="M3UXC",
            content="wx york",
            message_type="text",
            channel="localweather"
        )
        
        print(f"Incoming: '{msg.content}' from {msg.sender} on channel '{msg.channel}'")
        print()
        
        # Process the message
        sent_messages.clear()
        bot.handle_message(msg)
        
        # Should reply to the incoming channel
        assert len(sent_messages) == 1
        sent = sent_messages[0]
        
        print(f"✓ Bot sent reply to channel: '{sent['channel']}'")
        assert sent['channel'] == 'localweather', \
            f"Expected reply on 'localweather', got '{sent['channel']}'"
        
        print(f"✓ Bot correctly replied to 'localweather' channel")
        print()
        
        bot.mesh.stop()


def main():
    """Run all reply channel tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "Reply Channel Fix Tests" + " " * 27 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print("This verifies the fix for the issue where the bot was not")
    print("replying back to users on the correct channel.")
    print()
    
    try:
        test_reply_to_incoming_channel()
        test_no_configured_channel()
        
        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("  1. Bot now replies to the channel where messages originate")
        print("  2. Configured channels are used as fallback when no incoming channel")
        print("  3. Bot works correctly with or without configured channels")
        print()
        print("The bot will now properly reply to users on the same channel")
        print("they sent their weather requests from.")
        print()
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
