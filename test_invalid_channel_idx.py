#!/usr/bin/env python3
"""
Test to verify that messages with invalid channel indices are properly filtered.
This addresses the issue where encrypted/garbled messages with channel_idx > 7
were being logged and causing confusion.
"""

import sys
from weather_bot import WeatherBot


def test_invalid_channel_idx_filtering():
    """Test that invalid channel indices (outside 0-7 range) are rejected"""
    print("=" * 60)
    print("TEST: Invalid Channel Index Filtering")
    print("=" * 60)
    
    bot = WeatherBot(debug=True)
    
    # Test Case 1: Valid channel index (0-7)
    print("\n1. Testing valid channel indices (0-7):")
    for idx in range(8):
        # Old format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
        payload = bytes([0x88, idx, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) + b"Test message"
        channel_idx, text = bot._parse_channel_message(payload)
        print(f"   channel_idx={idx}: parsed as {channel_idx} ✓" if channel_idx is not None else f"   channel_idx={idx}: rejected ✗")
        assert channel_idx == idx, f"Valid channel_idx {idx} should be accepted"
        assert text == "Test message", f"Text should be parsed correctly"
    
    # Test Case 2: Invalid channel indices (outside 0-7 range)
    print("\n2. Testing invalid channel indices (> 7):")
    invalid_indices = [8, 10, 49, 50, 100, 255]
    for idx in invalid_indices:
        # Old format with invalid channel_idx and realistic header bytes
        # Format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
        import time
        ts = int(time.time()).to_bytes(4, "little")
        payload = bytes([0x88, idx, 0x05, 0x00]) + ts + b"Garbled data"
        channel_idx, text = bot._parse_channel_message(payload)
        print(f"   channel_idx={idx}: rejected ✓" if channel_idx is None else f"   channel_idx={idx}: accepted as {channel_idx} ✗")
        assert channel_idx is None, f"Invalid channel_idx {idx} should be rejected"
        assert text is None, f"Text should be None for invalid channel_idx"
    
    # Test Case 3: V3 format with valid channel index
    print("\n3. Testing V3 format with valid channel index:")
    # V3 format: code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    snr = 45  # Valid SNR value
    v3_payload = bytes([0x88, snr, 0x00, 0x00, 2, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) + b"V3 message"
    channel_idx, text = bot._parse_channel_message(v3_payload)
    print(f"   V3 format with channel_idx=2: parsed as {channel_idx} ✓" if channel_idx == 2 else f"   V3 format: rejected ✗")
    assert channel_idx == 2, "V3 format with valid channel_idx should be accepted"
    assert text == "V3 message", "V3 text should be parsed correctly"
    
    # Test Case 4: V3 format with invalid channel index
    print("\n4. Testing V3 format with invalid channel index:")
    # Even with valid SNR, invalid channel_idx should fall back to old format and be rejected
    v3_invalid_payload = bytes([0x88, snr, 0x00, 0x00, 50, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) + b"Invalid"
    channel_idx, text = bot._parse_channel_message(v3_invalid_payload)
    # This will fall back to old format where payload[1]=45 (SNR), which is invalid
    print(f"   V3 with invalid channel_idx: rejected ✓" if channel_idx is None else f"   parsed as {channel_idx} ✗")
    assert channel_idx is None, "V3 format with invalid channel_idx should be rejected"
    
    # Test Case 5: Simulated encrypted/garbled message
    print("\n5. Testing simulated encrypted/garbled message:")
    # Real-world encrypted messages have random bytes that can result in invalid channel_idx
    garbled_payload = bytes([0x88, 0xE9, 0x69, 0x26, 0x46, 0x41, 0x66, 0x46]) + b"\x78\x75\xd5\x95\x36\x32\x6b\x32"
    channel_idx, text = bot._parse_channel_message(garbled_payload)
    print(f"   Garbled message: rejected ✓" if channel_idx is None else f"   parsed as {channel_idx} ✗")
    assert channel_idx is None, "Garbled/encrypted message should be rejected"
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nMessages with invalid channel indices are now properly filtered.")
    print("This prevents encrypted/garbled messages from being logged.")
    print()


def main():
    """Run the test"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Invalid Channel Index Test" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_invalid_channel_idx_filtering()
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
