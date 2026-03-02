#!/usr/bin/env python3
"""
Test to verify that messages without "SenderName: " prefix are handled correctly.
These could be messages from new hashtag channels or self-sent messages.

Expected behavior:
- Messages without "SenderName: " prefix should be processed (sender="channel")
- Encrypted/garbled content won't match WX command pattern, so no response
- Valid WX commands without prefix SHOULD be responded to
"""

import logging
import os
import struct
import sys
import time
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from weather_bot import WeatherBot

# Test case constants
EXPECTED_MESSAGES_WITHOUT_PREFIX = 3  # Tests 1, 2, 3
EXPECTED_WX_RESPONSES = 2  # Tests 3, 4
EXPECTED_MESSAGES_WITH_SENDER = 5  # All 5 tests log message (with or without prefix)
EXPECTED_SENDERS = ["M3UXC/M", "Alice", "channel:"]  # Known senders from test cases


def create_channel_message(channel_idx, text, code=0x88):
    """
    Create a channel message payload in old format.
    Format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text

    path_len is set to 0x01 (non-zero) to ensure reserved bytes != 0x00 so that
    V3-format heuristic 3 is not incorrectly triggered for these old-format frames.
    """
    path_len = 0x01
    txt_type = 0x00
    timestamp = struct.pack("<I", int(time.time()))
    text_bytes = text.encode("utf-8", errors="ignore")

    payload = bytes([code, channel_idx, path_len, txt_type]) + timestamp + text_bytes
    return payload


def test_encrypted_message_not_logged(caplog):
    """Test that messages without sender prefix are processed but don't trigger responses for garbled content"""
    print("=" * 80)
    print("TEST: Messages Without SenderName Prefix")
    print("=" * 80)

    bot = WeatherBot(debug=True)
    bot._ser = MagicMock()
    bot._send_cmd = MagicMock()

    sent_responses = []

    def mock_send_channel_msg(text, channel_idx):
        sent_responses.append({"text": text, "channel_idx": channel_idx})

    bot._send_channel_msg = mock_send_channel_msg

    # Run all dispatch tests while capturing log records
    with caplog.at_level(logging.INFO, logger="weather_bot"):
        # Test 1: Encrypted/garbled message without "SenderName: " format
        # Should be logged but NOT responded to (no WX command)
        print("\nTest 1: Garbled message on channel 6 (without SenderName: format)")
        encrypted_text = "encrypted_binary_data_xyz123"
        payload1 = create_channel_message(6, encrypted_text)

        sent_responses.clear()
        bot._dispatch(payload1)

        # Should NOT respond (no WX command in garbled text)
        assert len(sent_responses) == 0, "Bot should not respond to garbled messages without WX command"

        # Test 2: Another encrypted message
        print("\nTest 2: Garbled message on channel 0 (without SenderName: format)")
        encrypted_text2 = "garbled_encrypted_content"
        payload2 = create_channel_message(0, encrypted_text2)

        sent_responses.clear()
        bot._dispatch(payload2)

        assert len(sent_responses) == 0, "Bot should not respond to garbled messages without WX command"

        # Test 3: Valid WX command WITHOUT sender prefix (NEW: should work!)
        print("\nTest 3: Valid WX command without SenderName: format")
        wx_without_sender = "WX London"
        payload3 = create_channel_message(2, wx_without_sender)

        sent_responses.clear()
        bot._dispatch(payload3)

        # Should respond to WX command even without sender prefix
        assert len(sent_responses) >= 1, "Bot should respond to valid WX command even without sender prefix"

        # Test 4: Valid message with proper format (should still work)
        print("\nTest 4: Valid message with SenderName: format")
        valid_text = "M3UXC/M: WX Leeds"
        payload4 = create_channel_message(0, valid_text)

        sent_responses.clear()
        bot._dispatch(payload4)

        # Should respond to WX command
        assert len(sent_responses) >= 1, "Bot should respond to valid WX command with sender prefix"

        # Test 5: Non-WX message with sender prefix
        print("\nTest 5: Non-WX message with sender prefix")
        valid_text2 = "Alice: Hello everyone"
        payload5 = create_channel_message(1, valid_text2)

        sent_responses.clear()
        bot._dispatch(payload5)

        # Should not respond (no WX command)
        assert len(sent_responses) == 0, "Bot should not respond to non-WX messages"

    output = caplog.text

    print("\n" + "=" * 80)
    print("RESULTS:")
    print("=" * 80)

    # Check what was logged
    lines = output.split("\n")

    # Helper function to classify log lines
    def is_message_without_prefix_log(line):
        """Check if line indicates a message without SenderName prefix"""
        return "message without SenderName: prefix" in line

    def is_message_with_sender_log(line):
        """Check if line contains a properly logged message with sender info"""
        if "channel_idx=" not in line or ": " not in line:
            return False
        # Look for known senders from our test cases
        return any(sender in line for sender in EXPECTED_SENDERS)

    def is_wx_response_log(line):
        """Check if line indicates a WX weather request was processed"""
        return "WX request" in line

    # Count different types of messages
    messages_without_prefix_count = 0
    messages_with_sender_count = 0
    wx_responses = 0

    for line in lines:
        if is_message_without_prefix_log(line):
            messages_without_prefix_count += 1
            print(f"✓ Message without prefix logged: {line[:80]}")
        elif is_message_with_sender_log(line):
            messages_with_sender_count += 1
            print(f"✓ Message logged: {line[:80]}")
        if is_wx_response_log(line):
            wx_responses += 1

    print(
        f"\nMessages without prefix (debug logged): {messages_without_prefix_count} (should be {EXPECTED_MESSAGES_WITHOUT_PREFIX})"
    )
    print(f"Messages with sender logged: {messages_with_sender_count} (should be {EXPECTED_MESSAGES_WITH_SENDER})")
    print(f"WX responses sent: {wx_responses} (should be {EXPECTED_WX_RESPONSES} - one with prefix, one without)")

    # Verify new behavior:
    # 1. Messages without prefix are logged (with debug message about the prefix)
    # 2. Garbled content doesn't trigger WX responses
    # 3. Valid WX commands work with or without sender prefix
    assert (
        messages_without_prefix_count == EXPECTED_MESSAGES_WITHOUT_PREFIX
    ), f"Should log {EXPECTED_MESSAGES_WITHOUT_PREFIX} messages without prefix, logged {messages_without_prefix_count}"
    assert (
        messages_with_sender_count == EXPECTED_MESSAGES_WITH_SENDER
    ), f"Should log {EXPECTED_MESSAGES_WITH_SENDER} messages with sender info, logged {messages_with_sender_count}"
    assert (
        wx_responses == EXPECTED_WX_RESPONSES
    ), f"Should respond to {EXPECTED_WX_RESPONSES} WX commands (with and without prefix), responded to {wx_responses}"

    print("\n✅ New behavior verified:")
    print("  - Messages without SenderName: prefix are processed (sender='channel')")
    print("  - Garbled content is logged but doesn't trigger responses")
    print("  - Valid WX commands work with or without sender prefix")
    print("=" * 80)


def main():
    try:
        test_encrypted_message_not_logged()
        print("\n✅ TEST PASSED!")
        print("\nThe bot now handles messages without 'SenderName: ' prefix:")
        print("  - Processes them with sender='channel' (like meshcore.py)")
        print("  - Logs them at debug level for visibility")
        print("  - Responds to WX commands even without sender prefix")
        print("  - Ignores garbled content that doesn't match WX pattern")
        print("\nThis enables support for new hashtag channels and self-sent messages")
        print("while still preventing responses to encrypted/garbled content.")
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
