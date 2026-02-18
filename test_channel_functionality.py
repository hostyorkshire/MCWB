#!/usr/bin/env python3
"""
Test script for MeshCore Channel functionality
Tests channel broadcasting and filtering
"""

import sys
from meshcore import MeshCore, MeshCoreMessage


def test_message_with_channel():
    """Test creating messages with channel"""
    print("=" * 60)
    print("TEST 1: Message with Channel")
    print("=" * 60)
    
    # Create message without channel
    msg1 = MeshCoreMessage("node1", "Hello", "text")
    assert msg1.channel is None
    print("✓ Message without channel: channel is None")
    
    # Create message with channel
    msg2 = MeshCoreMessage("node1", "Hello", "text", channel="weather")
    assert msg2.channel == "weather"
    print("✓ Message with channel: channel is 'weather'")
    
    # Test to_dict
    dict1 = msg1.to_dict()
    assert "channel" not in dict1
    print("✓ to_dict without channel: 'channel' key not present")
    
    dict2 = msg2.to_dict()
    assert "channel" in dict2
    assert dict2["channel"] == "weather"
    print("✓ to_dict with channel: 'channel' key is 'weather'")
    
    # Test from_dict
    msg3 = MeshCoreMessage.from_dict({"sender": "node2", "content": "Test", "channel": "news"})
    assert msg3.channel == "news"
    print("✓ from_dict with channel: channel is 'news'")
    
    msg4 = MeshCoreMessage.from_dict({"sender": "node2", "content": "Test"})
    assert msg4.channel is None
    print("✓ from_dict without channel: channel is None")
    
    print()


def test_send_message_with_channel():
    """Test sending messages with channel"""
    print("=" * 60)
    print("TEST 2: Send Message with Channel")
    print("=" * 60)
    
    mesh = MeshCore("test_node", debug=False)
    mesh.start()
    
    # Send without channel
    msg1 = mesh.send_message("Test message", "text")
    assert msg1.channel is None
    print("✓ send_message without channel: message has no channel")
    
    # Send with channel
    msg2 = mesh.send_message("Weather update", "text", channel="weather")
    assert msg2.channel == "weather"
    print("✓ send_message with channel: message has 'weather' channel")
    
    mesh.stop()
    print()


def test_channel_filtering():
    """Test channel filtering on receive"""
    print("=" * 60)
    print("TEST 3: Channel Filtering")
    print("=" * 60)
    
    mesh = MeshCore("test_node", debug=False)
    
    received_messages = []
    
    def handler(message):
        received_messages.append(message.content)
    
    mesh.register_handler("text", handler)
    mesh.start()
    
    # Create test messages
    msg_no_channel = MeshCoreMessage("sender", "No channel", "text")
    msg_weather = MeshCoreMessage("sender", "Weather channel", "text", channel="weather")
    msg_news = MeshCoreMessage("sender", "News channel", "text", channel="news")
    
    # Test 1: No filter - all messages received
    received_messages.clear()
    mesh.receive_message(msg_no_channel)
    mesh.receive_message(msg_weather)
    mesh.receive_message(msg_news)
    assert len(received_messages) == 3
    print("✓ No filter: received 3/3 messages")
    
    # Test 2: Filter on 'weather' channel
    received_messages.clear()
    mesh.set_channel_filter("weather")
    mesh.receive_message(msg_no_channel)  # Should be ignored
    mesh.receive_message(msg_weather)     # Should be received
    mesh.receive_message(msg_news)        # Should be ignored
    assert len(received_messages) == 1
    assert received_messages[0] == "Weather channel"
    print("✓ 'weather' filter: received 1/3 messages (only weather)")
    
    # Test 3: Filter on 'news' channel
    received_messages.clear()
    mesh.set_channel_filter("news")
    mesh.receive_message(msg_no_channel)  # Should be ignored
    mesh.receive_message(msg_weather)     # Should be ignored
    mesh.receive_message(msg_news)        # Should be received
    assert len(received_messages) == 1
    assert received_messages[0] == "News channel"
    print("✓ 'news' filter: received 1/3 messages (only news)")
    
    # Test 4: Remove filter
    received_messages.clear()
    mesh.set_channel_filter(None)
    mesh.receive_message(msg_no_channel)
    mesh.receive_message(msg_weather)
    mesh.receive_message(msg_news)
    assert len(received_messages) == 3
    print("✓ Filter removed: received 3/3 messages")
    
    mesh.stop()
    print()


def test_weather_bot_with_channel():
    """Test WeatherBot with channel support"""
    print("=" * 60)
    print("TEST 4: WeatherBot with Channel")
    print("=" * 60)
    
    from weather_bot import WeatherBot
    
    # Create bot without channel
    bot1 = WeatherBot(node_id="bot1", debug=False)
    assert bot1.channel is None
    print("✓ WeatherBot without channel: channel is None")
    
    # Create bot with channel
    bot2 = WeatherBot(node_id="bot2", debug=False, channel="weather")
    assert bot2.channel == "weather"
    print("✓ WeatherBot with channel: channel is 'weather'")
    
    print()


def test_meshcore_send_integration():
    """Test meshcore_send with channel"""
    print("=" * 60)
    print("TEST 5: meshcore_send Integration")
    print("=" * 60)
    
    from meshcore_send import send_message
    
    # Send without channel
    msg1 = send_message("sender", "Test", debug=False)
    assert msg1.channel is None
    print("✓ send_message without channel: message has no channel")
    
    # Send with channel
    msg2 = send_message("sender", "Test", channel="test", debug=False)
    assert msg2.channel == "test"
    print("✓ send_message with channel: message has 'test' channel")
    
    print()


def test_json_serialization():
    """Test JSON serialization with channel"""
    print("=" * 60)
    print("TEST 6: JSON Serialization")
    print("=" * 60)
    
    import json
    
    # Message with channel
    msg1 = MeshCoreMessage("node1", "Test", "text", channel="weather")
    json_str = msg1.to_json()
    data = json.loads(json_str)
    assert "channel" in data
    assert data["channel"] == "weather"
    print("✓ to_json with channel: includes 'channel' field")
    
    # Reconstruct from JSON
    msg2 = MeshCoreMessage.from_json(json_str)
    assert msg2.channel == "weather"
    print("✓ from_json with channel: channel preserved")
    
    # Message without channel
    msg3 = MeshCoreMessage("node1", "Test", "text")
    json_str = msg3.to_json()
    data = json.loads(json_str)
    assert "channel" not in data
    print("✓ to_json without channel: no 'channel' field")
    
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "MeshCore Channel Functionality Tests" + " " * 10 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_message_with_channel()
        test_send_message_with_channel()
        test_channel_filtering()
        test_weather_bot_with_channel()
        test_meshcore_send_integration()
        test_json_serialization()
        
        print("=" * 60)
        print("✅ All channel functionality tests passed!")
        print("=" * 60)
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
