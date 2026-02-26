#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

"""
Test channel verification and encryption detection functionality.
"""

from weather_bot import WeatherBot


def test_looks_like_valid_text():
    """Test the _looks_like_valid_text helper function."""
    print("Testing _looks_like_valid_text()...")

    # Create a bot instance to test the method
    bot = WeatherBot(debug=False, verify_channels=False)

    # Valid text examples
    valid_texts = [
        "Hello world",
        "WX Leeds",
        "User123: weather London",
        "Temperature: 15°C",
        "Test message with numbers 123 and symbols !@#",
    ]

    # Invalid/garbled text examples (from encrypted messages)
    invalid_texts = [
        "\x00\x01\x02\x03\x04",  # Control characters
        "",  # Empty
        "\x1f\x1e\x1d",  # More control chars
    ]

    for text in valid_texts:
        result = bot._looks_like_valid_text(text)
        status = "✓" if result else "✗"
        print(f"  {status} Valid text: '{text[:30]}...' -> {result}")
        assert result, f"Should recognize as valid: {text}"

    for text in invalid_texts:
        result = bot._looks_like_valid_text(text)
        status = "✓" if not result else "✗"
        safe_text = repr(text)[:40]
        print(f"  {status} Invalid text: {safe_text}... -> {result}")
        assert not result, f"Should recognize as invalid: {text}"

    print("✅ All _looks_like_valid_text tests passed!\n")


def test_encrypted_message_tracking():
    """Test that encrypted message tracking works."""
    print("Testing encrypted message tracking...")

    bot = WeatherBot(debug=False, verify_channels=True)

    # Simulate parsing a valid message
    # V3 format: code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    valid_payload = (
        bytes(
            [
                0x88,  # code: PUSH_CHAN_MSG
                35,  # SNR: 35 dB (realistic)
                0x00,
                0x00,  # reserved
                1,  # channel_idx: 1
                0,  # path_len
                0,  # txt_type
                0,
                0,
                0,
                0,  # timestamp
            ]
        )
        + b"User: WX London"
    )

    channel_idx, text = bot._parse_channel_message(valid_payload)
    assert channel_idx == 1, f"Expected channel_idx=1, got {channel_idx}"
    assert text == "User: WX London", f"Expected text, got {text}"
    assert 1 in bot._valid_channels, "Channel 1 should be in valid_channels"
    print("  ✓ Valid message tracked correctly")

    # Simulate parsing an encrypted/garbled message
    garbled_payload = bytes(
        [
            0x88,  # code: PUSH_CHAN_MSG
            40,  # SNR: 40 dB (realistic)
            0x00,
            0x00,  # reserved
            2,  # channel_idx: 2
            0,  # path_len
            0,  # txt_type
            0,
            0,
            0,
            0,  # timestamp
            # Garbled encrypted data (non-printable bytes)
            0x00,
            0x01,
            0x02,
            0x03,
            0x6B,
            0xDE,
            0x96,
            0x3F,
            0x17,
            0x5A,
            0x34,
            0x5A,
            0x72,
            0x5F,
            0x22,
            0x6D,
        ]
    )

    channel_idx, text = bot._parse_channel_message(garbled_payload)
    assert channel_idx is None, "Should return None for encrypted message"
    assert text is None, "Should return None for encrypted message"
    assert 2 in bot._encrypted_channels, "Channel 2 should be in encrypted_channels"
    print("  ✓ Encrypted message tracked correctly")

    # Verify summary
    assert len(bot._valid_channels) == 1, "Should have 1 valid channel"
    assert len(bot._encrypted_channels) == 1, "Should have 1 encrypted channel"
    print("  ✓ Tracking counts correct")

    print("✅ Encrypted message tracking tests passed!\n")


def test_channel_idx_validation():
    """Test that invalid channel indices are handled properly."""
    print("Testing channel_idx validation...")

    bot = WeatherBot(debug=False, verify_channels=False)

    # Test old format with invalid channel_idx (payload < 12 bytes to force old format)
    invalid_payload = bytes(
        [
            0x08,  # code: RESP_CHANNEL_MSG
            49,  # channel_idx: 49 (invalid, outside 0-7 range)
            0,  # path_len
            0,  # txt_type
            0,
            0,
            0,
            0,  # timestamp
            65,  # 'A' - one byte text to keep it short
        ]
    )

    channel_idx, text = bot._parse_channel_message(invalid_payload)
    assert channel_idx is None, f"Should return None for invalid channel_idx, got {channel_idx}"
    assert text is None, f"Should return None for invalid channel_idx, got {text}"
    print("  ✓ Invalid channel_idx (49) rejected in old format")

    # Test old format with valid channel_idx but garbled text (short payload)
    garbled_old_payload = bytes(
        [
            0x08,  # code: RESP_CHANNEL_MSG
            3,  # channel_idx: 3 (valid)
            0,  # path_len
            0,  # txt_type
            0,
            0,
            0,
            0,  # timestamp
            0x00,
            0x01,
            0x02,  # Just a few bytes of garbled data
        ]
    )

    channel_idx, text = bot._parse_channel_message(garbled_old_payload)
    assert channel_idx is None, f"Should return None for garbled text, got channel={channel_idx}"
    assert text is None, f"Should return None for garbled text, got text={text}"
    print("  ✓ Garbled old format message rejected")

    print("✅ Channel validation tests passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Channel Verification Tests")
    print("=" * 60 + "\n")

    test_looks_like_valid_text()
    test_encrypted_message_tracking()
    test_channel_idx_validation()

    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
