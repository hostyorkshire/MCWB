#!/usr/bin/env python3
"""
Test to verify bot behavior with encrypted messages on different channels
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import struct

from weather_bot import WeatherBot


def test_encrypted_vs_plaintext():
    """
    Simulate what happens when:
    - Channel 0 (wxtest) has plaintext messages
    - Other channels have encrypted messages
    """
    print()
    print("=" * 70)
    print("TEST: Bot Response to Encrypted vs Plaintext Messages")
    print("=" * 70)
    print()

    bot = WeatherBot(debug=True)

    # Test 1: Plaintext message on channel 0 (like wxtest)
    print("Test 1: Plaintext message on channel 0")
    code = 0x88  # PUSH_CHAN_MSG
    channel_idx = 0
    path_len = 0
    txt_type = 0
    timestamp = struct.pack("<I", 1234567890)
    text = b"M3UXC: wx Leeds"
    payload = bytes([code, channel_idx, path_len, txt_type]) + timestamp + text

    result = bot._parse_channel_message(payload)
    print(f"  Parse result: {result}")
    if result[0] is not None:
        print("  ✅ ACCEPTED: Plaintext message on channel 0")
    else:
        print("  ❌ REJECTED: Plaintext message on channel 0 (unexpected!)")
    print()

    # Test 2: Encrypted message on channel 1 (simulated with random bytes)
    print("Test 2: Encrypted message on channel 1")
    channel_idx = 1
    # Encrypted messages have random-looking bytes instead of readable text
    encrypted_text = bytes([0x7F, 0x3A, 0x9B, 0x12, 0xEF, 0x44, 0x88, 0x91, 0x23, 0xCD, 0xFE, 0xAA])
    payload = bytes([code, channel_idx, path_len, txt_type]) + timestamp + encrypted_text

    result = bot._parse_channel_message(payload)
    print(f"  Parse result: {result}")
    if result[0] is None:
        print("  ✅ EXPECTED: Encrypted message on channel 1 rejected")
    else:
        print("  ⚠️  UNEXPECTED: Encrypted message on channel 1 was accepted")
    print()

    # Test 3: Invalid channel index > 7
    print("Test 3: Message with invalid channel_idx=15")
    channel_idx = 15  # Invalid - max is 7
    payload = bytes([code, channel_idx, path_len, txt_type]) + timestamp + text

    result = bot._parse_channel_message(payload)
    print(f"  Parse result: {result}")
    if result[0] is None:
        print("  ✅ EXPECTED: Invalid channel_idx rejected")
    else:
        print("  ⚠️  UNEXPECTED: Invalid channel_idx was accepted")
    print()

    # Test 4: Plaintext message on channel 3 should work
    print("Test 4: Plaintext message on channel 3")
    channel_idx = 3
    payload = bytes([code, channel_idx, path_len, txt_type]) + timestamp + text

    result = bot._parse_channel_message(payload)
    print(f"  Parse result: {result}")
    if result[0] is not None:
        print("  ✅ ACCEPTED: Plaintext message on channel 3")
    else:
        print("  ❌ REJECTED: Plaintext message on channel 3 (unexpected!)")
    print()

    print("=" * 70)
    print("SUMMARY:")
    print("- Plaintext messages on ANY channel (0-7) should be accepted")
    print("- Encrypted messages on ANY channel should be rejected")
    print("- Messages with invalid channel_idx (>7) should be rejected")
    print()
    print("If other channels are encrypted in your mesh network,")
    print("the bot will only respond on unencrypted channels.")
    print("=" * 70)
    print()


if __name__ == "__main__":
    test_encrypted_vs_plaintext()
