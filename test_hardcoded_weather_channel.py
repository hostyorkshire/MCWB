#!/usr/bin/env python3
"""
Test that the weather bot is hardcoded to ONLY work on the weather channel
"""

import sys
from meshcore import MeshCore, MeshCoreMessage
from weather_bot import WeatherBot


def test_weather_bot_channel_filtering():
    """
    Test that the WeatherBot is hardcoded to only accept messages from the 'weather' channel.
    
    The bot should:
    1. REJECT messages on channel_idx 0 (default channel)
    2. ACCEPT messages on channel_idx 1 (weather channel)
    3. REJECT messages on any other channel_idx value
    """
    print()
    print("=" * 70)
    print("TEST: Weather Bot Hardcoded to Weather Channel Only")
    print("=" * 70)
    print()
    
    # Create the weather bot
    bot = WeatherBot(node_id="test_weather_bot", debug=True)
    bot.start()
    
    # Track which messages were processed
    processed_messages = []
    original_send = bot.send_response
    
    def track_send(content, **kwargs):
        processed_messages.append(content)
        original_send(content, **kwargs)
    
    bot.send_response = track_send
    
    # Test 1: Message on channel_idx 0 (default channel) should be REJECTED
    print("Test 1: Message on channel_idx 0 (default channel)")
    processed_messages.clear()
    msg_default = MeshCoreMessage(
        sender="USER1",
        content="wx Brighton",
        message_type="text",
        channel=None,
        channel_idx=0
    )
    bot.mesh.receive_message(msg_default)
    
    if len(processed_messages) == 0:
        print("✅ PASS: Message on channel_idx 0 was REJECTED (as expected)")
    else:
        print(f"❌ FAIL: Message on channel_idx 0 was ACCEPTED (should be rejected)")
        print(f"  Processed: {processed_messages}")
        bot.stop()
        return False
    print()
    
    # Test 2: Message on channel_idx 1 (weather) should be ACCEPTED
    print("Test 2: Message on channel_idx 1 (weather channel)")
    processed_messages.clear()
    msg_weather = MeshCoreMessage(
        sender="USER2",
        content="wx London",
        message_type="text",
        channel=None,
        channel_idx=1
    )
    bot.mesh.receive_message(msg_weather)
    
    # Should have processed the message (but API call would fail in test, which is ok)
    if len(processed_messages) > 0:
        print("✅ PASS: Message on channel_idx 1 (weather) was ACCEPTED")
    else:
        print(f"❌ FAIL: Message on channel_idx 1 was not processed")
        print(f"  Processed: {processed_messages}")
        bot.stop()
        return False
    print()
    
    # Test 3: Message on channel_idx 2 (different channel) should be REJECTED
    print("Test 3: Message on channel_idx 2 (different channel)")
    processed_messages.clear()
    msg_other = MeshCoreMessage(
        sender="USER3",
        content="wx Manchester",
        message_type="text",
        channel=None,
        channel_idx=2
    )
    bot.mesh.receive_message(msg_other)
    
    if len(processed_messages) == 0:
        print("✅ PASS: Message on channel_idx 2 was REJECTED (as expected)")
    else:
        print(f"❌ FAIL: Message on channel_idx 2 was ACCEPTED (should be rejected)")
        print(f"  Processed: {processed_messages}")
        bot.stop()
        return False
    print()
    
    bot.stop()
    return True


def main():
    """Run the test"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Weather Bot Hardcoded Channel Test" + " " * 19 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        success = test_weather_bot_channel_filtering()
        
        print()
        print("=" * 70)
        if success:
            print("✅ TEST PASSED")
            print()
            print("Weather bot is correctly hardcoded to ONLY accept messages")
            print("from the 'weather' channel (channel_idx 1).")
            print()
            print("Messages from other channels are ignored.")
        else:
            print("❌ TEST FAILED")
            print()
            print("Weather bot is not correctly filtering channels.")
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
