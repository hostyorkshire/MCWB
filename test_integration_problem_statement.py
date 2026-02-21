#!/usr/bin/env python3
"""
Integration test that validates the specific scenario from the problem statement.

This test simulates the exact issue reported:
- Bot started with --channel wxtest receives messages on wxtest
- Bot started with --channel weather receives messages on weather
- Bot correctly filters out messages from other channels
"""

import sys
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_problem_statement_scenario():
    """
    Test the exact scenario from the problem statement:
    'the bot is now responding in the wxtest channel but is not responding in the weather channel'
    
    Expected behavior after fix:
    - Bot with --channel wxtest should ONLY respond to wxtest messages
    - Bot with --channel weather should ONLY respond to weather messages
    """
    print("=" * 70)
    print("INTEGRATION TEST: Problem Statement Scenario")
    print("=" * 70)
    print()
    print("Problem: Bot was responding in wxtest but not in weather channel")
    print("Root Cause: --channel parameter didn't filter incoming messages")
    print("Fix: Bot now filters messages by configured channel(s)")
    print()
    
    # Track which messages are processed by checking the handler
    def create_tracking_bot(channel):
        """Create a bot with message tracking"""
        bot = WeatherBot(node_id="WX_BOT", debug=False, channel=channel)
        
        tracked = []
        original_text_handler = bot.mesh.message_handlers.get("text")
        
        def tracking_handler(msg):
            tracked.append(msg.channel)
            if original_text_handler:
                original_text_handler(msg)
        
        bot.mesh.message_handlers["text"] = tracking_handler
        bot.mesh.start()
        
        return bot, tracked
    
    # Test 1: Bot configured for wxtest channel
    print("-" * 70)
    print("TEST 1: Bot with --channel wxtest")
    print("-" * 70)
    
    bot_wxtest, tracked_wxtest = create_tracking_bot("wxtest")
    
    # Simulate message on wxtest channel (should be received)
    msg1 = MeshCoreMessage(
        sender="M3UXC",
        content="hello",  # Use simple message to avoid API calls
        message_type="text",
        channel="wxtest",
        channel_idx=1
    )
    bot_wxtest.mesh.receive_message(msg1)
    
    # Simulate message on weather channel (should be ignored)
    msg2 = MeshCoreMessage(
        sender="M3UXC",
        content="hello",
        message_type="text",
        channel="weather",
        channel_idx=2
    )
    bot_wxtest.mesh.receive_message(msg2)
    
    bot_wxtest.mesh.stop()
    
    # Verify results for wxtest bot
    assert tracked_wxtest == ['wxtest'], f"Expected ['wxtest'], got {tracked_wxtest}"
    print("✅ Bot with --channel wxtest correctly:")
    print("   - Received message from 'wxtest' channel")
    print("   - Ignored message from 'weather' channel")
    print()
    
    # Test 2: Bot configured for weather channel
    print("-" * 70)
    print("TEST 2: Bot with --channel weather")
    print("-" * 70)
    
    bot_weather, tracked_weather = create_tracking_bot("weather")
    
    # Simulate message on wxtest channel (should be ignored)
    msg3 = MeshCoreMessage(
        sender="M3UXC",
        content="hello",
        message_type="text",
        channel="wxtest",
        channel_idx=1
    )
    bot_weather.mesh.receive_message(msg3)
    
    # Simulate message on weather channel (should be received)
    msg4 = MeshCoreMessage(
        sender="M3UXC",
        content="hello",
        message_type="text",
        channel="weather",
        channel_idx=2
    )
    bot_weather.mesh.receive_message(msg4)
    
    bot_weather.mesh.stop()
    
    # Verify results for weather bot
    assert tracked_weather == ['weather'], f"Expected ['weather'], got {tracked_weather}"
    print("✅ Bot with --channel weather correctly:")
    print("   - Ignored message from 'wxtest' channel")
    print("   - Received message from 'weather' channel")
    print()
    
    # Test 3: Verify channel filtering is bidirectional
    print("-" * 70)
    print("TEST 3: Multi-channel bot (weather,wxtest)")
    print("-" * 70)
    
    bot_multi, tracked_multi = create_tracking_bot("weather,wxtest")
    
    # Simulate messages on both configured channels (should be received)
    for channel, idx in [('weather', 2), ('wxtest', 1)]:
        msg = MeshCoreMessage(
            sender="M3UXC",
            content="hello",
            message_type="text",
            channel=channel,
            channel_idx=idx
        )
        bot_multi.mesh.receive_message(msg)
    
    # Simulate message on non-configured channel (should be ignored)
    msg_other = MeshCoreMessage(
        sender="M3UXC",
        content="hello",
        message_type="text",
        channel="alerts",
        channel_idx=3
    )
    bot_multi.mesh.receive_message(msg_other)
    
    bot_multi.mesh.stop()
    
    # Verify results
    assert set(tracked_multi) == {'weather', 'wxtest'}, f"Expected {{'weather', 'wxtest'}}, got {set(tracked_multi)}"
    print("✅ Bot with --channel weather,wxtest correctly:")
    print("   - Received message from 'weather' channel")
    print("   - Received message from 'wxtest' channel")
    print("   - Ignored message from 'alerts' channel")
    print()
    
    return True


def main():
    """Run the integration test"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "Problem Statement Integration Test" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        if test_problem_statement_scenario():
            print("=" * 70)
            print("✅ INTEGRATION TEST PASSED")
            print("=" * 70)
            print()
            print("Summary:")
            print("  • Bot with --channel wxtest now correctly filters messages")
            print("  • Bot with --channel weather now correctly filters messages")
            print("  • Multi-channel bots work correctly")
            print("  • The problem statement issue is RESOLVED")
            print()
            print("The fix ensures that:")
            print("  1. Bot started with --channel weather ONLY responds in weather")
            print("  2. Bot started with --channel wxtest ONLY responds in wxtest")
            print("  3. Bot can be configured for multiple channels if needed")
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
