#!/usr/bin/env python3
"""
Test to verify that messages on the default channel (channel_idx 0) 
are accepted when a channel filter is set.

This tests the fix for the issue where the bot was ignoring messages
because they arrived on channel_idx 0 (channel=None) and the filter
was set to a specific channel like 'wxtest' or 'weather'.
"""

import sys
from meshcore import MeshCore, MeshCoreMessage


def test_default_channel_with_filter():
    """
    Test that messages on default channel (idx 0) are accepted when filter is set.
    
    Scenario from problem statement:
    - Bot started with --channel wxtest
    - User sends "Wx leeds" which arrives on channel_idx 0
    - Message should be accepted (not ignored)
    """
    print("=" * 70)
    print("TEST: Default Channel with Filter")
    print("=" * 70)
    print()
    
    # Create mesh with channel filter
    mesh = MeshCore("test_bot", debug=True)
    mesh.set_channel_filter("wxtest")
    
    # Track received messages
    received_messages = []
    
    def handler(msg):
        received_messages.append(msg.content)
    
    mesh.register_handler("text", handler)
    mesh.start()
    
    # Test 1: Message on default channel (channel_idx 0, channel=None)
    # This simulates the actual scenario from the logs
    print("\nTest 1: Message on default channel (idx=0, channel=None)")
    print("  Simulating: LoRa RX channel msg from M3UXC on channel_idx 0: Wx leeds")
    msg1 = MeshCoreMessage(
        sender="M3UXC",
        content="Wx leeds",
        message_type="text",
        channel=None,
        channel_idx=0
    )
    mesh.receive_message(msg1)
    
    # Test 2: Message on non-default channel that doesn't match filter
    # This should still be ignored
    print("\nTest 2: Message on non-matching channel (idx=2, channel='weather')")
    msg2 = MeshCoreMessage(
        sender="M3UXC",
        content="Wx london",
        message_type="text",
        channel="weather",
        channel_idx=2
    )
    mesh.receive_message(msg2)
    
    # Test 3: Message on matching channel
    print("\nTest 3: Message on matching channel (idx=1, channel='wxtest')")
    msg3 = MeshCoreMessage(
        sender="M3UXC",
        content="Wx york",
        message_type="text",
        channel="wxtest",
        channel_idx=1
    )
    mesh.receive_message(msg3)
    
    # Test 4: Edge case - message with channel_idx=0 but channel set to non-None
    # This shouldn't happen in normal operation, but test the edge case
    print("\nTest 4: Edge case - channel_idx=0 with channel='other'")
    msg4 = MeshCoreMessage(
        sender="M3UXC",
        content="Wx test",
        message_type="text",
        channel="other",
        channel_idx=0
    )
    mesh.receive_message(msg4)
    
    mesh.stop()
    
    # Verify results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Messages received: {received_messages}")
    print()
    
    # Should have received messages from test 1 and test 3
    assert len(received_messages) == 2, f"Expected 2 messages, got {len(received_messages)}"
    assert "Wx leeds" in received_messages, "Message from default channel not received"
    assert "Wx york" in received_messages, "Message from matching channel not received"
    assert "Wx london" not in received_messages, "Message from non-matching channel should be ignored"
    assert "Wx test" not in received_messages, "Edge case message (idx=0, channel='other') should be ignored"
    
    print("✅ TEST PASSED")
    print("  - Message on default channel (idx 0, channel=None) was accepted")
    print("  - Message on matching channel was accepted")
    print("  - Message on non-matching channel was correctly ignored")
    print("  - Edge case (idx=0, channel='other') was correctly ignored")
    print()
    
    return True


def test_multiple_scenarios():
    """Test multiple channel filter scenarios"""
    print("=" * 70)
    print("TEST: Multiple Channel Filter Scenarios")
    print("=" * 70)
    print()
    
    # Structure: (filter, messages_to_receive, messages_to_ignore)
    # Each message is a tuple of (content, channel, channel_idx)
    scenarios = [
        (
            "weather",
            [("Wx leeds", None, 0)],  # Default channel should be accepted
            [("Wx london", "wxtest", 1)]  # Non-matching channel should be ignored
        ),
        (
            "wxtest",
            [("Wx york", None, 0)],  # Default channel should be accepted
            [("Wx paris", "weather", 2)]  # Non-matching channel should be ignored
        ),
        (
            ["weather", "wxtest"],
            [
                ("Wx berlin", None, 0),  # Default channel should be accepted
                ("Wx madrid", "weather", 2)  # Matching channel should be accepted
            ],
            [("Wx rome", "alerts", 3)]  # Non-matching channel should be ignored
        ),
    ]
    
    for filter_channels, should_receive, should_ignore in scenarios:
        filter_str = ",".join(filter_channels) if isinstance(filter_channels, list) else filter_channels
        print(f"\nScenario: Channel filter = '{filter_str}'")
        # Enable debug for multi-channel scenario
        debug = isinstance(filter_channels, list)
        mesh = MeshCore("test_bot", debug=debug)
        mesh.set_channel_filter(filter_channels)
        
        received = []
        mesh.register_handler("text", lambda msg: received.append(msg.content))
        mesh.start()
        
        # Send messages that should be received
        for content, channel, channel_idx in should_receive:
            msg = MeshCoreMessage("user", content, "text", channel=channel, channel_idx=channel_idx)
            mesh.receive_message(msg)
        
        # Send messages that should be ignored
        for content, channel, channel_idx in should_ignore:
            msg = MeshCoreMessage("user", content, "text", channel=channel, channel_idx=channel_idx)
            mesh.receive_message(msg)
        
        mesh.stop()
        
        assert len(received) == len(should_receive), \
            f"Expected {len(should_receive)} messages, got {len(received)}"
        print(f"  ✅ Received {len(received)} messages as expected")
    
    print("\n✅ ALL SCENARIOS PASSED")
    print()
    return True


def main():
    """Run all tests"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Default Channel Filter Test" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        test_default_channel_with_filter()
        test_multiple_scenarios()
        
        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("  • Messages on default channel (idx 0) are now accepted")
        print("  • Channel filter still works for non-default channels")
        print("  • Bot will now reply to messages on any channel_idx 0")
        print()
        return 0
    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
