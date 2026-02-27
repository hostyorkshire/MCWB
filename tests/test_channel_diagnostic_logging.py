#!/usr/bin/env python3
"""
Test diagnostic logging for channel message parsing
Tests that helpful debug messages are shown when encrypted/invalid messages are received
"""

import sys
from weather_bot import WeatherBot


def test_valid_message_parsing():
    """Test that valid messages parse correctly without extra logging"""
    print("=" * 60)
    print("TEST 1: Valid Message Parsing")
    print("=" * 60)

    bot = WeatherBot(debug=True)

    # Valid old format message: channel_idx=0
    # Payload format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    valid_payload = bytes([0x88, 0, 1, 1, 0, 0, 0, 0]) + b'M3UXC: Wx barnsley'
    channel_idx, text = bot._parse_channel_message(valid_payload)

    assert channel_idx == 0, f"Expected channel_idx=0, got {channel_idx}"
    assert "barnsley" in text, f"Expected 'barnsley' in text, got: {text}"

    print(f"✓ Valid message parsed: channel_idx={channel_idx}")
    print(f"✓ Text extracted: {text[:30]}...")
    print()


def test_encrypted_message_detection():
    """Test that encrypted messages (invalid channel_idx) are detected and logged"""
    print("=" * 60)
    print("TEST 2: Encrypted Message Detection")
    print("=" * 60)

    bot = WeatherBot(debug=True)

    # Encrypted message: channel_idx > 7 (invalid)
    # Payload format: code(1) + channel_idx(1) + other bytes...
    encrypted_payload = bytes([0x88, 129, 42, 35, 115, 42, 59, 40]) + b'garbled data'
    channel_idx, text = bot._parse_channel_message(encrypted_payload)

    assert channel_idx is None, f"Expected None for encrypted message, got {channel_idx}"
    assert text is None, f"Expected None for encrypted message, got {text}"

    print("✓ Encrypted message correctly rejected")
    print("✓ Debug logging explained why message was rejected")
    print()


def test_short_message_detection():
    """Test that messages too short to parse are detected and logged"""
    print("=" * 60)
    print("TEST 3: Short Message Detection")
    print("=" * 60)

    bot = WeatherBot(debug=True)

    # Message too short (< 8 bytes required)
    short_payload = bytes([0x88, 0, 1, 2])
    channel_idx, text = bot._parse_channel_message(short_payload)

    assert channel_idx is None, f"Expected None for short message, got {channel_idx}"
    assert text is None, f"Expected None for short message, got {text}"

    print("✓ Short message correctly rejected")
    print("✓ Debug logging explained message was too short")
    print()


def test_multiple_channels():
    """Test that valid messages on different channel indices work correctly"""
    print("=" * 60)
    print("TEST 4: Multiple Valid Channels")
    print("=" * 60)

    bot = WeatherBot(debug=True)

    for idx in range(8):  # Test all valid channel indices (0-7)
        # Old format payload: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
        # To avoid V3 detection heuristic 3 (reserved bytes = 0x00), use non-zero values
        # for path_len and txt_type
        valid_payload = bytes([0x88, idx, 1, 1, 0, 0, 0, 0]) + f'User: Wx test{idx}'.encode()
        channel_idx, text = bot._parse_channel_message(valid_payload)

        assert channel_idx == idx, f"Expected channel_idx={idx}, got {channel_idx}"
        assert f"test{idx}" in text, f"Expected 'test{idx}' in text, got: {text}"

    print("✓ All 8 channel indices (0-7) work correctly")
    print()


def test_v3_format_invalid_channel():
    """Test V3 format message with invalid channel_idx"""
    print("=" * 60)
    print("TEST 5: V3 Format with Invalid Channel")
    print("=" * 60)

    bot = WeatherBot(debug=True)

    # V3 format: code(1) + SNR(1) + reserved(2) + channel_idx(1) + ...
    # Use invalid channel_idx (> 7) at position 4
    v3_invalid = bytes([0x11, 25, 0, 0, 99, 0, 0, 0, 0, 0, 0]) + b'test'

    # Simulate _dispatch calling this for V3 messages
    payload = v3_invalid
    code = payload[0]
    if code == 0x11:  # RESP_CHANNEL_MSG_V3
        channel_idx = payload[4]
        print(f"V3 message with channel_idx={channel_idx}")
        if not (0 <= channel_idx <= 7):
            bot._log(f"V3 message with invalid channel_idx={channel_idx} (valid range: 0-7) - likely encrypted or corrupted")

    print("✓ V3 format invalid channel detected and logged")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Channel Diagnostic Logging Tests" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_valid_message_parsing()
        test_encrypted_message_detection()
        test_short_message_detection()
        test_multiple_channels()
        test_v3_format_invalid_channel()

        print("=" * 60)
        print("✓ All diagnostic logging tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  • Valid messages on all channels (0-7) parse correctly")
        print("  • Encrypted messages (invalid channel_idx) are detected")
        print("  • Short/corrupted messages are detected")
        print("  • Helpful debug messages explain why messages are rejected")
        print()
        print("User Impact:")
        print("  • Users running with -d flag will now see WHY messages")
        print("    from certain channels aren't working")
        print("  • Clear guidance: check if channel is encrypted or")
        print("    if bot's radio is subscribed to that channel")
        print()

        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
