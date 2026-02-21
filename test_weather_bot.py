#!/usr/bin/env python3
"""
Test script for MeshCore Weather Bot
Demonstrates the bot's functionality with mock data when API is not accessible
"""

import sys
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_command_parsing():
    """Test weather command parsing"""
    print("=" * 60)
    print("TEST 1: Command Parsing")
    print("=" * 60)

    bot = WeatherBot(debug=False)

    test_cases = [
        ("wx London", "London"),
        ("weather Manchester", "Manchester"),
        ("WX York", "York"),
        ("WEATHER Leeds", "Leeds"),
        ("wx  Birmingham  ", "Birmingham"),
        ("hello", None),
        ("wx", None),
        ("weather", None),
    ]

    for command, expected in test_cases:
        result = bot.parse_weather_command(command)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{command}' -> {result} (expected: {expected})")

    print()


def test_weather_code_descriptions():
    """Test weather code to description conversion"""
    print("=" * 60)
    print("TEST 2: Weather Code Descriptions")
    print("=" * 60)

    bot = WeatherBot(debug=False)

    test_codes = [0, 1, 2, 3, 45, 51, 61, 63, 71, 80, 95]

    for code in test_codes:
        description = bot.get_weather_description(code)
        print(f"Code {code:2d}: {description}")

    print()


def test_weather_formatting():
    """Test weather response formatting"""
    print("=" * 60)
    print("TEST 3: Weather Response Formatting")
    print("=" * 60)

    bot = WeatherBot(debug=False)

    # Mock location data
    location_data = {
        "name": "London",
        "country": "GB",
        "latitude": 51.5074,
        "longitude": -0.1278
    }

    # Mock weather data
    weather_data = {
        "current": {
            "temperature_2m": 12.5,
            "apparent_temperature": 11.2,
            "relative_humidity_2m": 75,
            "wind_speed_10m": 15.3,
            "wind_direction_10m": 230,
            "precipitation": 0.0,
            "weather_code": 2
        }
    }

    response = bot.format_weather_response(location_data, weather_data)
    print(response)
    print()


def test_message_handling():
    """Test message handling"""
    print("=" * 60)
    print("TEST 4: Message Handling")
    print("=" * 60)

    bot = WeatherBot(debug=True)
    bot.start()

    # Test with a weather command (will fail due to network, but shows handling)
    MeshCoreMessage(
        sender="test_user",
        content="wx London",
        message_type="text"
    )

    print("\nProcessing: 'wx London'")
    print("-" * 40)
    # Note: This will fail with network error in sandbox, but shows the flow

    bot.stop()
    print()


def test_meshcore_integration():
    """Test MeshCore integration"""
    print("=" * 60)
    print("TEST 5: MeshCore Integration")
    print("=" * 60)

    from meshcore import MeshCore

    # Test basic MeshCore functionality
    mesh = MeshCore("test_node", debug=True)

    print("\nStarting MeshCore...")
    mesh.start()

    print("\nSending test message...")
    msg = mesh.send_message("Test weather request", "text")

    print("\nSimulating message reception...")

    def test_handler(message):
        print(f"Handler received: {message.content}")

    mesh.register_handler("text", test_handler)
    mesh.receive_message(msg)

    print("\nStopping MeshCore...")
    mesh.stop()
    print()


def test_reply_channel():
    """Test reply channel functionality"""
    print("=" * 60)
    print("TEST 6: Reply Channel Logic")
    print("=" * 60)

    from unittest.mock import MagicMock, patch

    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding and weather responses
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{"name": "York", "country": "UK", "latitude": 53.9, "longitude": -1.1}]
        }
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {"temperature_2m": 10, "apparent_temperature": 8, "relative_humidity_2m": 70,
                       "wind_speed_10m": 12, "wind_direction_10m": 180, "precipitation": 0, "weather_code": 1}
        }
        mock_get.side_effect = [geocoding_response, weather_response]

        # Create bot (no channel parameter - accepts all channels)
        bot = WeatherBot(node_id="test_bot", debug=False)
        
        # Track sent messages
        sent_messages = []
        original_send = bot.mesh.send_message
        def track_send(content, message_type, channel, channel_idx=None):
            sent_messages.append({'channel': channel, 'channel_idx': channel_idx})
            return original_send(content, message_type, channel, channel_idx)
        bot.mesh.send_message = track_send
        bot.mesh.start()

        # Test 1: Message from default channel (idx=0) - bot should reply on same channel
        print("\n1. Message from default channel (idx=0):")
        msg = MeshCoreMessage(sender="user", content="wx york", message_type="text", channel=None, channel_idx=0)
        sent_messages.clear()
        bot.handle_message(msg)
        # Bot replies on the channel where message came from to ensure user sees response
        assert len(sent_messages) == 1
        assert sent_messages[0]['channel_idx'] == 0, f"Expected channel_idx=0, got {sent_messages[0]['channel_idx']}"
        print("   ✓ Bot replied on channel_idx 0 (where message came from)")

        # Test 2: Message from named channel - bot should reply on same channel_idx
        mock_get.side_effect = [geocoding_response, weather_response]
        print("\n2. Message from channel_idx 1:")
        msg = MeshCoreMessage(sender="user", content="wx york", message_type="text", channel="weather", channel_idx=1)
        sent_messages.clear()
        bot.handle_message(msg)
        assert len(sent_messages) == 1 and sent_messages[0]['channel_idx'] == 1
        print("   ✓ Bot replied on channel_idx 1 (where message came from)")

        bot.mesh.stop()
    
    # Test bot WITHOUT configured channel - should reply on incoming channel
    print("\n3. Bot WITHOUT configured channel (default behavior):")
    with patch('weather_bot.requests.get') as mock_get:
        mock_get.side_effect = [geocoding_response, weather_response]
        bot_no_channel = WeatherBot(node_id="test_bot", debug=False)
        
        sent_messages = []
        original_send = bot_no_channel.mesh.send_message
        def track_send(content, message_type, channel, channel_idx=None):
            sent_messages.append({'channel': channel, 'channel_idx': channel_idx})
            return original_send(content, message_type, channel, channel_idx)
        bot_no_channel.mesh.send_message = track_send
        bot_no_channel.mesh.start()
        
        msg = MeshCoreMessage(sender="user", content="wx york", message_type="text", channel=None, channel_idx=2)
        sent_messages.clear()
        bot_no_channel.handle_message(msg)
        assert len(sent_messages) == 1
        assert sent_messages[0]['channel_idx'] == 2, f"Expected channel_idx=2, got {sent_messages[0]['channel_idx']}"
        print("   ✓ Bot replied on channel_idx 2 (where message came from)")
        
        bot_no_channel.mesh.stop()
    print()


def test_announcement():
    """Test periodic announcement functionality"""
    print("=" * 60)
    print("TEST 7: Periodic Announcement")
    print("=" * 60)

    from weather_bot import ANNOUNCE_MESSAGE, ANNOUNCE_INTERVAL

    # Verify constants
    assert ANNOUNCE_INTERVAL == 3 * 60 * 60, "ANNOUNCE_INTERVAL should be 3 hours"
    assert "WX" in ANNOUNCE_MESSAGE, "Announcement should mention WX command"
    print(f"  Announcement message: {ANNOUNCE_MESSAGE}")
    print(f"  Announcement interval: {ANNOUNCE_INTERVAL}s ({ANNOUNCE_INTERVAL // 3600}h)")

    # Test send_announcement sends to the configured announce_channel
    bot = WeatherBot(node_id="test_bot", debug=False, announce_channel="wxtest")
    bot.mesh.start()

    sent_messages = []
    original_send = bot.mesh.send_message
    def track_send(content, message_type, channel, channel_idx=None):
        sent_messages.append({"content": content, "channel": channel})
        return original_send(content, message_type, channel, channel_idx)
    bot.mesh.send_message = track_send

    bot.send_announcement()
    assert len(sent_messages) == 1, "Announcement should send exactly one message"
    assert sent_messages[0]["channel"] == "wxtest", f"Expected channel 'wxtest', got '{sent_messages[0]['channel']}'"
    assert sent_messages[0]["content"] == ANNOUNCE_MESSAGE, "Announcement content mismatch"
    print("  ✓ Announcement sent to 'wxtest' channel with correct message")

    # Test that announcement is suppressed when announce_channel is None
    bot_no_announce = WeatherBot(node_id="test_bot2", debug=False, announce_channel=None)
    bot_no_announce.mesh.start()
    no_announce_messages = []
    original_send2 = bot_no_announce.mesh.send_message
    def track_send2(content, message_type, channel, channel_idx=None):
        no_announce_messages.append({"content": content, "channel": channel})
        return original_send2(content, message_type, channel, channel_idx)
    bot_no_announce.mesh.send_message = track_send2
    bot_no_announce.send_announcement()
    assert len(no_announce_messages) == 0, "No announcement should be sent when announce_channel is None"
    print("  ✓ Announcement suppressed when announce_channel is None")

    bot.mesh.stop()
    bot_no_announce.mesh.stop()
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "MCWB - MeshCore Weather Bot Tests" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_command_parsing()
        test_weather_code_descriptions()
        test_weather_formatting()
        test_meshcore_integration()
        test_reply_channel()
        test_announcement()

        print("=" * 60)
        print("All component tests completed!")
        print("=" * 60)
        print()
        print("Note: Full API integration tests require network access.")
        print("To test with real API:")
        print("  python3 weather_bot.py --location 'London'")
        print("  python3 weather_bot.py --interactive")
        print()

        return 0

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
