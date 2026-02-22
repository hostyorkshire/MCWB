#!/usr/bin/env python3
"""
Test edge cases for V3 format detection to ensure the improved heuristics
correctly handle ambiguous cases.
"""

import struct
import time
from weather_bot import WeatherBot


def create_message(code, byte1, byte2, byte3, byte4, text):
    """Create a test payload with specific byte values."""
    path_len = 0x00
    txt_type = 0x00
    timestamp = struct.pack('<I', int(time.time()))
    text_bytes = text.encode('utf-8')
    
    return bytes([code, byte1, byte2, byte3, byte4, path_len, txt_type]) + timestamp + text_bytes


def test_edge_cases():
    """Test edge cases for format detection."""
    print("=" * 80)
    print("EDGE CASE TESTING: Format Detection Heuristics")
    print("=" * 80)
    
    bot = WeatherBot(debug=False)
    
    # Test Case 1: Old format with channel_idx=2 (should NOT be detected as V3)
    print("\n[Test 1] Old format: channel_idx=2, short payload")
    payload = create_message(0x88, 2, 0x00, 0x00, 0xFF, "Alice: WX Leeds")
    channel_idx, text = bot._parse_channel_message(payload)
    assert channel_idx == 2, f"Expected channel_idx=2 (old format), got {channel_idx}"
    assert "Alice: WX Leeds" in text, f"Expected text to contain 'Alice: WX Leeds', got '{text}'"
    print(f"✅ Correctly parsed as old format: channel_idx={channel_idx}")
    
    # Test Case 2: V3 format with SNR=49, channel_idx=1 (should be detected as V3)
    print("\n[Test 2] V3 format: SNR=49, channel_idx=1")
    payload = create_message(0x88, 49, 0x00, 0x00, 1, "Bob: weather Manchester")
    # Need to add extra bytes to make it look like V3 (text starts at position 11)
    # Insert 3 more bytes before text
    payload = payload[:7] + struct.pack('<I', int(time.time())) + b"Bob: weather Manchester"
    channel_idx, text = bot._parse_channel_message(payload)
    assert channel_idx == 1, f"Expected channel_idx=1 (V3 format), got {channel_idx}"
    print(f"✅ Correctly detected V3 format: SNR=49, channel_idx={channel_idx}")
    
    # Test Case 3: Ambiguous case - byte1=5 (valid channel in old format, mid-range SNR in V3)
    # If byte4=2 (valid channel), but SNR=5 is too low (< 20), should fall back to old format
    print("\n[Test 3] Ambiguous: byte1=5 (could be channel or low SNR), byte4=2")
    payload = create_message(0x88, 5, 0x00, 0x00, 2, "Carol: WX York")
    channel_idx, text = bot._parse_channel_message(payload)
    # SNR=5 is outside typical range (20-60), so should use old format
    # But also check if byte1 > 7 (which it isn't), so should use old format
    assert channel_idx == 5, f"Expected channel_idx=5 (old format), got {channel_idx}"
    print(f"✅ Correctly used old format: channel_idx={channel_idx}")
    
    # Test Case 4: V3 with high SNR=55, channel_idx=3 (should be detected as V3)
    print("\n[Test 4] V3 format: SNR=55, channel_idx=3")
    payload = create_message(0x88, 55, 0x00, 0x00, 3, "Dave: WX Birmingham")
    # Need proper V3 format
    payload = payload[:7] + struct.pack('<I', int(time.time())) + b"Dave: WX Birmingham"
    channel_idx, text = bot._parse_channel_message(payload)
    assert channel_idx == 3, f"Expected channel_idx=3 (V3 format), got {channel_idx}"
    print(f"✅ Correctly detected V3 format: SNR=55, channel_idx={channel_idx}")
    
    # Test Case 5: Byte1=10 (impossible as channel in old format), byte4=1
    # Should be detected as V3 even if SNR is outside typical range
    print("\n[Test 5] V3 format: byte1=10 (>7, must be SNR), channel_idx=1")
    payload = create_message(0x88, 10, 0x00, 0x00, 1, "Eve: weather Glasgow")
    # Need proper V3 format
    payload = payload[:7] + struct.pack('<I', int(time.time())) + b"Eve: weather Glasgow"
    channel_idx, text = bot._parse_channel_message(payload)
    assert channel_idx == 1, f"Expected channel_idx=1 (V3 format), got {channel_idx}"
    print(f"✅ Correctly detected V3 format: byte1=10 (>7), channel_idx={channel_idx}")
    
    # Test Case 6: Byte1=8 (impossible as channel), should be V3
    print("\n[Test 6] V3 format: byte1=8 (>7, must be SNR), channel_idx=0")
    payload = create_message(0x88, 8, 0x00, 0x00, 0, "Frank: WX Edinburgh")
    # Need proper V3 format
    payload = payload[:7] + struct.pack('<I', int(time.time())) + b"Frank: WX Edinburgh"
    channel_idx, text = bot._parse_channel_message(payload)
    assert channel_idx == 0, f"Expected channel_idx=0 (V3 format), got {channel_idx}"
    print(f"✅ Correctly detected V3 format: byte1=8 (>7), channel_idx={channel_idx}")
    
    print("\n" + "=" * 80)
    print("✅ ALL EDGE CASE TESTS PASSED!")
    print("=" * 80)
    print("\nThe improved heuristics correctly handle:")
    print("  • Old format messages (channel_idx at position 1)")
    print("  • V3 format messages with typical SNR range (20-60)")
    print("  • V3 format messages with SNR > 7 (impossible as channel_idx)")
    print("  • Ambiguous cases (prefer old format when SNR is atypical)")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_edge_cases()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
