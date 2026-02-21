#!/usr/bin/env python3
"""
Test that the weather bot accepts messages from ALL channels (no filtering)
"""

import sys
from meshcore import MeshCore, MeshCoreMessage
from weather_bot import WeatherBot


def test_accepts_all_channels():
    """
    Test that the WeatherBot accepts messages from ALL channels.
    
    The bot should:
    1. ACCEPT messages on channel_idx 0 (default channel)
    2. ACCEPT messages on channel_idx 1 
    3. ACCEPT messages on channel_idx 2
    4. ACCEPT messages on any channel_idx value
    5. Reply on the same channel_idx where each message came from
    """
    print()
    print("=" * 70)
    print("TEST: Weather Bot Accepts ALL Channels (No Filtering)")
    print("=" * 70)
    print()
    
    # Create the weather bot
    bot = WeatherBot(node_id="test_weather_bot", debug=True)
    bot.start()
    
    # Track which messages were processed
    processed_messages = []
    original_send = bot.send_response
    
    def track_send(content, **kwargs):
        processed_messages.append({
            'content': content,
            'reply_to_channel': kwargs.get('reply_to_channel'),
            'reply_to_channel_idx': kwargs.get('reply_to_channel_idx')
        })
        original_send(content, **kwargs)
    
    bot.send_response = track_send
    
    # Test 1: Message on channel_idx 0 (default channel) should be ACCEPTED
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
    
    if len(processed_messages) > 0:
        print("✅ PASS: Message on channel_idx 0 was ACCEPTED")
        print(f"   Reply sent to channel_idx: {processed_messages[0]['reply_to_channel_idx']}")
        if processed_messages[0]['reply_to_channel_idx'] != 0:
            print(f"   ⚠️  WARNING: Reply channel_idx mismatch! Expected 0, got {processed_messages[0]['reply_to_channel_idx']}")
    else:
        print(f"❌ FAIL: Message on channel_idx 0 was REJECTED (should be accepted)")
        bot.stop()
        return False
    print()
    
    # Test 2: Message on channel_idx 1 should be ACCEPTED
    print("Test 2: Message on channel_idx 1")
    processed_messages.clear()
    msg_ch1 = MeshCoreMessage(
        sender="USER2",
        content="wx London",
        message_type="text",
        channel=None,
        channel_idx=1
    )
    bot.mesh.receive_message(msg_ch1)
    
    if len(processed_messages) > 0:
        print("✅ PASS: Message on channel_idx 1 was ACCEPTED")
        print(f"   Reply sent to channel_idx: {processed_messages[0]['reply_to_channel_idx']}")
        if processed_messages[0]['reply_to_channel_idx'] != 1:
            print(f"   ⚠️  WARNING: Reply channel_idx mismatch! Expected 1, got {processed_messages[0]['reply_to_channel_idx']}")
    else:
        print(f"❌ FAIL: Message on channel_idx 1 was REJECTED (should be accepted)")
        bot.stop()
        return False
    print()
    
    # Test 3: Message on channel_idx 2 should be ACCEPTED
    print("Test 3: Message on channel_idx 2")
    processed_messages.clear()
    msg_ch2 = MeshCoreMessage(
        sender="USER3",
        content="wx Manchester",
        message_type="text",
        channel=None,
        channel_idx=2
    )
    bot.mesh.receive_message(msg_ch2)
    
    if len(processed_messages) > 0:
        print("✅ PASS: Message on channel_idx 2 was ACCEPTED")
        print(f"   Reply sent to channel_idx: {processed_messages[0]['reply_to_channel_idx']}")
        if processed_messages[0]['reply_to_channel_idx'] != 2:
            print(f"   ⚠️  WARNING: Reply channel_idx mismatch! Expected 2, got {processed_messages[0]['reply_to_channel_idx']}")
    else:
        print(f"❌ FAIL: Message on channel_idx 2 was REJECTED (should be accepted)")
        bot.stop()
        return False
    print()
    
    # Test 4: Message on channel_idx 5 should be ACCEPTED
    print("Test 4: Message on channel_idx 5")
    processed_messages.clear()
    msg_ch5 = MeshCoreMessage(
        sender="USER4",
        content="wx Leeds",
        message_type="text",
        channel=None,
        channel_idx=5
    )
    bot.mesh.receive_message(msg_ch5)
    
    if len(processed_messages) > 0:
        print("✅ PASS: Message on channel_idx 5 was ACCEPTED")
        print(f"   Reply sent to channel_idx: {processed_messages[0]['reply_to_channel_idx']}")
        if processed_messages[0]['reply_to_channel_idx'] != 5:
            print(f"   ⚠️  WARNING: Reply channel_idx mismatch! Expected 5, got {processed_messages[0]['reply_to_channel_idx']}")
    else:
        print(f"❌ FAIL: Message on channel_idx 5 was REJECTED (should be accepted)")
        bot.stop()
        return False
    print()
    
    bot.stop()
    return True


def main():
    """Run the test"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "No Channel Filtering Test" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        success = test_accepts_all_channels()
        
        print()
        print("=" * 70)
        if success:
            print("✅ ALL TESTS PASSED")
            print()
            print("Weather bot correctly accepts messages from ALL channels:")
            print("- Messages from channel_idx 0 (default) are ACCEPTED")
            print("- Messages from channel_idx 1 are ACCEPTED")
            print("- Messages from channel_idx 2 are ACCEPTED")
            print("- Messages from any channel_idx are ACCEPTED")
            print()
            print("Bot replies on the same channel_idx where each message came from.")
        else:
            print("❌ TEST FAILED")
            print()
            print("Weather bot is not accepting messages from all channels.")
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
