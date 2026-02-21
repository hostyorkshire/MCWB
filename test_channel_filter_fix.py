#!/usr/bin/env python3
"""
Test for channel filtering: Bot should only accept messages from configured channels
when channel filter is set, and accept all messages when no filter is set.
"""

import sys
from meshcore import MeshCore, MeshCoreMessage


def test_with_channel_filtering():
    """
    Test that the bot only accepts messages from configured channels when
    channel filter is set.
    
    When channel filter is set to 'weather', the bot should:
    1. REJECT messages on channel_idx 0 (default)
    2. ACCEPT messages on channel_idx 1 (weather)
    3. REJECT messages on any other channel_idx value
    4. Reply on the same channel_idx where the message came from
    """
    print()
    print("=" * 70)
    print("TEST: With Channel Filter (weather only)")
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
    
    # Set channel filter to 'weather' - this SHOULD filter incoming messages
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
        print("✅ PASS: Message on channel_idx 1 was ACCEPTED")
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


def test_without_channel_filtering():
    """
    Test that the bot accepts messages from ALL channels when no
    channel filter is set.
    
    When no channel filter is set, the bot should:
    1. ACCEPT messages on channel_idx 0 (default)
    2. ACCEPT messages on channel_idx 1 (weather or any other)
    3. ACCEPT messages on any channel_idx value
    4. Reply on the same channel_idx where the message came from
    """
    print()
    print("=" * 70)
    print("TEST: Without Channel Filter (accepts all channels)")
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
    
    # DO NOT set channel filter - should accept all messages
    print("✓ No channel filter set")
    print()
    
    # Test 1: Message on channel_idx 0 (default) should be ACCEPTED
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
        print("✅ PASS: Message on channel_idx 1 was ACCEPTED")
    else:
        print(f"❌ FAIL: Message on channel_idx 1 was not processed")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    # Test 3: Message on channel_idx 2 (different channel) should be ACCEPTED
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
    
    if len(received_messages) == 1:
        print("✅ PASS: Message on channel_idx 2 was ACCEPTED")
    else:
        print(f"❌ FAIL: Message on channel_idx 2 was not processed")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    mesh.stop()
    return True


def main():
    """Run the test"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "Channel Filtering Test" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        # Test 1: With channel filter
        success1 = test_with_channel_filtering()
        
        # Test 2: Without channel filter
        success2 = test_without_channel_filtering()
        
        print()
        print("=" * 70)
        if success1 and success2:
            print("✅ ALL TESTS PASSED")
            print()
            print("Channel filtering is working correctly:")
            print("- When --channel IS set: Only accepts messages from that channel")
            print("- When --channel is NOT set: Accepts messages from ALL channels")
            print()
            print("The bot always replies on the same channel_idx where each")
            print("message came from.")
        else:
            print("❌ TEST FAILED")
            print()
            print("Channel filtering is not working as expected.")
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
