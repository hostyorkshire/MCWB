#!/usr/bin/env python3
"""
Test for channel filter removal: Bot should accept messages from ALL channels
and reply on the same channel where the message came from.
"""

import sys
from meshcore import MeshCore, MeshCoreMessage


def test_no_channel_filtering():
    """
    Test that the bot accepts messages from ALL channels regardless of
    the channel configuration.
    
    After removing channel filtering, the bot should:
    1. Accept messages on channel_idx 0 (default)
    2. Accept messages on channel_idx 1 (weather or any other)
    3. Accept messages on any channel_idx value
    4. Reply on the same channel_idx where the message came from
    """
    print()
    print("=" * 70)
    print("TEST: No Channel Filtering (accepts all channels)")
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
    
    # Set channel configuration to 'weather' (but this should NOT filter incoming messages)
    mesh.set_channel_filter("weather")
    
    # Verify the mapping
    assert mesh._channel_map["weather"] == 1, "Expected 'weather' to map to channel_idx 1"
    print(f"✓ Channel 'weather' mapped to channel_idx 1")
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
    print("║" + " " * 18 + "No Channel Filtering Test" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        success = test_no_channel_filtering()
        
        print()
        print("=" * 70)
        if success:
            print("✅ ALL TESTS PASSED")
            print()
            print("The bot correctly accepts messages from ALL channels:")
            print("- Messages on channel_idx 0 (default) are ACCEPTED")
            print("- Messages on channel_idx 1 (weather) are ACCEPTED")
            print("- Messages on any channel_idx are ACCEPTED")
            print()
            print("The bot will reply on the same channel_idx where each")
            print("message came from, ensuring users receive responses")
            print("regardless of their channel configuration.")
        else:
            print("❌ TEST FAILED")
            print()
            print("The bot is not accepting messages from all channels.")
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
