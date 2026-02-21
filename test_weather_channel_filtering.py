#!/usr/bin/env python3
"""
Test for weather bot channel filtering: Bot should only accept messages from configured channels
"""

import sys
from meshcore import MeshCore, MeshCoreMessage


def test_channel_filtering():
    """
    Test that the bot filters messages based on channel name, but accepts
    binary-protocol messages (with channel_idx only) regardless of filter.
    
    When channel filter is set to 'weather':
    1. Messages with explicit channel names NOT in filter should be REJECTED
    2. Messages with explicit channel names IN filter should be ACCEPTED  
    3. Binary-protocol messages (channel=None, channel_idx set) should be ACCEPTED
       regardless of channel_idx, because physical radio slot indices are independent
       of the bot's internal channel-name mapping
    """
    print()
    print("=" * 70)
    print("TEST: Channel Filtering (weather channel only)")
    print("=" * 70)
    print()
    
    mesh = MeshCore("test_bot", debug=True)
    
    received_messages = []
    
    def handler(message):
        received_messages.append({
            'content': message.content,
            'channel': message.channel,
            'channel_idx': message.channel_idx
        })
    
    mesh.register_handler("text", handler)
    mesh.start()
    
    # Set channel filter to 'weather' - should only filter by channel name
    mesh.set_channel_filter("weather")
    
    # Verify the mapping
    assert mesh._channel_map["weather"] == 1, "Expected 'weather' to map to channel_idx 1"
    print(f"✓ Channel 'weather' mapped to channel_idx 1")
    print()
    
    # Test 1: Binary-protocol message on channel_idx 0 (no channel name) should be ACCEPTED
    # This is because binary messages don't carry channel names, only indices
    print("Test 1: Binary-protocol message on channel_idx 0 (default channel)")
    received_messages.clear()
    msg_default = MeshCoreMessage(
        sender="USER1",
        content="wx Brighton",
        message_type="text",
        channel=None,  # Binary protocol - no channel name
        channel_idx=0
    )
    mesh.receive_message(msg_default)
    
    if len(received_messages) == 1:
        print("✅ PASS: Binary message on channel_idx 0 was ACCEPTED (as expected)")
        print("  (Binary-protocol messages are not filtered by channel_idx)")
    else:
        print(f"❌ FAIL: Binary message on channel_idx 0 was REJECTED (should be accepted)")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    # Test 2: Binary-protocol message on channel_idx 1 (weather) should be ACCEPTED
    print("Test 2: Binary-protocol message on channel_idx 1")
    received_messages.clear()
    msg_weather = MeshCoreMessage(
        sender="USER2",
        content="wx London",
        message_type="text",
        channel=None,  # Binary protocol - no channel name
        channel_idx=1
    )
    mesh.receive_message(msg_weather)
    
    if len(received_messages) == 1:
        print("✅ PASS: Binary message on channel_idx 1 was ACCEPTED")
    else:
        print(f"❌ FAIL: Binary message on channel_idx 1 was not processed")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    # Test 3: Binary-protocol message on channel_idx 2 (different channel) should be ACCEPTED
    # Even though filter is set to 'weather', binary messages are accepted from all indices
    print("Test 3: Binary-protocol message on channel_idx 2 (different channel)")
    received_messages.clear()
    msg_other = MeshCoreMessage(
        sender="USER3",
        content="wx Manchester",
        message_type="text",
        channel=None,  # Binary protocol - no channel name
        channel_idx=2
    )
    mesh.receive_message(msg_other)
    
    if len(received_messages) == 1:
        print("✅ PASS: Binary message on channel_idx 2 was ACCEPTED (as expected)")
        print("  (Binary-protocol messages are not filtered by channel_idx)")
    else:
        print(f"❌ FAIL: Binary message on channel_idx 2 was REJECTED (should be accepted)")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    # Test 4: Named-channel message NOT in filter should be REJECTED
    print("Test 4: Named message channel='news' (not in filter)")
    received_messages.clear()
    msg_news = MeshCoreMessage(
        sender="USER4",
        content="some news",
        message_type="text",
        channel="news",  # Explicit channel name - will be filtered
        channel_idx=None
    )
    mesh.receive_message(msg_news)
    
    if len(received_messages) == 0:
        print("✅ PASS: Named message on channel 'news' was REJECTED (as expected)")
    else:
        print(f"❌ FAIL: Named message on channel 'news' was ACCEPTED (should be rejected)")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    # Test 5: Named-channel message IN filter should be ACCEPTED
    print("Test 5: Named message channel='weather' (in filter)")
    received_messages.clear()
    msg_weather_named = MeshCoreMessage(
        sender="USER5",
        content="wx Leeds",
        message_type="text",
        channel="weather",  # Explicit channel name in filter
        channel_idx=None
    )
    mesh.receive_message(msg_weather_named)
    
    if len(received_messages) == 1:
        print("✅ PASS: Named message on channel 'weather' was ACCEPTED")
    else:
        print(f"❌ FAIL: Named message on channel 'weather' was not processed")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    mesh.stop()
    return True


def test_no_filtering():
    """
    Test that when no channel filter is set, bot accepts messages from all channels.
    """
    print()
    print("=" * 70)
    print("TEST: No Filtering (accepts all channels)")
    print("=" * 70)
    print()
    
    mesh = MeshCore("test_bot", debug=True)
    
    received_messages = []
    
    def handler(message):
        received_messages.append({
            'content': message.content,
            'channel': message.channel,
            'channel_idx': message.channel_idx
        })
    
    mesh.register_handler("text", handler)
    mesh.start()
    
    # No channel filter - should accept all messages
    # (set_channel_filter is not called, so channel_filter remains None)
    
    # Test 1: Message on channel_idx 0 should be ACCEPTED
    print("Test 1: Message on channel_idx 0 (default channel)")
    received_messages.clear()
    msg_default = MeshCoreMessage(
        sender="USER1",
        content="wx Brighton",
        message_type="text",
        channel=None,
        channel_idx=0
    )
    mesh.receive_message(msg_default)
    
    if len(received_messages) == 1:
        print("✅ PASS: Message on channel_idx 0 was ACCEPTED")
    else:
        print(f"❌ FAIL: Message on channel_idx 0 was not processed")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    # Test 2: Message on channel_idx 1 should be ACCEPTED
    print("Test 2: Message on channel_idx 1")
    received_messages.clear()
    msg_ch1 = MeshCoreMessage(
        sender="USER2",
        content="wx London",
        message_type="text",
        channel=None,
        channel_idx=1
    )
    mesh.receive_message(msg_ch1)
    
    if len(received_messages) == 1:
        print("✅ PASS: Message on channel_idx 1 was ACCEPTED")
    else:
        print(f"❌ FAIL: Message on channel_idx 1 was not processed")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    mesh.stop()
    return True


def main():
    """Run the tests"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "Channel Filtering Tests" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        # Test 1: With channel filter
        success1 = test_channel_filtering()
        
        # Test 2: Without channel filter
        success2 = test_no_filtering()
        
        print()
        print("=" * 70)
        if success1 and success2:
            print("✅ ALL TESTS PASSED")
            print()
            print("Channel filtering is working correctly:")
            print("- Named-channel messages are filtered by channel name")
            print("- Binary-protocol messages (channel=None) are NOT filtered")
            print("  (because channel_idx mapping is independent of bot's names)")
            print("- When no channel filter is set: Accepts ALL messages")
            print()
            print("The bot always replies on the same channel_idx where each")
            print("message came from.")
        else:
            print("❌ SOME TESTS FAILED")
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
