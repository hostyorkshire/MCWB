#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

"""
Test to verify encrypted message detection works correctly.
This test simulates the real-world scenario where encrypted messages
have a valid channel_idx but garbled/encrypted content.
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


def test_encrypted_message_detection():
    """Test that encrypted messages with valid channel_idx are detected and skipped"""
    print("=" * 80)
    print("TEST: Encrypted Message Detection")
    print("=" * 80)

    bot = WeatherBot(debug=True)
    bot._ser = MagicMock()
    bot._send_cmd = MagicMock()

    sent_responses = []

    def mock_send_channel_msg(text, channel_idx):
        sent_responses.append({"text": text, "channel_idx": channel_idx})

    bot._send_channel_msg = mock_send_channel_msg

    print("\n--- Test 1: Valid unencrypted message ---")
    valid_text = b"M3UXC: WX London"
    payload1 = create_channel_message(0, valid_text)

    sent_responses.clear()
    bot._dispatch(payload1)

    assert len(sent_responses) == 1, f"Should respond to valid message, got {len(sent_responses)} responses"
    print("✅ Valid message: responded correctly")

    print("\n--- Test 2: Encrypted message with valid channel_idx=1 ---")
    # Simulate encrypted data with lots of non-printable bytes
    # This is similar to what we see in the logs: ^t�&tE%3GۺIrƘ&cՆwguPv2>[0#0R#9
    encrypted_bytes = b"\x01\x02\x03\x04\x05\x06\x07\x08test\x0a\x0b\x0c\x0d\x0e\x0f\x10"
    payload2 = create_channel_message(1, encrypted_bytes)

    sent_responses.clear()
    bot._dispatch(payload2)

    assert len(sent_responses) == 0, f"Should NOT respond to encrypted message, got {len(sent_responses)} responses"
    print("✅ Encrypted message with valid channel_idx=1: correctly ignored")

    print("\n--- Test 3: Another encrypted message with channel_idx=2 ---")
    # More encrypted data
    encrypted_bytes2 = b"\x00\x00\x00hello\xff\xfe\xfd\xfc\xfb\xfa\xf9\xf8\xf7\xf6"
    payload3 = create_channel_message(2, encrypted_bytes2)

    sent_responses.clear()
    bot._dispatch(payload3)

    assert len(sent_responses) == 0, f"Should NOT respond to encrypted message, got {len(sent_responses)} responses"
    print("✅ Encrypted message with valid channel_idx=2: correctly ignored")

    print("\n--- Test 4: Valid message without 'SenderName:' prefix ---")
    # This simulates new hashtag channels
    valid_no_prefix = b"WX Leeds"
    payload4 = create_channel_message(3, valid_no_prefix)

    sent_responses.clear()
    bot._dispatch(payload4)

    assert len(sent_responses) == 1, f"Should respond to valid WX command, got {len(sent_responses)} responses"
    print("✅ Valid message without prefix: responded correctly")

    print("\n--- Test 5: Long encrypted message (like in user's log) ---")
    # Simulate the 153-byte encrypted message from the log
    long_encrypted = b"\x01\x15\x8a\x99" + b"encrypted" + b"\xf1\xaa\xbb" * 40
    payload5 = create_channel_message(1, long_encrypted)

    sent_responses.clear()
    bot._dispatch(payload5)

    assert (
        len(sent_responses) == 0
    ), f"Should NOT respond to long encrypted message, got {len(sent_responses)} responses"
    print("✅ Long encrypted message: correctly ignored")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("\nThe bot correctly:")
    print("  - Responds to valid unencrypted messages")
    print("  - Ignores encrypted messages even with valid channel_idx")
    print("  - Handles messages with and without 'SenderName:' prefix")
    print("  - Filters based on byte content, not just channel_idx")
    print("=" * 80)


def test_byte_validation_directly():
    """Test the _is_valid_message_bytes method directly"""
    print("\n" + "=" * 80)
    print("TEST: Direct Byte Validation")
    print("=" * 80)

    bot = WeatherBot(debug=False)

    test_cases = [
        (b"WX London", True, "Valid ASCII text"),
        (b"M3UXC: weather Leeds", True, "Valid text with colon"),
        (b"Test\nwith\nnewlines", True, "Text with newlines"),
        (b"UTF-8: \xc3\xa9\xc3\xa0", True, "Valid UTF-8 with accents"),
        (b"\x01\x02\x03\x04\x05test", False, "Lots of control chars"),
        (b"\x00\x01\x15\x8a\x99\xf1\xaa\xbb", False, "All non-printable"),
        (b"\x1f\x1e\x1d\x1c\x1b\x1a", False, "Control characters only"),
        # Updated: NULL bytes and invalid UTF-8 sequences are now rejected by strict UTF-8 decoding
        # This is better behavior as NULL bytes should not appear in text messages
        (b"hello\x00world\xff\xfe", False, "Mixed with invalid UTF-8 (NULL, 0xFF, 0xFE) - correctly rejected"),
        # More realistic encrypted data
        (b"\x00\x01\x02hi\xff\xfe\xfd", False, "Mostly encrypted with short text"),
    ]

    all_passed = True
    for text_bytes, expected, description in test_cases:
        result = bot._is_valid_message_bytes(text_bytes)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False

        # Calculate actual ratio for debugging
        printable = sum(
            1
            for b in text_bytes
            if (
                32 <= b <= 126  # Printable ASCII
                or b in (9, 10, 13)  # Whitespace (tab, newline, CR)
                or 0x80 <= b <= 0xBF  # UTF-8 continuation bytes
                or 0xC2 <= b <= 0xF4  # UTF-8 start bytes (2-4 byte sequences)
            )
        )
        ratio = printable / len(text_bytes) if text_bytes else 0

        print(f"{status} {description}: expected={expected}, got={result}, ratio={ratio:.2f}")

    assert all_passed, "Some byte validation tests failed"
    print("\n" + "=" * 80)
    print("✅ ALL BYTE VALIDATION TESTS PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_byte_validation_directly()
        test_encrypted_message_detection()
        print("\n🎉 ALL TESTS PASSED! 🎉")
        exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
