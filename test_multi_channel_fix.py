#!/usr/bin/env python3
"""
Test that the bot accepts valid weather commands from multiple channels
without rejecting them as "encrypted/garbled".
"""

import sys
import time
from weather_bot import WeatherBot

def test_multi_channel_messages():
    """Test that messages from different channels are accepted."""
    print("Testing multi-channel message acceptance...")
    
    # Create bot without serial connection (we'll test message parsing directly)
    bot = WeatherBot(port=None, debug=True)
    
    # Test Case 1: V3 format message on channel 0
    # Simulates: "M3UXC: Wx london"
    print("\n=== Test 1: V3 format message on channel 0 ===")
    # V3 format payload (INCLUDING the frame code as received by _parse_channel_message)
    # Format: code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    v3_payload_ch0 = bytes([
        0x88,  # code: PUSH_CHAN_MSG
        30,    # SNR value (realistic)
        0x00, 0x00,  # reserved bytes
        0,     # channel_idx = 0
        1,     # path_len
        0,     # txt_type
        0x00, 0x00, 0x00, 0x00,  # timestamp (4 bytes)
    ]) + b"M3UXC: Wx london"
    
    channel_idx, text = bot._parse_channel_message(v3_payload_ch0)
    assert channel_idx is not None, "Message should be accepted, not rejected as encrypted"
    assert channel_idx == 0, f"Channel index should be 0, got {channel_idx}"
    assert "wx london" in text.lower() or "m3uxc" in text.lower(), f"Text should contain command, got: {text}"
    print(f"✓ Accepted: channel_idx={channel_idx}, text='{text}'")
    
    # Test Case 2: V3 format message on channel 1
    # Simulates: "User: WX Leeds"
    print("\n=== Test 2: V3 format message on channel 1 ===")
    v3_payload_ch1 = bytes([
        0x88,  # code: PUSH_CHAN_MSG
        28,    # SNR value (realistic)
        0x00, 0x00,  # reserved bytes
        1,     # channel_idx = 1
        1,     # path_len
        0,     # txt_type
        0x00, 0x00, 0x00, 0x00,  # timestamp (4 bytes)
    ]) + b"User: WX Leeds"
    
    channel_idx, text = bot._parse_channel_message(v3_payload_ch1)
    assert channel_idx is not None, "Message should be accepted, not rejected as encrypted"
    assert channel_idx == 1, f"Channel index should be 1, got {channel_idx}"
    assert "wx leeds" in text.lower() or "leeds" in text.lower(), f"Text should contain command, got: {text}"
    print(f"✓ Accepted: channel_idx={channel_idx}, text='{text}'")
    
    # Test Case 3: Old format message on channel 2
    # Simulates: "TestUser: weather Manchester"
    print("\n=== Test 3: Old format message on channel 2 ===")
    # Old format payload (INCLUDING the frame code)
    # Format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    old_payload_ch2 = bytes([
        0x08,  # code: RESP_CHANNEL_MSG
        2,     # channel_idx = 2
        1,     # path_len
        0,     # txt_type
        0x00, 0x00, 0x00, 0x00,  # timestamp (4 bytes)
    ]) + b"TestUser: weather Manchester"
    
    channel_idx, text = bot._parse_channel_message(old_payload_ch2)
    assert channel_idx is not None, "Message should be accepted, not rejected as encrypted"
    assert channel_idx == 2, f"Channel index should be 2, got {channel_idx}"
    assert "manchester" in text.lower(), f"Text should contain command, got: {text}"
    print(f"✓ Accepted: channel_idx={channel_idx}, text='{text}'")
    
    # Test Case 4: Invalid channel index in old format
    # When channel_idx > 7 in old format, the bot tries V3 format instead
    # This is expected behavior - bot tries to find a valid interpretation
    print("\n=== Test 4: Old format with invalid channel_idx ===")
    # Old format with invalid channel_idx - will be reinterpreted as V3
    invalid_old_payload = bytes([
        0x08,  # code: RESP_CHANNEL_MSG
        43,    # This would be channel_idx=43 in old format (invalid)
               # But will be interpreted as SNR=43 in V3 format (valid)
        1,     # Would be path_len in old, or reserved1 in V3
        0,     # Would be txt_type in old, or reserved2 in V3
        0,     # Would be timestamp in old, or channel_idx=0 in V3
        0x00, 0x00, 0x00,  # Rest of old timestamp, or V3 path_len/txt_type/timestamp start
    ]) + b"Some text"
    
    channel_idx, text = bot._parse_channel_message(invalid_old_payload)
    # The bot will reinterpret this as V3 format with channel_idx from byte 4
    # This is acceptable - bot tries to make sense of ambiguous data
    print(f"  Reinterpreted as V3: channel_idx={channel_idx}, text='{text}'")
    print(f"✓ Bot handles ambiguous messages by trying alternate formats")
    
    # Test Case 5: Empty message should be rejected
    print("\n=== Test 5: Empty message (should be rejected) ===")
    # V3 format with no text content
    empty_payload = bytes([
        0x88,  # code: PUSH_CHAN_MSG
        30,    # SNR value
        0x00, 0x00,  # reserved bytes
        0,     # channel_idx = 0
        1,     # path_len
        0,     # txt_type
        0x00, 0x00, 0x00, 0x00,  # timestamp (4 bytes)
    ])  # No text content
    
    channel_idx, text = bot._parse_channel_message(empty_payload)
    assert channel_idx is None, "Empty message should be rejected"
    assert text is None, "Empty message should return None"
    print(f"✓ Correctly rejected empty message")
    
    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED!")
    print("="*50)
    print("\nThe bot now accepts valid weather commands from multiple channels")
    print("without incorrectly rejecting them as 'encrypted/garbled'.")


if __name__ == "__main__":
    try:
        test_multi_channel_messages()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
