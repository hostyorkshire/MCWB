#!/usr/bin/env python3
"""
Test that validates the fix for "bot is not replying to the client" issue.

This test validates that when a client sends a message on channel_idx 0,
the bot replies back on channel_idx 0, NOT on its configured channel.

This ensures the client actually sees the response.
"""

import sys
from unittest.mock import MagicMock, patch
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_bot_replies_to_client_on_incoming_channel():
    """
    Test that bot replies to client on the channel where the message came from.
    
    Scenario from problem statement:
    - Bot configured with --channel weather
    - Client M3UXC sends message on channel_idx 0 (default channel)
    - Bot should reply on channel_idx 0 (where client sent from)
    - NOT on 'weather' channel (channel_idx 1) where client isn't listening
    """
    print()
    print("=" * 70)
    print("TEST: Bot Replies to Client on Incoming Channel")
    print("=" * 70)
    print()
    print("Scenario: Client sends message on channel_idx 0")
    print("Expected: Bot replies on channel_idx 0 (where client is)")
    print("Previous Bug: Bot replied on 'weather' channel (where client wasn't)")
    print()
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "London",
                "country": "United Kingdom",
                "latitude": 51.50853,
                "longitude": -0.12574
            }]
        }
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 10.1,
                "apparent_temperature": 7.3,
                "relative_humidity_2m": 86,
                "wind_speed_10m": 15.6,
                "wind_direction_10m": 241,
                "precipitation": 0.0,
                "weather_code": 3
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Create bot with --channel weather (from problem statement)
        bot = WeatherBot(node_id="WX_BOT", debug=True, channel="weather")
        
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
        
        # Simulate EXACT message from problem statement log:
        # "LoRa RX channel msg from M3UXC on channel_idx 0: Wx london"
        msg = MeshCoreMessage(
            sender="M3UXC",
            content="Wx london",
            message_type="text",
            channel=None,          # No channel name (default channel)
            channel_idx=0          # Exact channel_idx from log
        )
        
        print("Simulating incoming message:")
        print(f"  From: {msg.sender}")
        print(f"  Content: {msg.content}")
        print(f"  Channel_idx: {msg.channel_idx}")
        print(f"  Bot configured with: --channel weather")
        print()
        
        # Process the message
        sent_messages.clear()
        bot.handle_message(msg)
        
        # Verify the fix
        print("Checking bot reply...")
        assert len(sent_messages) == 1, f"Expected 1 reply, got {len(sent_messages)}"
        
        sent = sent_messages[0]
        print(f"  Bot replied on: channel_idx={sent['channel_idx']}, channel='{sent['channel']}'")
        print()
        
        # The key assertion: bot should reply on channel_idx 0 (where client sent from)
        # NOT on 'weather' channel where client isn't listening
        if sent['channel_idx'] == 0:
            print("✅ SUCCESS!")
            print()
            print("Bot correctly replied on channel_idx 0")
            print("(the channel where the client sent the message from)")
            print()
            print("This fixes the problem:")
            print("  Before: Bot replied on 'weather' channel - client didn't see it")
            print("  After: Bot replies on channel_idx 0 - client DOES see it")
            print()
            print("The client M3UXC will now receive the weather response!")
            success = True
        else:
            print("❌ FAILED!")
            print(f"  Expected: channel_idx=0")
            print(f"  Got: channel_idx={sent['channel_idx']}, channel='{sent['channel']}'")
            print()
            print("Bot is NOT replying to the client!")
            print("Client won't see the response because they're on channel_idx 0")
            success = False
        
        bot.mesh.stop()
        
        return success


def test_bot_without_channel_config():
    """
    Test that bot without --channel configuration also replies correctly.
    
    This ensures the fix works across all bot configurations.
    """
    print()
    print("=" * 70)
    print("TEST: Bot Without Channel Config")
    print("=" * 70)
    print()
    print("Scenario: Bot without --channel, client sends on channel_idx 0")
    print("Expected: Bot replies on channel_idx 0")
    print()
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock responses
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "Manchester",
                "country": "United Kingdom",
                "latitude": 53.48095,
                "longitude": -2.23743
            }]
        }
        
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 9.5,
                "apparent_temperature": 6.8,
                "relative_humidity_2m": 78,
                "wind_speed_10m": 12.4,
                "wind_direction_10m": 220,
                "precipitation": 0.0,
                "weather_code": 1
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
            content="Wx Manchester",
            message_type="text",
            channel=None,
            channel_idx=0
        )
        
        print("Simulating incoming message:")
        print(f"  From: {msg.sender}")
        print(f"  Content: {msg.content}")
        print(f"  Channel_idx: {msg.channel_idx}")
        print(f"  Bot configured with: (no --channel)")
        print()
        
        sent_messages.clear()
        bot.handle_message(msg)
        
        print("Checking bot reply...")
        assert len(sent_messages) == 1
        
        sent = sent_messages[0]
        print(f"  Bot replied on: channel_idx={sent['channel_idx']}, channel='{sent['channel']}'")
        print()
        
        # Bot without channel config should reply on channel_idx 0
        if sent['channel_idx'] == 0:
            print("✅ SUCCESS!")
            print()
            print("Bot without --channel correctly replied on channel_idx 0")
            success = True
        else:
            print("❌ FAILED!")
            print("Bot should reply on channel_idx 0")
            success = False
        
        bot.mesh.stop()
        
        return success


def test_bot_replies_on_weather_channel():
    """
    Test that bot replies on weather channel when message comes from weather channel.
    
    This ensures the bot replies on channel_idx 1 when that's where the message came from.
    """
    print()
    print("=" * 70)
    print("TEST: Bot Replies on Weather Channel")
    print("=" * 70)
    print()
    print("Scenario: Bot with --channel weather, client sends on channel_idx 1")
    print("Expected: Bot replies on channel_idx 1 (where message came from)")
    print()
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock responses
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "York",
                "country": "United Kingdom",
                "latitude": 53.95763,
                "longitude": -1.08271
            }]
        }
        
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 11.2,
                "apparent_temperature": 8.9,
                "relative_humidity_2m": 75,
                "wind_speed_10m": 14.2,
                "wind_direction_10m": 235,
                "precipitation": 0.0,
                "weather_code": 2
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Create bot with --channel weather
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
        
        # Message on weather channel (channel_idx 1)
        msg = MeshCoreMessage(
            sender="M3UXC",
            content="Wx York",
            message_type="text",
            channel="weather",
            channel_idx=1
        )
        
        print("Simulating incoming message:")
        print(f"  From: {msg.sender}")
        print(f"  Content: {msg.content}")
        print(f"  Channel_idx: {msg.channel_idx}")
        print(f"  Bot configured with: --channel weather")
        print()
        
        sent_messages.clear()
        bot.handle_message(msg)
        
        print("Checking bot reply...")
        assert len(sent_messages) == 1
        
        sent = sent_messages[0]
        print(f"  Bot replied on: channel_idx={sent['channel_idx']}, channel='{sent['channel']}'")
        print()
        
        # Bot should reply on channel_idx 1 (where message came from)
        if sent['channel_idx'] == 1:
            print("✅ SUCCESS!")
            print()
            print("Bot correctly replied on channel_idx 1")
            print("(the channel where the message came from)")
            success = True
        else:
            print("❌ FAILED!")
            print(f"Expected: channel_idx=1")
            print(f"Got: channel_idx={sent['channel_idx']}")
            success = False
        
        bot.mesh.stop()
        
        return success


def main():
    """
    Run the tests.
    
    Returns:
        int: Exit code - 0 if all tests pass, 1 if any test fails
    """
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Client Reply Fix Test" + " " * 32 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        success1 = test_bot_replies_to_client_on_incoming_channel()
        success2 = test_bot_without_channel_config()
        success3 = test_bot_replies_on_weather_channel()
        
        print()
        print("=" * 70)
        if success1 and success2 and success3:
            print("✅ ALL TESTS PASSED")
            print()
            print("The fix is working correctly!")
            print("Bot now replies to clients on the channel where they sent the message.")
            print("This works for both bots with and without --channel configuration.")
            print("Clients will see the bot's responses.")
        else:
            print("❌ SOME TESTS FAILED")
            if not success1:
                print("  • Bot with --channel on channel_idx 0 not working correctly")
            if not success2:
                print("  • Bot without --channel not working correctly")
            if not success3:
                print("  • Bot with --channel on channel_idx 1 not working correctly")
        print("=" * 70)
        print()
        
        return 0 if (success1 and success2 and success3) else 1
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
