#!/usr/bin/env python3
"""
Test that validates bot replies on configured channels when --channel is specified.

When a bot is configured with --channel, it should reply on that channel,
not on the default channel (channel_idx 0) where the message came from.

This test addresses the requirement: "the bot is working in the wxtest channel"
"""

import sys
from unittest.mock import MagicMock, patch
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_bot_replies_on_configured_channel():
    """
    Test that bot configured with --channel alerts replies on alerts channel,
    not on default channel (channel_idx 0) where message came from.
    """
    print()
    print("=" * 70)
    print("TEST: Bot Replies on Configured Channel")
    print("=" * 70)
    print()
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "Birmingham",
                "country": "United Kingdom",
                "latitude": 52.48142,
                "longitude": -1.89983
            }]
        }
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 8.6,
                "apparent_temperature": 6.3,
                "relative_humidity_2m": 91,
                "wind_speed_10m": 10.9,
                "wind_direction_10m": 224,
                "precipitation": 0.0,
                "weather_code": 80
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Create bot with --channel alerts
        bot = WeatherBot(node_id="WX_BOT", debug=True, channel="alerts")
        
        # Track what channel the bot replies on
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
        
        # Simulate message received on default channel (channel_idx 0)
        # This is the scenario from the logs
        msg = MeshCoreMessage(
            sender="M3UXC",
            content="Wx Birmingham",
            message_type="text",
            channel=None,          # No channel name (default channel)
            channel_idx=0          # Default channel index
        )
        
        print("Simulating message from logs:")
        print(f"  Bot configured with: --channel alerts")
        print(f"  Message from: {msg.sender}")
        print(f"  Message content: {msg.content}")
        print(f"  Message channel_idx: {msg.channel_idx}")
        print()
        
        # Process the message
        sent_messages.clear()
        bot.handle_message(msg)
        
        # Verify the fix
        print("Checking bot reply...")
        assert len(sent_messages) == 1, f"Expected 1 reply, got {len(sent_messages)}"
        
        sent = sent_messages[0]
        print(f"  Bot replied on: channel='{sent['channel']}', channel_idx={sent['channel_idx']}")
        print()
        
        # The bot should reply on 'alerts' channel (its configured channel)
        # NOT on channel_idx 0 (where message came from)
        if sent['channel'] == 'alerts':
            print("✅ SUCCESS!")
            print()
            print("Bot correctly replied on 'alerts' channel")
            print("(the channel it was configured with)")
            print()
            print("This meets the requirement:")
            print("  Bot with --channel always replies on configured channel")
            print()
            print("Users monitoring the alerts channel will see the reply!")
            success = True
        else:
            print("❌ FAILED!")
            print(f"  Expected: channel='alerts'")
            print(f"  Got: channel='{sent['channel']}', channel_idx={sent['channel_idx']}")
            print()
            print("Bot is not replying on the configured channel!")
            success = False
        
        bot.mesh.stop()
        
        return success


def test_bot_without_channel_config():
    """
    Test that bot without --channel configuration replies on the channel
    where the message came from (backward compatibility).
    """
    print()
    print("=" * 70)
    print("TEST: Bot Without Channel Config (Backward Compatibility)")
    print("=" * 70)
    print()
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock responses
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "Leeds",
                "country": "United Kingdom",
                "latitude": 53.79648,
                "longitude": -1.54785
            }]
        }
        
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
        
        # Create bot WITHOUT --channel configuration
        bot = WeatherBot(node_id="WX_BOT", debug=True, channel=None)
        
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
        
        # Message on default channel
        msg = MeshCoreMessage(
            sender="M3UXC",
            content="Wx Leeds",
            message_type="text",
            channel=None,
            channel_idx=0
        )
        
        print("Simulating message:")
        print(f"  Bot configured with: (no --channel)")
        print(f"  Message channel_idx: {msg.channel_idx}")
        print()
        
        sent_messages.clear()
        bot.handle_message(msg)
        
        print("Checking bot reply...")
        assert len(sent_messages) == 1
        
        sent = sent_messages[0]
        print(f"  Bot replied on: channel='{sent['channel']}', channel_idx={sent['channel_idx']}")
        print()
        
        # Bot without channel config should reply on the channel_idx where message came from
        if sent['channel_idx'] == 0:
            print("✅ SUCCESS!")
            print()
            print("Bot without --channel correctly replied on channel_idx 0")
            print("(where the message came from)")
            success = True
        else:
            print("❌ FAILED!")
            print("Bot should reply on channel_idx 0 when no --channel is configured")
            success = False
        
        bot.mesh.stop()
        
        return success


def main():
    """Run the tests"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Channel Reply Priority Test" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        success1 = test_bot_replies_on_configured_channel()
        success2 = test_bot_without_channel_config()
        
        print()
        print("=" * 70)
        if success1 and success2:
            print("✅ ALL TESTS PASSED")
            print()
            print("Summary:")
            print("  • Bot with --channel replies on configured channel ✓")
            print("  • Bot without --channel replies on incoming channel ✓")
            print("  • Channel reply behavior working correctly ✓")
        else:
            print("❌ SOME TESTS FAILED")
            if not success1:
                print("  • Bot with --channel not working correctly")
            if not success2:
                print("  • Bot without --channel not working correctly")
        print("=" * 70)
        print()
        
        return 0 if (success1 and success2) else 1
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
