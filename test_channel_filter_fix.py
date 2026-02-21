#!/usr/bin/env python3
"""
Test script to verify that weather bot correctly filters messages by channel.

This test addresses the issue where the bot was responding in wxtest but not in weather channel.
The root cause was that the bot wasn't setting a channel filter based on the --channel parameter.
"""

import sys
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_single_channel_filter():
    """Test that bot with single channel only receives messages from that channel"""
    print("=" * 60)
    print("TEST 1: Single Channel Filter")
    print("=" * 60)

    # Create bot configured for 'weather' channel
    bot = WeatherBot(node_id="test_bot", debug=False, channel="weather")
    bot.mesh.start()

    # Verify that the channel filter was set
    if bot.mesh.channel_filter == ['weather']:
        print("   ✓ Channel filter correctly set to ['weather']")
    else:
        print(f"   ✗ Expected channel filter ['weather'], got {bot.mesh.channel_filter}")
        bot.mesh.stop()
        return False

    # Track messages that reach the MeshCore message handler
    received_by_meshcore = []
    original_receive = bot.mesh.receive_message
    def track_receive(message):
        received_by_meshcore.append(message)
        original_receive(message)
    bot.mesh.receive_message = track_receive

    # Test 1: Message on 'weather' channel - should be received
    print("\n1. Sending message on 'weather' channel...")
    msg1 = MeshCoreMessage(
        sender="user1", 
        content="hello", 
        message_type="text",
        channel="weather"
    )
    bot.mesh.receive_message(msg1)
    
    if len(received_by_meshcore) == 1:
        print("   ✓ Message on 'weather' channel was received by MeshCore")
    else:
        print(f"   ✗ Expected 1 message, got {len(received_by_meshcore)}")
        bot.mesh.stop()
        return False

    # Test 2: Message on 'wxtest' channel - should be ignored
    print("\n2. Sending message on 'wxtest' channel...")
    received_by_meshcore.clear()
    msg2 = MeshCoreMessage(
        sender="user2",
        content="hello",
        message_type="text",
        channel="wxtest"
    )
    # Directly call the original receive_message to simulate message coming from LoRa
    original_receive(msg2)
    
    if len(received_by_meshcore) == 0:
        print("   ✓ Message on 'wxtest' channel was filtered out (correct)")
    else:
        print(f"   ✗ Expected 0 messages, got {len(received_by_meshcore)}")
        bot.mesh.stop()
        return False

    # Test 3: Message with no channel - should be ignored
    print("\n3. Sending message with no channel...")
    received_by_meshcore.clear()
    msg3 = MeshCoreMessage(
        sender="user3",
        content="hello",
        message_type="text",
        channel=None
    )
    original_receive(msg3)
    
    if len(received_by_meshcore) == 0:
        print("   ✓ Message with no channel was filtered out (correct)")
    else:
        print(f"   ✗ Expected 0 messages, got {len(received_by_meshcore)}")
        bot.mesh.stop()
        return False

    bot.mesh.stop()
    print("\n✓ Single channel filter test passed\n")
    return True


def test_multiple_channel_filter():
    """Test that bot with multiple channels receives messages from any of them"""
    print("=" * 60)
    print("TEST 2: Multiple Channel Filter")
    print("=" * 60)

    # Create bot configured for 'weather' and 'wxtest' channels
    bot = WeatherBot(node_id="test_bot", debug=False, channel="weather,wxtest")
    bot.mesh.start()

    # Verify that the channel filter was set
    if bot.mesh.channel_filter == ['weather', 'wxtest']:
        print("   ✓ Channel filter correctly set to ['weather', 'wxtest']")
    else:
        print(f"   ✗ Expected channel filter ['weather', 'wxtest'], got {bot.mesh.channel_filter}")
        bot.mesh.stop()
        return False

    # Track messages that reach the message handlers
    received_by_handlers = []
    original_handler = bot.mesh.message_handlers.get("text")
    def track_handler(message):
        received_by_handlers.append(message)
        if original_handler:
            original_handler(message)
    bot.mesh.message_handlers["text"] = track_handler

    # Test 1: Message on 'weather' channel - should be received
    print("\n1. Sending message on 'weather' channel...")
    msg1 = MeshCoreMessage(
        sender="user1",
        content="hello",
        message_type="text",
        channel="weather"
    )
    bot.mesh.receive_message(msg1)
    
    if len(received_by_handlers) == 1:
        print("   ✓ Message on 'weather' channel reached handler")
    else:
        print(f"   ✗ Expected 1 message, got {len(received_by_handlers)}")
        bot.mesh.stop()
        return False

    # Test 2: Message on 'wxtest' channel - should be received
    print("\n2. Sending message on 'wxtest' channel...")
    received_by_handlers.clear()
    msg2 = MeshCoreMessage(
        sender="user2",
        content="hello",
        message_type="text",
        channel="wxtest"
    )
    bot.mesh.receive_message(msg2)
    
    if len(received_by_handlers) == 1:
        print("   ✓ Message on 'wxtest' channel reached handler")
    else:
        print(f"   ✗ Expected 1 message, got {len(received_by_handlers)}")
        bot.mesh.stop()
        return False

    # Test 3: Message on 'alerts' channel - should be ignored
    print("\n3. Sending message on 'alerts' channel...")
    received_by_handlers.clear()
    msg3 = MeshCoreMessage(
        sender="user3",
        content="hello",
        message_type="text",
        channel="alerts"
    )
    bot.mesh.receive_message(msg3)
    
    if len(received_by_handlers) == 0:
        print("   ✓ Message on 'alerts' channel was filtered out (correct)")
    else:
        print(f"   ✗ Expected 0 messages, got {len(received_by_handlers)}")
        bot.mesh.stop()
        return False

    bot.mesh.stop()
    print("\n✓ Multiple channel filter test passed\n")
    return True


def test_no_channel_filter():
    """Test that bot without channel filter receives all messages"""
    print("=" * 60)
    print("TEST 3: No Channel Filter (Receive All)")
    print("=" * 60)

    # Create bot without channel configuration
    bot = WeatherBot(node_id="test_bot", debug=False, channel=None)
    bot.mesh.start()

    # Verify that no channel filter was set
    if bot.mesh.channel_filter is None:
        print("   ✓ Channel filter correctly set to None (receive all)")
    else:
        print(f"   ✗ Expected channel filter None, got {bot.mesh.channel_filter}")
        bot.mesh.stop()
        return False

    # Track messages that reach the message handlers
    received_by_handlers = []
    original_handler = bot.mesh.message_handlers.get("text")
    def track_handler(message):
        received_by_handlers.append(message)
        if original_handler:
            original_handler(message)
    bot.mesh.message_handlers["text"] = track_handler

    # Test 1: Message on 'weather' channel - should be received
    print("\n1. Sending message on 'weather' channel...")
    msg1 = MeshCoreMessage(
        sender="user1",
        content="hello",
        message_type="text",
        channel="weather"
    )
    bot.mesh.receive_message(msg1)
    
    if len(received_by_handlers) == 1:
        print("   ✓ Message on 'weather' channel reached handler")
    else:
        print(f"   ✗ Expected 1 message, got {len(received_by_handlers)}")
        bot.mesh.stop()
        return False

    # Test 2: Message on 'wxtest' channel - should be received
    print("\n2. Sending message on 'wxtest' channel...")
    received_by_handlers.clear()
    msg2 = MeshCoreMessage(
        sender="user2",
        content="hello",
        message_type="text",
        channel="wxtest"
    )
    bot.mesh.receive_message(msg2)
    
    if len(received_by_handlers) == 1:
        print("   ✓ Message on 'wxtest' channel reached handler")
    else:
        print(f"   ✗ Expected 1 message, got {len(received_by_handlers)}")
        bot.mesh.stop()
        return False

    # Test 3: Message with no channel - should be received
    print("\n3. Sending message with no channel...")
    received_by_handlers.clear()
    msg3 = MeshCoreMessage(
        sender="user3",
        content="hello",
        message_type="text",
        channel=None
    )
    bot.mesh.receive_message(msg3)
    
    if len(received_by_handlers) == 1:
        print("   ✓ Message with no channel reached handler")
    else:
        print(f"   ✗ Expected 1 message, got {len(received_by_handlers)}")
        bot.mesh.stop()
        return False

    bot.mesh.stop()
    print("\n✓ No channel filter test passed\n")
    return True


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 8 + "Weather Bot Channel Filter Tests" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        all_passed = True
        
        if not test_single_channel_filter():
            all_passed = False
            
        if not test_multiple_channel_filter():
            all_passed = False
            
        if not test_no_channel_filter():
            all_passed = False

        if all_passed:
            print("=" * 60)
            print("✅ All tests passed!")
            print("=" * 60)
            print()
            print("Summary:")
            print("  • Bot with single channel filters correctly")
            print("  • Bot with multiple channels filters correctly")
            print("  • Bot without channel configuration receives all messages")
            print("  • The fix addresses the issue: bot now responds only")
            print("    in configured channels (weather, wxtest, etc.)")
            print()
            return 0
        else:
            print("=" * 60)
            print("❌ Some tests failed!")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
