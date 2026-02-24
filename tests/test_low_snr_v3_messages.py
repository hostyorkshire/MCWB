#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

"""
Test to verify that V3 format messages with low SNR values are correctly parsed.

This test addresses the issue from the problem statement where messages with
low SNR values (0, 1, 2, etc.) were being misparsed as OLD format, causing
the bot to not respond to weather commands.
"""

import struct
import time
from unittest.mock import MagicMock
from weather_bot import WeatherBot


def create_v3_channel_message(channel_idx, snr, text):
    """
    Create a V3 format PUSH_CHAN_MSG payload.
    Format: code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    """
    code = 0x88  # PUSH_CHAN_MSG
    reserved = b'\x00\x00'
    path_len = 0x00
    txt_type = 0x00
    timestamp = struct.pack('<I', int(time.time()))
    text_bytes = text.encode('utf-8')

    payload = bytes([code, snr, reserved[0], reserved[1], channel_idx, path_len, txt_type]) + timestamp + text_bytes
    return payload


def test_low_snr_v3_messages():
    """Test that V3 messages with low SNR values (0-7) are correctly parsed."""
    print("=" * 80)
    print("TEST: V3 Format Detection with Low SNR Values")
    print("=" * 80)
    print("\nThis test verifies the fix for messages with SNR < 20")
    print("that were previously misparsed as OLD format.\n")

    bot = WeatherBot(debug=True)

    # Mock the serial connection and sending
    bot._ser = MagicMock()
    sent_messages = []

    def mock_send_channel_msg(text, channel_idx):
        sent_messages.append({'text': text, 'channel_idx': channel_idx})

    bot._send_channel_msg = mock_send_channel_msg
    bot._send_cmd = MagicMock()

    # Test Case 1: V3 format with SNR=0, channel_idx=0
    print("[Test Case 1] V3 format: SNR=0, channel_idx=0, text='WX Leeds'")
    payload = create_v3_channel_message(channel_idx=0, snr=0, text="WX Leeds")
    print(f"  Payload: {payload.hex()}")
    print(f"  Byte 1 (SNR): {payload[1]}")
    print(f"  Byte 2-3 (reserved): {payload[2]:02x} {payload[3]:02x}")
    print(f"  Byte 4 (channel_idx): {payload[4]}")

    bot._dispatch(payload)

    assert len(sent_messages) == 1, f"Expected 1 response, got {len(sent_messages)}"
    assert sent_messages[0]['channel_idx'] == 0, f"Expected channel_idx=0, got {sent_messages[0]['channel_idx']}"
    assert "Leeds" in sent_messages[0]['text'], "Expected weather response for Leeds"
    print(f"✓ Bot correctly responded on channel_idx=0")
    print(f"✓ Response contains: {sent_messages[0]['text'][:50]}...\n")

    # Test Case 2: V3 format with SNR=1, channel_idx=1
    print("[Test Case 2] V3 format: SNR=1, channel_idx=1, text='weather London'")
    sent_messages.clear()
    payload = create_v3_channel_message(channel_idx=1, snr=1, text="weather London")
    print(f"  Payload: {payload.hex()}")
    print(f"  Byte 1 (SNR): {payload[1]}")
    print(f"  Byte 2-3 (reserved): {payload[2]:02x} {payload[3]:02x}")
    print(f"  Byte 4 (channel_idx): {payload[4]}")

    bot._dispatch(payload)

    assert len(sent_messages) == 1, f"Expected 1 response, got {len(sent_messages)}"
    assert sent_messages[0]['channel_idx'] == 1, f"Expected channel_idx=1, got {sent_messages[0]['channel_idx']}"
    assert "London" in sent_messages[0]['text'], "Expected weather response for London"
    print(f"✓ Bot correctly responded on channel_idx=1")
    print(f"✓ Response contains: {sent_messages[0]['text'][:50]}...\n")

    # Test Case 3: V3 format with SNR=5, channel_idx=2
    print("[Test Case 3] V3 format: SNR=5, channel_idx=2, text='TestUser: WX York'")
    sent_messages.clear()
    payload = create_v3_channel_message(channel_idx=2, snr=5, text="TestUser: WX York")
    print(f"  Payload: {payload.hex()}")
    print(f"  Byte 1 (SNR): {payload[1]}")
    print(f"  Byte 2-3 (reserved): {payload[2]:02x} {payload[3]:02x}")
    print(f"  Byte 4 (channel_idx): {payload[4]}")

    bot._dispatch(payload)

    assert len(sent_messages) == 1, f"Expected 1 response, got {len(sent_messages)}"
    assert sent_messages[0]['channel_idx'] == 2, f"Expected channel_idx=2, got {sent_messages[0]['channel_idx']}"
    assert "York" in sent_messages[0]['text'], "Expected weather response for York"
    print(f"✓ Bot correctly responded on channel_idx=2")
    print(f"✓ Response contains: {sent_messages[0]['text'][:50]}...\n")

    # Test Case 4: V3 format with SNR=7 (edge case), channel_idx=3
    print("[Test Case 4] V3 format: SNR=7, channel_idx=3, text='WX Manchester'")
    sent_messages.clear()
    payload = create_v3_channel_message(channel_idx=3, snr=7, text="WX Manchester")

    bot._dispatch(payload)

    assert len(sent_messages) == 1, f"Expected 1 response, got {len(sent_messages)}"
    assert sent_messages[0]['channel_idx'] == 3, f"Expected channel_idx=3, got {sent_messages[0]['channel_idx']}"
    assert "Manchester" in sent_messages[0]['text'], "Expected weather response for Manchester"
    print(f"✓ Bot correctly responded on channel_idx=3\n")

    print("=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nThe fix correctly handles:")
    print("  • V3 format messages with SNR values 0-7")
    print("  • Messages with and without 'SenderName:' prefix")
    print("  • Weather commands on any channel")
    print("\nThe bot now uses reserved bytes (0x00 0x00) to distinguish V3 from OLD format")
    print("when SNR values are in the ambiguous range (0-7).")


def test_high_snr_still_works():
    """Test that high SNR V3 messages still work (regression test)."""
    print("\n" + "=" * 80)
    print("TEST: High SNR V3 Messages (Regression Test)")
    print("=" * 80)

    bot = WeatherBot(debug=True)
    bot._ser = MagicMock()
    sent_messages = []

    def mock_send_channel_msg(text, channel_idx):
        sent_messages.append({'text': text, 'channel_idx': channel_idx})

    bot._send_channel_msg = mock_send_channel_msg
    bot._send_cmd = MagicMock()

    # Test with high SNR values (existing heuristic)
    print("\n[Test Case] V3 format: SNR=35, channel_idx=1, text='WX Leeds'")
    payload = create_v3_channel_message(channel_idx=1, snr=35, text="WX Leeds")
    bot._dispatch(payload)

    assert len(sent_messages) == 1, f"Expected 1 response, got {len(sent_messages)}"
    assert sent_messages[0]['channel_idx'] == 1, f"Expected channel_idx=1"
    print(f"✓ High SNR messages still work correctly\n")


def main():
    """Run all tests."""
    try:
        test_low_snr_v3_messages()
        test_high_snr_still_works()

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED - FIX VERIFIED!")
        print("=" * 80)
        print("\nThe bot now correctly handles V3 messages with any SNR value (0-60).")
        print("Messages with low SNR that were previously ignored will now get responses.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
