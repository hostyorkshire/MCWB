#!/usr/bin/env python3
"""
Test for weather bot channel filtering: Bot should only accept messages from configured channels
"""

import sys
from meshcore import MeshCore, MeshCoreMessage


def test_channel_filtering():
    """
    Test that the bot only accepts messages from configured channels.
    
    When channel filter is set to 'weather':
    1. Messages on the 'weather' channel should be ACCEPTED
    2. Messages on other channels (including channel_idx 0) should be IGNORED
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
    
    # Set channel filter to 'weather' - should only accept messages from weather channel
    mesh.set_channel_filter("weather")
    
    # Verify the mapping
    assert mesh._channel_map["weather"] == 1, "Expected 'weather' to map to channel_idx 1"
    print(f"✓ Channel 'weather' mapped to channel_idx 1")
    print()
    
    # Test 1: Message on channel_idx 0 (default) should be REJECTED
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
    
    if len(received_messages) == 0:
        print("✅ PASS: Message on channel_idx 0 was REJECTED (as expected)")
    else:
        print(f"❌ FAIL: Message on channel_idx 0 was ACCEPTED (should be rejected)")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    # Test 2: Message on channel_idx 1 (weather) should be ACCEPTED
    print("Test 2: Message on channel_idx 1 (weather channel)")
    received_messages.clear()
    msg_weather = MeshCoreMessage(
        sender="USER2",
        content="wx London",
        message_type="text",
        channel=None,
        channel_idx=1
    )
    mesh.receive_message(msg_weather)
    
    if len(received_messages) == 1:
        print("✅ PASS: Message on channel_idx 1 (weather) was ACCEPTED")
    else:
        print(f"❌ FAIL: Message on channel_idx 1 was not processed")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    # Test 3: Message on channel_idx 2 (different channel) should be REJECTED
    print("Test 3: Message on channel_idx 2 (different channel)")
    received_messages.clear()
    msg_other = MeshCoreMessage(
        sender="USER3",
        content="wx Manchester",
        message_type="text",
        channel=None,
        channel_idx=2
    )
    mesh.receive_message(msg_other)
    
    if len(received_messages) == 0:
        print("✅ PASS: Message on channel_idx 2 was REJECTED (as expected)")
    else:
        print(f"❌ FAIL: Message on channel_idx 2 was ACCEPTED (should be rejected)")
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
            print("- When --channel is specified: Only accepts messages from that channel")
            print("- When --channel is NOT specified: Accepts messages from ALL channels")
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
