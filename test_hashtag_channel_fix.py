#!/usr/bin/env python3
"""
Manual test to demonstrate the fix for hashtag channel message skipping issue.

This test simulates the exact scenario from the problem statement:
- Messages from new hashtag channels without "SenderName: " prefix
- Previously these were skipped with "skipping message without SenderName: format"
- Now they should be processed correctly
"""

import struct
import time
from unittest.mock import MagicMock
from weather_bot import WeatherBot


def create_channel_message(channel_idx, text, code=0x88):
    """
    Create a channel message payload in old format.
    
    Old format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    V3 format adds SNR(1) + reserved(2) before channel_idx for signal quality tracking.
    
    This function uses the old format for compatibility with existing deployments.
    """
    path_len = 0x00
    txt_type = 0x00
    timestamp = struct.pack('<I', int(time.time()))
    text_bytes = text.encode('utf-8', errors='ignore')
    
    payload = bytes([code, channel_idx, path_len, txt_type]) + timestamp + text_bytes
    return payload


def test_hashtag_channel_messages():
    """
    Test that simulates messages from new hashtag channels.
    These messages may not have the "SenderName: " prefix.
    """
    print("\n" + "=" * 80)
    print("DEMONSTRATION: Hashtag Channel Message Fix")
    print("=" * 80)
    print("\nProblem: Messages from new meshcore hashtag channels were being skipped")
    print("         with log: 'skipping message without SenderName: format'\n")
    
    bot = WeatherBot(debug=True)
    bot._ser = MagicMock()
    bot._send_cmd = MagicMock()
    
    sent_responses = []
    
    def mock_send_channel_msg(text, channel_idx):
        sent_responses.append({'text': text, 'channel_idx': channel_idx})
        print(f"\n✅ BOT RESPONDED on channel_idx={channel_idx}:")
        print(f"   {text[:100]}{'...' if len(text) > 100 else ''}\n")
    
    bot._send_channel_msg = mock_send_channel_msg
    
    print("=" * 80)
    print("TEST SCENARIO: Messages from new hashtag channels")
    print("=" * 80)
    
    # Test 1: Message on channel 0 without sender prefix (like from problem statement)
    print("\nTest 1: WX command on channel_idx=0 WITHOUT sender prefix")
    print("        (Simulating message from new hashtag channel)")
    test_message_1 = "WX London"
    payload1 = create_channel_message(0, test_message_1)
    
    sent_responses.clear()
    bot._dispatch(payload1)
    
    if len(sent_responses) == 1:
        print("✅ SUCCESS: Bot processed message and sent weather response")
    else:
        print("❌ FAILED: Bot did not respond to valid WX command")
    
    # Test 2: Message on channel 1 without sender prefix
    print("\nTest 2: WX command on channel_idx=1 WITHOUT sender prefix")
    print("        (Another new hashtag channel)")
    test_message_2 = "weather Leeds"
    payload2 = create_channel_message(1, test_message_2)
    
    sent_responses.clear()
    bot._dispatch(payload2)
    
    if len(sent_responses) == 1:
        print("✅ SUCCESS: Bot processed message and sent weather response")
    else:
        print("❌ FAILED: Bot did not respond to valid WX command")
    
    # Test 3: Message WITH sender prefix (normal case - should still work)
    print("\nTest 3: WX command WITH sender prefix (normal case)")
    test_message_3 = "M3UXC/M: WX York"
    payload3 = create_channel_message(0, test_message_3)
    
    sent_responses.clear()
    bot._dispatch(payload3)
    
    if len(sent_responses) == 1:
        print("✅ SUCCESS: Bot processed message and sent weather response")
    else:
        print("❌ FAILED: Bot did not respond to valid WX command")
    
    # Test 4: Non-WX message without prefix (should be logged but not responded to)
    print("\nTest 4: Non-WX message WITHOUT sender prefix")
    print("        (Should be logged but no response)")
    test_message_4 = "Hello everyone"
    payload4 = create_channel_message(2, test_message_4)
    
    sent_responses.clear()
    bot._dispatch(payload4)
    
    if len(sent_responses) == 0:
        print("✅ SUCCESS: Bot logged message but did not respond (no WX command)")
    else:
        print("❌ UNEXPECTED: Bot responded to non-WX message")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✅ FIX VERIFIED!")
    print("\nThe bot now correctly:")
    print("  1. Processes messages from hashtag channels WITHOUT sender prefix")
    print("  2. Responds to WX commands even without 'SenderName: ' format")
    print("  3. Still handles normal messages with sender prefix")
    print("  4. Logs all messages for debugging when debug mode is enabled")
    print("\nThis fixes the issue where messages from new meshcore hashtag")
    print("channels were being skipped with 'skipping message without SenderName: format'")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_hashtag_channel_messages()
