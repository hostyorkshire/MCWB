#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

"""
Test to verify that weather_bot correctly handles both old and V3 format
for PUSH_CHAN_MSG (0x88) and RESP_CHANNEL_MSG (0x08) frames.

This test addresses the issue where messages on channels 49/51 were being
misinterpreted due to SNR values being read as channel indices.
"""

import struct
import time
from unittest.mock import MagicMock, patch
from weather_bot import WeatherBot


def create_v3_channel_message(channel_idx, snr, sender, message_text):
    """
    Create a V3 format PUSH_CHAN_MSG payload.
    Format: code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    """
    code = 0x88  # PUSH_CHAN_MSG
    reserved = b'\x00\x00'
    path_len = 0x00
    txt_type = 0x00
    timestamp = struct.pack('<I', int(time.time()))
    text = f"{sender}: {message_text}".encode('utf-8')

    payload = bytes([code, snr, reserved[0], reserved[1], channel_idx, path_len, txt_type]) + timestamp + text
    return payload


def create_old_channel_message(channel_idx, sender, message_text):
    """
    Create old format PUSH_CHAN_MSG payload.
    Format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    """
    code = 0x88  # PUSH_CHAN_MSG
    path_len = 0x00
    txt_type = 0x00
    timestamp = struct.pack('<I', int(time.time()))
    text = f"{sender}: {message_text}".encode('utf-8')

    payload = bytes([code, channel_idx, path_len, txt_type]) + timestamp + text
    return payload


def test_v3_format_with_high_snr():
    """Test that messages with high SNR values (49, 51) are correctly parsed as V3 format."""
    print("=" * 70)
    print("TEST: V3 Format Detection with High SNR Values")
    print("=" * 70)

    bot = WeatherBot(debug=True)

    # Mock the serial connection and sending
    bot._ser = MagicMock()
    bot._send_cmd = MagicMock()

    # Track handled messages
    handled_messages = []
    original_handle = bot._handle_channel_message

    def mock_handle(text, channel_idx):
        handled_messages.append({'text': text, 'channel_idx': channel_idx})
        original_handle(text, channel_idx)

    bot._handle_channel_message = mock_handle

    # Test Case 1: V3 format with SNR=49, channel_idx=1
    print("\n[Test Case 1] V3 format: SNR=49, channel_idx=1")
    payload = create_v3_channel_message(channel_idx=1, snr=49, sender="TestUser", message_text="WX Leeds")
    bot._dispatch(payload)

    assert len(handled_messages) == 1, f"Expected 1 message, got {len(handled_messages)}"
    assert handled_messages[0]['channel_idx'] == 1, f"Expected channel_idx=1, got {handled_messages[0]['channel_idx']}"
    assert "WX Leeds" in handled_messages[0]['text'], "Expected 'WX Leeds' in message text"
    print(f"✓ Correctly parsed: channel_idx={handled_messages[0]['channel_idx']}, text='{handled_messages[0]['text']}'")

    # Test Case 2: V3 format with SNR=51, channel_idx=2
    print("\n[Test Case 2] V3 format: SNR=51, channel_idx=2")
    handled_messages.clear()
    payload = create_v3_channel_message(channel_idx=2, snr=51, sender="TestUser", message_text="weather London")
    bot._dispatch(payload)

    assert len(handled_messages) == 1, f"Expected 1 message, got {len(handled_messages)}"
    assert handled_messages[0]['channel_idx'] == 2, f"Expected channel_idx=2, got {handled_messages[0]['channel_idx']}"
    assert "weather London" in handled_messages[0]['text'], "Expected 'weather London' in message text"
    print(f"✓ Correctly parsed: channel_idx={handled_messages[0]['channel_idx']}, text='{handled_messages[0]['text']}'")

    print("\n✅ All V3 format tests passed!")


def test_old_format_still_works():
    """Test that old format messages (without SNR) still work correctly."""
    print("\n" + "=" * 70)
    print("TEST: Old Format Backward Compatibility")
    print("=" * 70)

    bot = WeatherBot(debug=True)

    # Mock the serial connection and sending
    bot._ser = MagicMock()
    bot._send_cmd = MagicMock()

    # Track handled messages
    handled_messages = []
    original_handle = bot._handle_channel_message

    def mock_handle(text, channel_idx):
        handled_messages.append({'text': text, 'channel_idx': channel_idx})
        original_handle(text, channel_idx)

    bot._handle_channel_message = mock_handle

    # Test Case: Old format with channel_idx=3
    print("\n[Test Case] Old format: channel_idx=3")
    payload = create_old_channel_message(channel_idx=3, sender="TestUser", message_text="WX Manchester")
    bot._dispatch(payload)

    assert len(handled_messages) == 1, f"Expected 1 message, got {len(handled_messages)}"
    assert handled_messages[0]['channel_idx'] == 3, f"Expected channel_idx=3, got {handled_messages[0]['channel_idx']}"
    assert "WX Manchester" in handled_messages[0]['text'], "Expected 'WX Manchester' in message text"
    print(f"✓ Correctly parsed: channel_idx={handled_messages[0]['channel_idx']}, text='{handled_messages[0]['text']}'")

    print("\n✅ Old format backward compatibility test passed!")


def test_v3_format_with_invalid_channel():
    """Test that V3 format with invalid channel_idx (>7) falls back to old format parsing."""
    print("\n" + "=" * 70)
    print("TEST: V3 Format Fallback for Invalid Channel Index")
    print("=" * 70)

    bot = WeatherBot(debug=True)

    # Mock the serial connection and sending
    bot._ser = MagicMock()
    bot._send_cmd = MagicMock()

    # Track handled messages
    handled_messages = []
    original_handle = bot._handle_channel_message

    def mock_handle(text, channel_idx):
        handled_messages.append({'text': text, 'channel_idx': channel_idx})
        original_handle(text, channel_idx)

    bot._handle_channel_message = mock_handle

    # Create a payload that looks like V3 format but has invalid channel_idx at position 4
    # This should trigger fallback to old format
    print("\n[Test Case] V3-length payload with invalid channel_idx at position 4")
    code = 0x88
    # In old format: channel_idx is at position 1
    # In V3 format: SNR at position 1, channel_idx at position 4
    # We set position 4 to an invalid value (10 > 7) to trigger old format parsing
    payload = bytes([code, 5, 0x00, 0x00, 10, 0x00, 0x00]) + struct.pack('<I', int(time.time())) + b"TestUser: WX York"

    bot._dispatch(payload)

    assert len(handled_messages) == 1, f"Expected 1 message, got {len(handled_messages)}"
    # Should fall back to reading channel_idx from position 1, which is 5
    assert handled_messages[0]['channel_idx'] == 5, f"Expected channel_idx=5 (fallback), got {handled_messages[0]['channel_idx']}"
    print(f"✓ Correctly fell back to old format: channel_idx={handled_messages[0]['channel_idx']}")

    print("\n✅ Fallback mechanism test passed!")


def main():
    """Run all tests."""
    try:
        test_v3_format_with_high_snr()
        test_old_format_still_works()
        test_v3_format_with_invalid_channel()

        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\nThe fix correctly handles:")
        print("  • V3 format messages with SNR values (49, 51, etc.)")
        print("  • Old format messages (backward compatible)")
        print("  • Fallback when V3 format has invalid channel_idx")
        print("\nThe bot should now correctly respond to messages on any channel.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
