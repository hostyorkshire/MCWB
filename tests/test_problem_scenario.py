#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

"""
Simulate the exact scenario from the problem statement:
Messages received on channel_idx 49 and 51 (which are actually SNR values in V3 format)

This test verifies that the fix resolves the issue where:
- Messages showed "channel_idx=49 unknown" and "channel_idx=51 unknown"
- The text was garbled
- The bot did not respond to weather commands
"""

import struct
import time
from unittest.mock import MagicMock
from weather_bot import WeatherBot


def create_realistic_v3_message(channel_idx, snr, sender, message):
    """
    Create a V3 format PUSH_CHAN_MSG (0x88) payload that mimics what 
    the real MeshCore firmware sends.
    """
    code = 0x88  # PUSH_CHAN_MSG
    reserved = b'\x00\x00'
    path_len = 0x00
    txt_type = 0x00
    timestamp = struct.pack('<I', int(time.time()))
    text = f"{sender}: {message}".encode('utf-8')
    
    # V3 format: code + SNR + reserved(2) + channel_idx + path_len + txt_type + timestamp + text
    payload = bytes([code, snr]) + reserved + bytes([channel_idx, path_len, txt_type]) + timestamp + text
    return payload


def test_problem_statement_scenario():
    """
    Replicate the exact issue from the problem statement.
    Before the fix, this would show:
      [20:58:10] channel_idx=51 unknown: [garbled text]
      [20:58:11] channel_idx=49 unknown: [garbled text]
    
    After the fix, it should correctly parse the messages and respond.
    """
    print("=" * 80)
    print("REPRODUCING PROBLEM STATEMENT SCENARIO")
    print("=" * 80)
    print("\nOriginal issue:")
    print("  - User sent WX commands on channels but bot did not reply")
    print("  - Log showed: 'channel_idx=49 unknown' and 'channel_idx=51 unknown'")
    print("  - Text was garbled because SNR values (49, 51) were being read as channel_idx")
    print("\n" + "=" * 80)
    
    bot = WeatherBot(debug=True)
    
    # Mock serial and command sending
    bot._ser = MagicMock()
    sent_responses = []
    
    def mock_send_channel_msg(text, channel_idx):
        sent_responses.append({'text': text, 'channel_idx': channel_idx})
        print(f"[BOT RESPONSE] Sent on channel_idx={channel_idx}: {text[:50]}...")
    
    bot._send_channel_msg = mock_send_channel_msg
    bot._send_cmd = MagicMock()
    
    print("\n" + "-" * 80)
    print("TEST CASE 1: Message with SNR=51 on channel_idx=1")
    print("-" * 80)
    print("Simulating: User on channel #weather (idx=1) sends 'WX Leeds'")
    print("            Radio firmware sends V3 format with SNR=51")
    
    # This simulates what was happening in the problem statement
    # SNR=51, actual channel_idx=1
    payload1 = create_realistic_v3_message(
        channel_idx=1,
        snr=51,
        sender="Alice",
        message="WX Leeds"
    )
    
    print(f"\nPayload bytes: {payload1[:12].hex()}")
    print(f"  Byte [1] (SNR): {payload1[1]} (was being read as channel_idx BEFORE fix)")
    print(f"  Byte [4] (channel_idx): {payload1[4]} (correct value)")
    
    sent_responses.clear()
    bot._dispatch(payload1)
    
    # Verify the bot responded
    assert len(sent_responses) == 1, f"Expected bot to send 1 response, got {len(sent_responses)}"
    assert sent_responses[0]['channel_idx'] == 1, f"Bot should respond on channel_idx=1, got {sent_responses[0]['channel_idx']}"
    print(f"\n✅ SUCCESS: Bot correctly parsed channel_idx=1 (not 51)")
    print(f"✅ SUCCESS: Bot recognized 'WX Leeds' command and responded")
    print(f"✅ SUCCESS: Response sent on correct channel_idx=1")
    
    print("\n" + "-" * 80)
    print("TEST CASE 2: Message with SNR=49 on channel_idx=2")
    print("-" * 80)
    print("Simulating: User on different channel (idx=2) sends 'weather Manchester'")
    print("            Radio firmware sends V3 format with SNR=49")
    
    # SNR=49, actual channel_idx=2
    payload2 = create_realistic_v3_message(
        channel_idx=2,
        snr=49,
        sender="Bob",
        message="weather Manchester"
    )
    
    print(f"\nPayload bytes: {payload2[:12].hex()}")
    print(f"  Byte [1] (SNR): {payload2[1]} (was being read as channel_idx BEFORE fix)")
    print(f"  Byte [4] (channel_idx): {payload2[4]} (correct value)")
    
    sent_responses.clear()
    bot._dispatch(payload2)
    
    # Verify the bot responded
    assert len(sent_responses) == 1, f"Expected bot to send 1 response, got {len(sent_responses)}"
    assert sent_responses[0]['channel_idx'] == 2, f"Bot should respond on channel_idx=2, got {sent_responses[0]['channel_idx']}"
    print(f"\n✅ SUCCESS: Bot correctly parsed channel_idx=2 (not 49)")
    print(f"✅ SUCCESS: Bot recognized 'weather Manchester' command and responded")
    print(f"✅ SUCCESS: Response sent on correct channel_idx=2")
    
    print("\n" + "=" * 80)
    print("🎉 PROBLEM STATEMENT SCENARIO FIXED!")
    print("=" * 80)
    print("\nBefore fix:")
    print("  ❌ channel_idx=51 unknown: [garbled text]")
    print("  ❌ channel_idx=49 unknown: [garbled text]")
    print("  ❌ Bot did not respond")
    print("\nAfter fix:")
    print("  ✅ channel_idx=1 Alice: WX Leeds")
    print("  ✅ channel_idx=2 Bob: weather Manchester")
    print("  ✅ Bot responds on correct channels")
    print("=" * 80)


def test_all_valid_channels():
    """Test that the bot works on all valid channel indices (0-7) with various SNR values."""
    print("\n\n" + "=" * 80)
    print("COMPREHENSIVE TEST: All Valid Channels (0-7) with Various SNR Values")
    print("=" * 80)
    
    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()
    bot._send_cmd = MagicMock()
    
    sent_responses = []
    
    def mock_send_channel_msg(text, channel_idx):
        sent_responses.append({'channel_idx': channel_idx})
    
    bot._send_channel_msg = mock_send_channel_msg
    
    # Test all valid channel indices with realistic SNR values
    test_cases = [
        (0, 45, "John", "WX London"),
        (1, 51, "Alice", "WX Leeds"),
        (2, 49, "Bob", "weather Manchester"),
        (3, 47, "Carol", "WX York"),
        (4, 52, "Dave", "weather Birmingham"),
        (5, 48, "Eve", "WX Glasgow"),
        (6, 50, "Frank", "weather Edinburgh"),
        (7, 46, "Grace", "WX Belfast"),
    ]
    
    success_count = 0
    for channel_idx, snr, sender, message in test_cases:
        sent_responses.clear()
        payload = create_realistic_v3_message(channel_idx, snr, sender, message)
        bot._dispatch(payload)
        
        if len(sent_responses) == 1 and sent_responses[0]['channel_idx'] == channel_idx:
            success_count += 1
            print(f"✅ channel_idx={channel_idx}, SNR={snr}: PASSED")
        else:
            print(f"❌ channel_idx={channel_idx}, SNR={snr}: FAILED")
    
    print(f"\n{success_count}/{len(test_cases)} channels tested successfully")
    assert success_count == len(test_cases), "Not all channels passed"
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_problem_statement_scenario()
        test_all_valid_channels()
        
        print("\n\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nThe weather bot now correctly:")
        print("  1. Detects V3 format messages (with SNR)")
        print("  2. Extracts correct channel_idx (not SNR value)")
        print("  3. Decodes message text properly")
        print("  4. Recognizes weather commands")
        print("  5. Responds on the correct channel")
        print("\nThe issue reported in the problem statement is RESOLVED.")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise
