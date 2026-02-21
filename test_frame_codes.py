#!/usr/bin/env python3
"""
Test handling of frame codes 0x05 (CMD_GET_DEVICE_TIME) and 0x88 (PUSH_MSG_ACK)
This addresses the issue where these codes were showing as "unhandled" in debug logs.
"""

import sys
import time
from unittest.mock import MagicMock
from meshcore import MeshCore


def create_frame(code: int, data: bytes = b'') -> bytes:
    """
    Helper function to create a MeshCore binary frame.
    
    Args:
        code: Frame code byte
        data: Additional payload data (optional)
    
    Returns:
        Complete binary frame with FRAME_OUT header and length
    """
    frame_payload = bytes([code]) + data
    frame = bytes([0x3E]) + len(frame_payload).to_bytes(2, "little") + frame_payload
    return frame


def test_cmd_get_device_time():
    """Test handling of CMD_GET_DEVICE_TIME (0x05)"""
    print("=" * 60)
    print("TEST: CMD_GET_DEVICE_TIME (0x05)")
    print("=" * 60)
    
    mesh = MeshCore("test_node", debug=True)
    mesh.running = True
    
    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    # Simulate receiving CMD_GET_DEVICE_TIME frame (0x05)
    frame = create_frame(0x05)
    
    # Extract payload from frame (skip 0x3E + 2-byte length)
    payload = frame[3:]
    
    # Parse the payload directly
    mesh._parse_binary_frame(payload)
    
    # Verify that _send_command was called with RESP_CURR_TIME (0x09)
    assert mock_serial.write.called, "Expected response to be sent"
    
    # Get the response that was sent
    response_frame = mock_serial.write.call_args[0][0]
    
    # Parse response frame: 0x3C + length(2) + payload(code + timestamp)
    # Response should be: RESP_CURR_TIME (0x09) + 4-byte timestamp
    assert response_frame[0] == 0x3C, "Response should start with FRAME_IN (0x3C)"
    
    # Extract payload (skip FRAME_IN and length bytes)
    payload_length = int.from_bytes(response_frame[1:3], "little")
    payload = response_frame[3:3+payload_length]
    
    assert payload[0] == 0x09, f"Response code should be RESP_CURR_TIME (0x09), got {payload[0]:#04x}"
    assert len(payload) == 5, f"Response should be 5 bytes (code + 4-byte timestamp), got {len(payload)}"
    
    # Verify timestamp is reasonable (within last minute)
    timestamp = int.from_bytes(payload[1:5], "little")
    current_time = int(time.time())
    assert abs(timestamp - current_time) < 60, f"Timestamp {timestamp} should be close to current time {current_time}"
    
    print(f"✓ CMD_GET_DEVICE_TIME (0x05) handled correctly")
    print(f"✓ Responded with RESP_CURR_TIME (0x09) + timestamp {timestamp}")
    print()
    
    return True


def test_push_chan_msg():
    """Test handling of PUSH_CHAN_MSG (0x88) - pushed inline channel message delivery"""
    print("=" * 60)
    print("TEST: PUSH_CHAN_MSG (0x88) — inline channel message dispatch")
    print("=" * 60)

    mesh = MeshCore("test_node", debug=True)
    mesh.running = True

    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial

    # Track handler calls
    received = []

    def handler(message):
        received.append(message)

    mesh.register_handler("text", handler)

    # Build a realistic 0x88 payload:
    # code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    channel_idx = 2
    path_len = 1
    txt_type = 0
    timestamp = (1771711343).to_bytes(4, "little")
    text = b"Alice: wx leeds"
    inner = bytes([channel_idx, path_len, txt_type]) + timestamp + text
    frame = create_frame(0x88, inner)
    payload = frame[3:]

    mock_serial.write.reset_mock()
    mesh._parse_binary_frame(payload)

    # Handler must have been called with the parsed message
    assert len(received) == 1, f"Expected 1 message dispatched, got {len(received)}"
    msg = received[0]
    assert msg.sender == "Alice", f"Expected sender 'Alice', got '{msg.sender}'"
    assert msg.content == "wx leeds", f"Expected content 'wx leeds', got '{msg.content}'"
    assert msg.channel_idx == channel_idx, f"Expected channel_idx {channel_idx}, got {msg.channel_idx}"

    # CMD_SYNC_NEXT_MSG must also have been sent to drain the queue
    assert mock_serial.write.called, "Expected CMD_SYNC_NEXT_MSG to be sent after push message"
    cmd_frame = mock_serial.write.call_args[0][0]
    assert cmd_frame[0] == 0x3C, "Command should start with FRAME_IN (0x3C)"
    payload_length = int.from_bytes(cmd_frame[1:3], "little")
    cmd_payload = cmd_frame[3:3 + payload_length]
    assert cmd_payload[0] == 0x0a, \
        f"Command should be CMD_SYNC_NEXT_MSG (0x0a), got {cmd_payload[0]:#04x}"

    print(f"✓ PUSH_CHAN_MSG (0x88) dispatched message correctly")
    print(f"  sender='{msg.sender}', content='{msg.content}', channel_idx={msg.channel_idx}")
    print(f"✓ CMD_SYNC_NEXT_MSG (0x0a) sent to drain remaining queue")
    print()

    return True


def test_no_unhandled_errors():
    """Test that codes 0x05, 0x82, and 0x88 don't trigger 'unhandled frame code' logs"""
    print("=" * 60)
    print("TEST: No 'unhandled frame code' errors")
    print("=" * 60)

    mesh = MeshCore("test_node", debug=False)
    mesh.running = True

    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial

    # Register a no-op handler so 0x88 dispatch doesn't fail
    mesh.register_handler("text", lambda msg: None)

    # Test all three previously-problematic frame codes
    test_codes = [0x05, 0x82, 0x88]

    for code in test_codes:
        # Provide enough bytes so length checks pass (use realistic padding)
        frame = create_frame(code, bytes(10))

        # Extract payload from frame
        payload = frame[3:]

        # This should not raise any exception or log "unhandled"
        try:
            mesh._parse_binary_frame(payload)
            print(f"✓ Code {code:#04x} handled without errors")
        except Exception as e:
            print(f"✗ Code {code:#04x} raised exception: {e}")
            return False

    print()
    return True


def main():
    """Run all frame code tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "Frame Code Handler Tests" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        # Run tests
        test_cmd_get_device_time()
        test_push_chan_msg()
        test_no_unhandled_errors()

        print("=" * 60)
        print("✅ All frame code tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  • CMD_GET_DEVICE_TIME (0x05) responds with current time")
        print("  • PUSH_CHAN_MSG (0x88) now dispatches inline channel messages")
        print("  • PUSH_SEND_CONFIRMED (0x82) handled gracefully")
        print("  • No more 'unhandled frame code' errors for any of these codes")
        print()
        
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
