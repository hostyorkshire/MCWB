#!/usr/bin/env python3
"""
Test script to verify multi-channel broadcast functionality for weather bot.
Tests the feature requested in the problem statement:
"can this bot only transmit to one channel? I tested with wxtest channel 
but would like it to run on weather channel in meshcore"
"""

import sys
from unittest.mock import MagicMock
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_single_channel():
    """Test bot with single channel (original behavior)"""
    print("=" * 60)
    print("TEST: Single Channel Broadcast")
    print("=" * 60)
    
    bot = WeatherBot(node_id="test_bot", debug=False, channel="weather")
    
    # Verify channels are parsed correctly
    assert bot.channels == ["weather"], f"Expected ['weather'], got {bot.channels}"
    print("✓ Bot initialized with single channel: 'weather'")
    
    # Mock the mesh send_message to capture calls
    sent_messages = []
    
    def mock_send(content, msg_type, channel):
        sent_messages.append({"content": content, "type": msg_type, "channel": channel})
        return MeshCoreMessage(bot.mesh.node_id, content, msg_type, channel=channel)
    
    bot.mesh.send_message = mock_send
    
    # Send a response
    bot.send_response("Test weather message")
    
    # Verify message was sent to the correct channel
    assert len(sent_messages) == 1, f"Expected 1 message, got {len(sent_messages)}"
    assert sent_messages[0]["channel"] == "weather", f"Expected 'weather' channel"
    print("✓ Message sent to 'weather' channel")
    print()


def test_multiple_channels():
    """Test bot with multiple channels (new feature)"""
    print("=" * 60)
    print("TEST: Multiple Channel Broadcast")
    print("=" * 60)
    
    # Test with two channels as requested in problem statement
    bot = WeatherBot(node_id="test_bot", debug=False, channel="weather,wxtest")
    
    # Verify channels are parsed correctly
    assert bot.channels == ["weather", "wxtest"], f"Expected ['weather', 'wxtest'], got {bot.channels}"
    print("✓ Bot initialized with multiple channels: 'weather', 'wxtest'")
    
    # Mock the mesh send_message to capture calls
    sent_messages = []
    
    def mock_send(content, msg_type, channel):
        sent_messages.append({"content": content, "type": msg_type, "channel": channel})
        return MeshCoreMessage(bot.mesh.node_id, content, msg_type, channel=channel)
    
    bot.mesh.send_message = mock_send
    
    # Send a response
    bot.send_response("Test weather message")
    
    # Verify message was sent to both channels
    assert len(sent_messages) == 2, f"Expected 2 messages, got {len(sent_messages)}"
    
    channels_sent = [msg["channel"] for msg in sent_messages]
    assert "weather" in channels_sent, "Expected message on 'weather' channel"
    assert "wxtest" in channels_sent, "Expected message on 'wxtest' channel"
    
    print("✓ Message broadcast to both 'weather' and 'wxtest' channels")
    print()


def test_multiple_channels_with_spaces():
    """Test bot with multiple channels with spaces around commas"""
    print("=" * 60)
    print("TEST: Multiple Channels with Spacing")
    print("=" * 60)
    
    # Test with spaces around commas
    bot = WeatherBot(node_id="test_bot", debug=False, channel="weather, wxtest, alerts")
    
    # Verify channels are parsed correctly (spaces should be stripped)
    assert bot.channels == ["weather", "wxtest", "alerts"], f"Expected ['weather', 'wxtest', 'alerts'], got {bot.channels}"
    print("✓ Bot correctly parses channels with spaces: 'weather, wxtest, alerts'")
    
    # Mock the mesh send_message to capture calls
    sent_messages = []
    
    def mock_send(content, msg_type, channel):
        sent_messages.append({"content": content, "type": msg_type, "channel": channel})
        return MeshCoreMessage(bot.mesh.node_id, content, msg_type, channel=channel)
    
    bot.mesh.send_message = mock_send
    
    # Send a response
    bot.send_response("Test weather message")
    
    # Verify message was sent to all three channels
    assert len(sent_messages) == 3, f"Expected 3 messages, got {len(sent_messages)}"
    
    channels_sent = [msg["channel"] for msg in sent_messages]
    assert "weather" in channels_sent, "Expected message on 'weather' channel"
    assert "wxtest" in channels_sent, "Expected message on 'wxtest' channel"
    assert "alerts" in channels_sent, "Expected message on 'alerts' channel"
    
    print("✓ Message broadcast to all 3 channels: 'weather', 'wxtest', 'alerts'")
    print()


def test_empty_channel_names():
    """Test bot with empty channel names in input"""
    print("=" * 60)
    print("TEST: Empty Channel Names Handling")
    print("=" * 60)
    
    # Test with empty channel names (should be filtered out with warning)
    bot = WeatherBot(node_id="test_bot", debug=True, channel="weather,,,wxtest")
    
    # Verify only valid channels are kept
    assert bot.channels == ["weather", "wxtest"], f"Expected ['weather', 'wxtest'], got {bot.channels}"
    print("✓ Bot correctly filters out empty channel names from 'weather,,,wxtest'")
    print("✓ Warning should have been logged about empty channel names")
    print()


def test_no_channel():
    """Test bot without channel (broadcast to all)"""
    print("=" * 60)
    print("TEST: No Channel (Broadcast to All)")
    print("=" * 60)
    
    bot = WeatherBot(node_id="test_bot", debug=False, channel=None)
    
    # Verify no channels are set
    assert bot.channels == [], f"Expected empty list, got {bot.channels}"
    print("✓ Bot initialized without channels (broadcast mode)")
    
    # Mock the mesh send_message to capture calls
    sent_messages = []
    
    def mock_send(content, msg_type, channel):
        sent_messages.append({"content": content, "type": msg_type, "channel": channel})
        return MeshCoreMessage(bot.mesh.node_id, content, msg_type, channel=channel)
    
    bot.mesh.send_message = mock_send
    
    # Send a response
    bot.send_response("Test weather message")
    
    # Verify message was sent without a channel
    assert len(sent_messages) == 1, f"Expected 1 message, got {len(sent_messages)}"
    assert sent_messages[0]["channel"] is None, f"Expected no channel, got {sent_messages[0]['channel']}"
    print("✓ Message broadcast without channel (to all)")
    print()


def test_problem_statement_scenario():
    """
    Test the exact scenario from the problem statement:
    User wants to use both 'wxtest' and 'weather' channels
    """
    print("=" * 60)
    print("TEST: Problem Statement Scenario")
    print("=" * 60)
    print("User request: 'tested with wxtest channel but would like it")
    print("              to run on weather channel in meshcore'")
    print()
    
    # Create bot with both channels as requested
    bot = WeatherBot(node_id="weather_bot", debug=False, channel="wxtest,weather")
    
    print(f"✓ Bot created with channels: {bot.channels}")
    
    # Mock the mesh send_message to capture calls
    sent_messages = []
    
    def mock_send(content, msg_type, channel):
        sent_messages.append({"content": content, "type": msg_type, "channel": channel})
        return MeshCoreMessage(bot.mesh.node_id, content, msg_type, channel=channel)
    
    bot.mesh.send_message = mock_send
    
    # Simulate a weather request
    msg = MeshCoreMessage(
        sender="user",
        content="wx London",
        message_type="text"
    )
    
    # Mock the weather API calls
    bot.geocode_location = lambda loc: {
        "name": "London",
        "country": "GB",
        "latitude": 51.5074,
        "longitude": -0.1278
    }
    
    bot.get_weather = lambda lat, lon: {
        "current": {
            "temperature_2m": 15.5,
            "apparent_temperature": 14.2,
            "relative_humidity_2m": 70,
            "wind_speed_10m": 10.5,
            "wind_direction_10m": 180,
            "precipitation": 0.0,
            "weather_code": 1
        }
    }
    
    # Process the weather request directly without starting the event loop
    bot.handle_message(msg)
    
    # Verify message was broadcast to both channels
    assert len(sent_messages) == 2, f"Expected 2 messages (one per channel), got {len(sent_messages)}"
    
    channels_sent = [msg["channel"] for msg in sent_messages]
    assert "wxtest" in channels_sent, "Expected message on 'wxtest' channel"
    assert "weather" in channels_sent, "Expected message on 'weather' channel"
    
    print("✓ Weather response broadcast to both 'wxtest' and 'weather' channels")
    print("✓ Bot now supports multiple channels as requested!")
    print()


def main():
    """Run all multi-channel tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Multi-Channel Broadcast Tests" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_single_channel()
        test_multiple_channels()
        test_multiple_channels_with_spaces()
        test_empty_channel_names()
        test_no_channel()
        test_problem_statement_scenario()

        print("=" * 60)
        print("✅ All multi-channel tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  • Bot can broadcast to a single channel")
        print("  • Bot can broadcast to multiple channels simultaneously")
        print("  • Channel list accepts comma-separated values")
        print("  • Whitespace around commas is handled correctly")
        print("  • Empty channel names are filtered out with warning")
        print("  • Bot can still broadcast without channels (to all)")
        print()
        print("Usage examples:")
        print("  # Single channel:")
        print("  python3 weather_bot.py --channel weather --interactive")
        print()
        print("  # Multiple channels (solves the problem statement):")
        print("  python3 weather_bot.py --channel weather,wxtest --interactive")
        print()
        print("  # Multiple channels with spaces:")
        print("  python3 weather_bot.py --channel 'weather, wxtest, alerts' --interactive")
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
