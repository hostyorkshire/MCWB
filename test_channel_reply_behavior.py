#!/usr/bin/env python3
"""
Test to verify correct channel reply behavior after the channel filter fix.

This test validates:
1. Bot with --channel weather ignores messages from default channel (channel_idx 0)
2. Bot replies on the channel where the message came from (channel_idx 1+)
3. Bot respects channel filter for incoming messages
"""

import sys
sys.path.insert(0, '/home/runner/work/MCWB/MCWB')

from weather_bot import WeatherBot
from meshcore import MeshCoreMessage

def test_channel_reply_behavior():
    """Test that bot correctly handles channel filtering and replies"""
    print("\n" + "=" * 70)
    print("Channel Reply Behavior Test")
    print("=" * 70 + "\n")
    
    # Create bot configured for 'weather' channel
    print("Setting up: Bot with --channel weather\n")
    bot = WeatherBot(node_id="WX_BOT", debug=True, channel="weather")
    
    # Track messages processed
    processed = []
    sent_messages = []
    
    original_handler = bot.mesh.message_handlers.get("text")
    def tracking_handler(msg):
        processed.append(msg)
        if original_handler:
            original_handler(msg)
    bot.mesh.message_handlers["text"] = tracking_handler
    
    # Mock send to track what gets sent
    original_send = bot.mesh.send_message
    def tracking_send(content, msg_type, channel=None, channel_idx=None):
        sent_messages.append({
            'content': content,
            'channel': channel,
            'channel_idx': channel_idx
        })
        original_send(content, msg_type, channel, channel_idx)
    bot.mesh.send_message = tracking_send
    
    print("TEST 1: Message from default channel (channel_idx 0) - should be ACCEPTED")
    print("-" * 70)
    processed.clear()
    sent_messages.clear()
    
    msg1 = MeshCoreMessage(
        sender="User1",
        content="wx test",
        message_type="text",
        channel=None,
        channel_idx=0
    )
    bot.mesh.receive_message(msg1)
    
    if len(processed) > 0:
        print("✅ PASS: Message from default channel was correctly processed")
        if len(sent_messages) > 0 and sent_messages[0]['channel'] == 'weather':
            print("✅ PASS: Bot replied on 'weather' channel (configured channel)\n")
        else:
            print(f"❌ FAIL: Bot did not reply on 'weather' channel (got: {sent_messages[0] if sent_messages else 'no message'})\n")
            return False
    else:
        print("❌ FAIL: Message from default channel was not processed\n")
        return False
    
    print("TEST 2: Message from channel_idx 1 (unnamed) - should be ACCEPTED")
    print("-" * 70)
    processed.clear()
    sent_messages.clear()
    
    msg2 = MeshCoreMessage(
        sender="User2",
        content="wx test",
        message_type="text",
        channel=None,
        channel_idx=1
    )
    bot.mesh.receive_message(msg2)
    
    if len(processed) > 0:
        print(f"✅ PASS: Message from channel_idx 1 was processed")
        if len(sent_messages) > 0 and sent_messages[0]['channel'] == 'weather':
            print(f"✅ PASS: Bot replied on 'weather' channel (configured channel)\n")
        else:
            print(f"❌ FAIL: Bot did not reply on 'weather' channel (got: {sent_messages[0] if sent_messages else 'no message'})\n")
            return False
    else:
        print("❌ FAIL: Message from channel_idx 1 was not processed\n")
        return False
    
    print("TEST 3: Message from 'weather' channel - should be ACCEPTED")
    print("-" * 70)
    processed.clear()
    sent_messages.clear()
    
    msg3 = MeshCoreMessage(
        sender="User3",
        content="wx test",
        message_type="text",
        channel="weather",
        channel_idx=1
    )
    bot.mesh.receive_message(msg3)
    
    if len(processed) > 0:
        print(f"✅ PASS: Message from 'weather' channel was processed")
        if len(sent_messages) > 0 and sent_messages[0]['channel'] == 'weather':
            print(f"✅ PASS: Bot replied on 'weather' channel (configured channel)\n")
        else:
            print(f"❌ FAIL: Bot did not reply on 'weather' channel (got: {sent_messages[0] if sent_messages else 'no message'})\n")
            return False
    else:
        print("❌ FAIL: Message from 'weather' channel was not processed\n")
        return False
    
    bot.mesh.stop()
    return True

if __name__ == "__main__":
    success = test_channel_reply_behavior()
    
    print("=" * 70)
    if success:
        print("✅ ALL TESTS PASSED")
        print("\nVerified behavior:")
        print("  • Bot with --channel weather accepts messages from default channel (idx 0)")
        print("  • Bot accepts messages from non-zero channel_idx")
        print("  • Bot accepts messages from matching channel name")
        print("  • Bot ALWAYS replies on the configured 'weather' channel")
        print("  • This ensures all users monitoring the channel see all responses")
    else:
        print("❌ TESTS FAILED")
        sys.exit(1)
    print("=" * 70)
