#!/usr/bin/env python3
"""
Test to verify that when a message comes from default channel (idx=0),
the bot replies on default channel (idx=0), even when configured with --channel.

This ensures users on default channel can see bot replies.
"""

import sys
from unittest.mock import MagicMock, patch
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_default_channel_reply_priority():
    """
    Test that messages from default channel (idx=0) get replies on default channel (idx=0),
    even when bot is configured with --channel weather.
    """
    print("=" * 70)
    print("TEST: Default Channel Reply Priority")
    print("=" * 70)
    print()
    print("Scenario: Bot started with --channel weather")
    print("  - Receives message on channel_idx 0 (default)")
    print("  - Should reply on channel_idx 0 (where message came from)")
    print("  - NOT on 'weather' channel (configured)")
    print()
    
    # Create bot with configured channel 'weather'
    bot = WeatherBot(node_id="WX_BOT", debug=True, channel="weather")
    
    # Track what channel is used for replies
    sent_messages = []
    
    def track_send(content, message_type, channel, channel_idx=None):
        sent_messages.append({
            'content': content,
            'channel': channel,
            'channel_idx': channel_idx
        })
        # Return a mock message
        return MeshCoreMessage(sender="WX_BOT", content=content, message_type=message_type)
    
    bot.mesh.send_message = track_send
    
    # Simulate incoming message on channel_idx 0 (default channel)
    msg = MeshCoreMessage(
        sender="M3UXC",
        content="test message",
        message_type="text",
        channel=None,  # No channel name (default channel)
        channel_idx=0  # Incoming on channel_idx 0
    )
    
    print("Simulating message:")
    print(f"  From: {msg.sender}")
    print(f"  Content: {msg.content}")
    print(f"  Channel: {msg.channel}")
    print(f"  Channel_idx: {msg.channel_idx}")
    print()
    
    # Send a response
    sent_messages.clear()
    bot.send_response("Test response", 
                     reply_to_channel=msg.channel, 
                     reply_to_channel_idx=msg.channel_idx)
    
    # Check what channel was used
    print("-" * 70)
    print("Result:")
    assert len(sent_messages) == 1, f"Expected 1 message, got {len(sent_messages)}"
    
    sent = sent_messages[0]
    print(f"  Channel used: {sent['channel']}")
    print(f"  Channel_idx used: {sent['channel_idx']}")
    print()
    
    # Expected: Bot should reply on channel_idx 0 (default), not 'weather'
    if sent['channel_idx'] == 0:
        print("✅ PASS: Bot correctly replied on channel_idx 0 (default)")
        print()
        print("This ensures users on default channel see the reply!")
        return True
    else:
        print("❌ FAIL: Bot should reply on channel_idx 0")
        print(f"  Expected: channel_idx=0")
        print(f"  Got: channel={sent['channel']}, channel_idx={sent['channel_idx']}")
        print()
        print("Users on default channel won't see the reply!")
        return False


def test_configured_channel_still_works():
    """
    Test that messages from configured channels still get replies on configured channels.
    """
    print()
    print("=" * 70)
    print("TEST: Configured Channel Still Works")
    print("=" * 70)
    print()
    print("Scenario: Bot started with --channel weather")
    print("  - Receives message on channel_idx 1 (weather channel)")
    print("  - Should reply on 'weather' channel (configured)")
    print()
    
    # Create bot with configured channel 'weather'
    bot = WeatherBot(node_id="WX_BOT", debug=True, channel="weather")
    
    # Track what channel is used for replies
    sent_messages = []
    
    def track_send(content, message_type, channel, channel_idx=None):
        sent_messages.append({
            'content': content,
            'channel': channel,
            'channel_idx': channel_idx
        })
        return MeshCoreMessage(sender="WX_BOT", content=content, message_type=message_type)
    
    bot.mesh.send_message = track_send
    
    # Simulate incoming message on channel_idx 1 (weather channel)
    msg = MeshCoreMessage(
        sender="M3UXC",
        content="test message",
        message_type="text",
        channel="weather",  # Weather channel
        channel_idx=1  # Incoming on channel_idx 1
    )
    
    print("Simulating message:")
    print(f"  From: {msg.sender}")
    print(f"  Content: {msg.content}")
    print(f"  Channel: {msg.channel}")
    print(f"  Channel_idx: {msg.channel_idx}")
    print()
    
    # Send a response
    sent_messages.clear()
    bot.send_response("Test response", 
                     reply_to_channel=msg.channel, 
                     reply_to_channel_idx=msg.channel_idx)
    
    # Check what channel was used
    print("-" * 70)
    print("Result:")
    assert len(sent_messages) == 1, f"Expected 1 message, got {len(sent_messages)}"
    
    sent = sent_messages[0]
    print(f"  Channel used: {sent['channel']}")
    print(f"  Channel_idx used: {sent['channel_idx']}")
    print()
    
    # Expected: Bot should reply on 'weather' channel
    if sent['channel'] == 'weather':
        print("✅ PASS: Bot correctly replied on 'weather' channel")
        print()
        print("Dedicated service mode still works!")
        return True
    else:
        print("❌ FAIL: Bot should reply on 'weather' channel")
        print(f"  Expected: channel='weather'")
        print(f"  Got: channel={sent['channel']}, channel_idx={sent['channel_idx']}")
        return False


def main():
    """Run the tests"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "Default Channel Reply Fix Test" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        test1_success = test_default_channel_reply_priority()
        test2_success = test_configured_channel_still_works()
        
        print()
        print("=" * 70)
        if test1_success and test2_success:
            print("✅ ALL TESTS PASSED")
            print()
            print("The bot now:")
            print("  1. Replies on default channel (idx=0) for messages from there")
            print("  2. Replies on configured channels for messages from those channels")
            print()
            print("This ensures users on any channel can see bot replies!")
        else:
            print("❌ SOME TESTS FAILED")
            if not test1_success:
                print("  - Default channel reply failed")
            if not test2_success:
                print("  - Configured channel reply failed")
        print("=" * 70)
        print()
        
        return 0 if (test1_success and test2_success) else 1
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
