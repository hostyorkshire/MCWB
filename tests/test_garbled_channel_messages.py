#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

"""
Test to verify the fix for garbled messages from non-#wxtest channels.
This simulates the exact scenario from the problem statement where
encrypted/garbled messages from channel_idx=0 and channel_idx=1
were showing corrupted terminal output.
"""

import struct
import time
from unittest.mock import MagicMock

from weather_bot import WeatherBot


def create_channel_message(channel_idx, text_bytes, code=0x88):
    """
    Create a channel message payload in old format.
    Format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    """
    path_len = 0x00
    txt_type = 0x00
    timestamp = struct.pack("<I", int(time.time()))

    payload = bytes([code, channel_idx, path_len, txt_type]) + timestamp + text_bytes
    return payload


def test_garbled_messages_filtered():
    """Test that garbled messages from various channels are properly filtered"""
    print("=" * 80)
    print("TEST: Garbled Channel Messages (Problem Statement Scenario)")
    print("=" * 80)

    bot = WeatherBot(debug=True)
    bot._ser = MagicMock()
    bot._send_cmd = MagicMock()

    sent_responses = []

    def mock_send_channel_msg(text, channel_idx):
        sent_responses.append({"text": text, "channel_idx": channel_idx})

    bot._send_channel_msg = mock_send_channel_msg

    print("\n--- Test 1: Garbled message from channel_idx=0 (like in user's log) ---")
    # Simulate encrypted/garbled data that might come from channel 0
    # This represents encrypted data with invalid UTF-8 to ensure it's rejected
    garbled_bytes_1 = b"\x67\x46\x3a\x44\x25\x3f\x3b\xff\xfe\x63\x4d\x43"  # Invalid UTF-8
    payload1 = create_channel_message(0, garbled_bytes_1)

    sent_responses.clear()
    bot._dispatch(payload1)

    assert len(sent_responses) == 0, f"Should NOT respond to garbled message, got {len(sent_responses)} responses"
    print("✅ Garbled message from channel_idx=0: correctly filtered (no response)")

    print("\n--- Test 2: Garbled message from channel_idx=1 ---")
    # Another garbled message
    garbled_bytes_2 = b"\x00\x01\x02\x03\x7c\x79\xff\xfe\xfd"  # Mix of invalid UTF-8
    payload2 = create_channel_message(1, garbled_bytes_2)

    sent_responses.clear()
    bot._dispatch(payload2)

    assert len(sent_responses) == 0, f"Should NOT respond to garbled message, got {len(sent_responses)} responses"
    print("✅ Garbled message from channel_idx=1: correctly filtered (no response)")

    print("\n--- Test 3: Valid message from channel_idx=0 (should work) ---")
    # A proper weather request
    valid_text = b"Alice: WX York"
    payload3 = create_channel_message(0, valid_text)

    sent_responses.clear()
    bot._dispatch(payload3)

    assert len(sent_responses) == 1, f"Should respond to valid message, got {len(sent_responses)} responses"
    print("✅ Valid message from channel_idx=0: correctly processed and responded")

    print("\n--- Test 4: Valid message from channel_idx=1 (should work) ---")
    # Another proper weather request
    valid_text_2 = b"Bob: weather London"
    payload4 = create_channel_message(1, valid_text_2)

    sent_responses.clear()
    bot._dispatch(payload4)

    assert len(sent_responses) == 1, f"Should respond to valid message, got {len(sent_responses)} responses"
    print("✅ Valid message from channel_idx=1: correctly processed and responded")

    print("\n--- Test 5: Message without SenderName prefix but valid (should work) ---")
    # Messages from new hashtag channels may not have "SenderName: " prefix
    valid_no_prefix = b"WX Leeds"
    payload5 = create_channel_message(2, valid_no_prefix)

    sent_responses.clear()
    bot._dispatch(payload5)

    assert len(sent_responses) == 1, f"Should respond to valid WX command, got {len(sent_responses)} responses"
    print("✅ Valid message without prefix from channel_idx=2: correctly processed")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("\nThe fix successfully:")
    print("  - Filters out garbled/encrypted messages from all channels")
    print("  - Prevents terminal corruption from control characters")
    print("  - Allows valid messages from all channels")
    print("  - Handles messages with and without 'SenderName:' prefix")
    print("=" * 80)


def test_log_sanitization():
    """Test that log sanitization prevents terminal corruption"""
    print("\n" + "=" * 80)
    print("TEST: Log Sanitization")
    print("=" * 80)

    bot = WeatherBot(debug=True)

    test_cases = [
        ("Normal text", "Normal text", "Normal ASCII text"),
        ("Text\nwith\nnewlines", "Text\nwith\nnewlines", "Text with newlines"),
        ("Text\x00with\x01null", "Text\\x00with\\x01null", "Control chars converted to hex"),
        ("A" * 300, "A" * 200 + "... (100 more chars)", "Long text truncated"),
        ("Mix\x1b[31mESC\x1b[0m", "Mix\\x1b[31mESC\\x1b[0m", "ANSI escape codes sanitized (ESC to hex, rest kept)"),
    ]

    print("\nTesting sanitization on various inputs:")
    all_passed = True
    for input_text, expected_output, description in test_cases:
        result = bot._sanitize_for_log(input_text)
        # For the truncation test, just check if it starts correctly and is truncated
        if len(input_text) > 200:
            passes = result.startswith("A" * 200) and "more chars)" in result
        else:
            passes = result == expected_output

        status = "✅" if passes else "❌"
        if not passes:
            all_passed = False
            print(f"{status} {description}")
            print(f"  Input: {repr(input_text[:50])}")
            print(f"  Expected: {repr(expected_output[:50])}")
            print(f"  Got: {repr(result[:50])}")
        else:
            print(f"{status} {description}")

    assert all_passed, "Some sanitization tests failed"
    print("\n" + "=" * 80)
    print("✅ LOG SANITIZATION TESTS PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_log_sanitization()
        test_garbled_messages_filtered()
        print("\n" + "🎉" * 20)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("🎉" * 20)
        print("\nThe fix successfully prevents garbled output from")
        print("encrypted/corrupted messages on any channel!")
        exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
