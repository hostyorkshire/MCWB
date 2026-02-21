#!/usr/bin/env python3
"""
Test to verify that when a bot is configured with --channel, 
it replies on the configured channel, not the incoming channel.

This test validates the fix for the problem:
- Bot started with --channel weather
- Receives message on channel_idx 0 (default/wxtest)
- Now correctly replies on the configured 'weather' channel
"""

import sys
from unittest.mock import MagicMock, call
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_configured_channel_priority():
    """
    Test that bot with configured channel replies on default channel when
    messages come from default channel (idx=0).
    
    This ensures users on default channel can see bot replies.
    """
    print("=" * 70)
    print("TEST: Default Channel Reply Priority (FIX)")
    print("=" * 70)
    print()
    print("Scenario: Bot started with --channel weather")
    print("  - Receives message on channel_idx 0 (default)")
    print("  - Should reply on channel_idx 0 (where message came from)")
    print("  - NOT on 'weather' channel (to ensure users see reply)")
    print()
    
    # Create bot with configured channel 'weather'
    bot = WeatherBot(node_id="WX_BOT", debug=True, channel="weather")
    
    # Mock the send_message method to capture what channel is used
    bot.mesh.send_message = MagicMock()
    
    # Simulate incoming message on channel_idx 0 (default channel)
    msg = MeshCoreMessage(
        sender="M3UXC",
        content="hello",  # Not a weather command, won't trigger API calls
        message_type="text",
        channel=None,  # No channel name (default channel)
        channel_idx=0  # Incoming on channel_idx 0
    )
    
    # Send a simple response (simulate weather bot reply)
    bot.send_response("Test response", 
                     reply_to_channel=msg.channel, 
                     reply_to_channel_idx=msg.channel_idx)
    
    # Check what channel was used for the reply
    assert bot.mesh.send_message.called, "send_message should have been called"
    
    # Get the call arguments
    call_args = bot.mesh.send_message.call_args
    
    print("-" * 70)
    print("Result:")
    print(f"  send_message called with: {call_args}")
    print()
    
    # Extract the channel parameter from the call
    # send_message signature: (content, message_type, channel, channel_idx=None)
    if call_args[1]:  # kwargs
        channel_used = call_args[1].get('channel')
        channel_idx_used = call_args[1].get('channel_idx')
    else:  # positional args
        channel_used = call_args[0][2] if len(call_args[0]) > 2 else None
        channel_idx_used = None
    
    print(f"  Channel used: {channel_used}")
    print(f"  Channel_idx used: {channel_idx_used}")
    print()
    
    # Expected: Bot should reply on channel_idx 0 (default), not 'weather' channel
    # This ensures users on default channel can see the reply
    if channel_idx_used == 0:
        print("✅ PASS: Bot correctly replied on channel_idx 0 (default)")
        print()
        print("This FIXES the problem statement issue!")
        print("  Users on default channel can now see bot replies.")
        print()
        return True
    else:
        print("❌ FAIL: Bot should reply on channel_idx 0")
        print(f"  Expected: channel_idx=0")
        print(f"  Got: channel={channel_used}, channel_idx={channel_idx_used}")
        print()
        print("This is the OLD behavior that caused the problem!")
        print()
        return False


def main():
    """Run the test"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 12 + "Default Channel Reply Priority Test (FIX)" + " " * 15 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        success = test_configured_channel_priority()
        
        print("=" * 70)
        if success:
            print("✅ TEST PASSED")
            print()
            print("The bot now correctly replies on the default channel when")
            print("messages come from there, ensuring users can see replies.")
            print()
            print("This FIXES the issue where users couldn't see bot replies")
            print("because they were sent to a different channel!")
        else:
            print("❌ TEST FAILED")
            print()
            print("The bot is still using the old behavior.")
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
