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
    Test that bot with configured channel uses that channel for replies,
    not the incoming channel_idx.
    """
    print("=" * 70)
    print("TEST: Configured Channel Priority")
    print("=" * 70)
    print()
    print("Scenario: Bot started with --channel weather")
    print("  - Receives message on channel_idx 0")
    print("  - Should reply on 'weather' channel (configured)")
    print("  - Not on channel_idx 0 (incoming)")
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
    
    # Expected: Bot should use configured channel 'weather', not incoming channel_idx 0
    expected_channel = "weather"
    
    if channel_used == expected_channel:
        print("✅ PASS: Bot correctly replied on configured channel 'weather'")
        print()
        return True
    else:
        print("❌ FAIL: Bot should reply on configured channel 'weather'")
        print(f"  Expected: channel='weather'")
        print(f"  Got: channel={channel_used}, channel_idx={channel_idx_used}")
        print()
        print("This is the issue from the problem statement!")
        print()
        return False


def main():
    """Run the test"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Configured Channel Priority Test" + " " * 21 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        success = test_configured_channel_priority()
        
        print("=" * 70)
        if success:
            print("✅ TEST PASSED")
            print()
            print("The bot correctly uses the configured channel for replies,")
            print("ignoring the incoming channel_idx.")
        else:
            print("❌ TEST FAILED")
            print()
            print("The bot is using the incoming channel_idx instead of the")
            print("configured channel. This matches the problem statement.")
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
