#!/usr/bin/env python3
"""
Test to verify that encrypted/garbled messages are NOT logged.
These are messages from other users/channels that the bot cannot decrypt.

The issue: Bot logs "channel_idx=X unknown: [garbled text]" for encrypted messages.
Expected: Bot should silently skip messages that don't have the "SenderName: " format.
"""

import struct
import time
from unittest.mock import MagicMock
from io import StringIO
import sys
from weather_bot import WeatherBot


def create_channel_message(channel_idx, text, code=0x88):
    """
    Create a channel message payload in old format.
    Format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    """
    path_len = 0x00
    txt_type = 0x00
    timestamp = struct.pack('<I', int(time.time()))
    text_bytes = text.encode('utf-8', errors='ignore')
    
    payload = bytes([code, channel_idx, path_len, txt_type]) + timestamp + text_bytes
    return payload


def test_encrypted_message_not_logged():
    """Test that encrypted/garbled messages without sender format are silently skipped"""
    print("=" * 80)
    print("TEST: Encrypted Message Logging")
    print("=" * 80)
    
    bot = WeatherBot(debug=True)
    bot._ser = MagicMock()
    bot._send_cmd = MagicMock()
    
    sent_responses = []
    
    def mock_send_channel_msg(text, channel_idx):
        sent_responses.append({'text': text, 'channel_idx': channel_idx})
    
    bot._send_channel_msg = mock_send_channel_msg
    
    # Capture stdout to check what gets logged
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    try:
        # Test 1: Encrypted/garbled message without "SenderName: " format
        print("\nTest 1: Encrypted message on channel 6 (no colon, encrypted content)")
        # Using simple text without colon to represent encrypted/improperly formatted message
        encrypted_text = "encrypted_binary_data_xyz123"
        payload1 = create_channel_message(6, encrypted_text)
        
        sent_responses.clear()
        bot._dispatch(payload1)
        
        # Should NOT respond (no WX command) and should skip with debug log
        assert len(sent_responses) == 0, "Bot should not respond to encrypted messages"
        
        # Test 2: Another encrypted message
        print("\nTest 2: Encrypted message on channel 0")
        encrypted_text2 = "garbled_encrypted_content"
        payload2 = create_channel_message(0, encrypted_text2)
        
        sent_responses.clear()
        bot._dispatch(payload2)
        
        assert len(sent_responses) == 0, "Bot should not respond to garbled messages"
        
        # Test 3: Valid message with proper format (should be logged)
        print("\nTest 3: Valid message with SenderName: format")
        valid_text = "M3UXC/M: WX Leeds"
        payload3 = create_channel_message(0, valid_text)
        
        sent_responses.clear()
        bot._dispatch(payload3)
        
        # Should respond to WX command
        assert len(sent_responses) == 1, "Bot should respond to valid WX command"
        
        # Test 4: Another valid message
        print("\nTest 4: Another valid message")
        valid_text2 = "Alice: Hello everyone"
        payload4 = create_channel_message(1, valid_text2)
        
        sent_responses.clear()
        bot._dispatch(payload4)
        
        # Should not respond (no WX command) but should log normally
        assert len(sent_responses) == 0, "Bot should not respond to non-WX messages"
        
    finally:
        sys.stdout = old_stdout
    
    output = captured_output.getvalue()
    
    print("\n" + "=" * 80)
    print("RESULTS:")
    print("=" * 80)
    
    # Check what was logged
    lines = output.split('\n')
    
    # Count messages with and without proper format
    skipped_message_count = 0
    unknown_logged_count = 0
    valid_message_count = 0
    
    for line in lines:
        # Check for skipped messages (new behavior with debug log)
        if 'skipping message without sender format' in line:
            skipped_message_count += 1
            print(f"✓ Skipped encrypted message (debug log): {line[:80]}")
        # Check for old-style "unknown:" logs (should not appear)
        elif 'channel_idx=' in line and 'unknown:' in line:
            unknown_logged_count += 1
            print(f"❌ Found 'unknown:' in log: {line[:80]}")
        # Check for valid messages with sender format
        elif 'channel_idx=' in line and ('M3UXC/M' in line or 'Alice' in line):
            valid_message_count += 1
            print(f"✓ Valid message logged: {line[:80]}")
    
    print(f"\nSkipped messages (with debug log): {skipped_message_count} (should be 2)")
    print(f"Messages with 'unknown:' logged: {unknown_logged_count} (should be 0)")
    print(f"Valid messages logged: {valid_message_count} (should be 2)")
    
    # The fix should ensure that:
    # 1. Encrypted messages are skipped (with debug log)
    # 2. No "unknown:" entries appear in logs
    # 3. Valid messages are still logged normally
    assert skipped_message_count == 2, f"Should skip 2 encrypted messages, skipped {skipped_message_count}"
    assert unknown_logged_count == 0, f"'unknown:' should NOT appear in logs, found {unknown_logged_count}"
    assert valid_message_count == 2, f"Valid messages should be logged, found {valid_message_count}"
    
    print("\n✅ Fix verified: Encrypted messages are skipped with debug log")
    print("=" * 80)


def main():
    try:
        test_encrypted_message_not_logged()
        print("\n✅ TEST PASSED!")
        print("\nThe bot now skips encrypted messages that:")
        print("  - Don't have the 'SenderName: ' format")
        print("  - Logs them at debug level for troubleshooting")
        print("\nThis prevents confusing 'unknown:' log entries while still")
        print("allowing debug visibility when needed.")
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
