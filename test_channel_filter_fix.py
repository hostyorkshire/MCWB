#!/usr/bin/env python3
"""
Test for channel filter fix: Bot with --channel weather should only process
messages on the 'weather' channel (channel_idx 1), not on default channel (channel_idx 0)
"""

import sys
from meshcore import MeshCore, MeshCoreMessage


def test_channel_filter_with_channel_idx():
    """
    Test that when a channel filter is set, only messages on the filtered
    channel's channel_idx are processed, not messages on other channel_idx values.
    
    This reproduces the bug from the problem statement where a bot with
    --channel weather processes messages on channel_idx 0 (default) when it
    should only process messages on channel_idx 1 (weather).
    """
    print()
    print("=" * 70)
    print("TEST: Channel Filter with channel_idx")
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
    
    # Set channel filter to 'weather' (this maps to channel_idx 1)
    mesh.set_channel_filter("weather")
    
    # Verify the mapping
    assert mesh._channel_map["weather"] == 1, "Expected 'weather' to map to channel_idx 1"
    print(f"✓ Channel 'weather' mapped to channel_idx 1")
    print()
    
    # Test 1: Message on channel_idx 0 (default) should be IGNORED
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
        print("✅ PASS: Message on channel_idx 0 was correctly IGNORED")
    else:
        print(f"❌ FAIL: Message on channel_idx 0 was processed (should be ignored)")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    # Test 2: Message on channel_idx 1 (weather) should be PROCESSED
    print("Test 2: Message on channel_idx 1 (weather channel)")
    received_messages.clear()
    msg_weather = MeshCoreMessage(
        sender="USER2",
        content="wx London",
        message_type="text",
        channel=None,  # No channel name set (from LoRa)
        channel_idx=1   # But channel_idx is 1 (mapped to 'weather')
    )
    mesh.receive_message(msg_weather)
    
    if len(received_messages) == 1:
        print("✅ PASS: Message on channel_idx 1 was correctly PROCESSED")
    else:
        print(f"❌ FAIL: Message on channel_idx 1 was not processed (should be processed)")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    # Test 3: Message on channel_idx 2 (different channel) should be IGNORED
    print("Test 3: Message on channel_idx 2 (different channel)")
    received_messages.clear()
    msg_other = MeshCoreMessage(
        sender="USER3",
        content="some message",
        message_type="text",
        channel=None,
        channel_idx=2
    )
    mesh.receive_message(msg_other)
    
    if len(received_messages) == 0:
        print("✅ PASS: Message on channel_idx 2 was correctly IGNORED")
    else:
        print(f"❌ FAIL: Message on channel_idx 2 was processed (should be ignored)")
        print(f"  Received: {received_messages}")
        return False
    print()
    
    mesh.stop()
    return True


def main():
    """Run the test"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "Channel Filter Fix Test" + " " * 27 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        success = test_channel_filter_with_channel_idx()
        
        print()
        print("=" * 70)
        if success:
            print("✅ ALL TESTS PASSED")
            print()
            print("The bot correctly filters messages by channel_idx:")
            print("- Messages on channel_idx 0 (default) are IGNORED")
            print("- Messages on channel_idx 1 (weather) are PROCESSED")
            print("- Messages on other channel_idx values are IGNORED")
        else:
            print("❌ TEST FAILED")
            print()
            print("The bot is not correctly filtering by channel_idx.")
            print("This is the bug described in the problem statement:")
            print("- Bot with --channel weather should only process channel_idx 1")
            print("- But it's also processing channel_idx 0 (default)")
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
