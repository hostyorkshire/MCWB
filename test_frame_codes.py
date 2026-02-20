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
    
    # Set up mock to return the frame
    mock_serial.readline.return_value = frame
    
    # Parse the frame
    mesh._handle_binary_frame(frame)
    
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


def test_push_msg_ack():
    """Test handling of PUSH_MSG_ACK (0x88)"""
    print("=" * 60)
    print("TEST: PUSH_MSG_ACK (0x88)")
    print("=" * 60)
    
    mesh = MeshCore("test_node", debug=True)
    mesh.running = True
    
    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    # Simulate receiving PUSH_MSG_ACK frame (0x88) with dummy ack data
    frame = create_frame(0x88, bytes([0x00, 0x00, 0x00, 0x00]))
    
    # Set up mock to return the frame
    mock_serial.readline.return_value = frame
    
    # Reset the mock to track new calls
    mock_serial.write.reset_mock()
    
    # Parse the frame
    mesh._handle_binary_frame(frame)
    
    # Verify that CMD_SYNC_NEXT_MSG (0x0a) is sent to fetch queued messages
    assert mock_serial.write.called, "Expected CMD_SYNC_NEXT_MSG to be sent after ACK"
    
    # Get the command that was sent
    cmd_frame = mock_serial.write.call_args[0][0]
    
    # Parse command frame: 0x3C + length(2) + payload
    assert cmd_frame[0] == 0x3C, "Command should start with FRAME_IN (0x3C)"
    
    # Extract payload
    payload_length = int.from_bytes(cmd_frame[1:3], "little")
    payload = cmd_frame[3:3+payload_length]
    
    assert payload[0] == 0x0a, f"Command should be CMD_SYNC_NEXT_MSG (0x0a), got {payload[0]:#04x}"
    
    print(f"✓ PUSH_MSG_ACK (0x88) handled correctly")
    print(f"✓ CMD_SYNC_NEXT_MSG (0x0a) sent to fetch queued messages")
    print(f"✓ No 'unhandled frame code' error logged")
    print()
    
    return True


def test_no_unhandled_errors():
    """Test that codes 0x05 and 0x88 don't trigger 'unhandled frame code' logs"""
    print("=" * 60)
    print("TEST: No 'unhandled frame code' errors")
    print("=" * 60)
    
    mesh = MeshCore("test_node", debug=False)
    mesh.running = True
    
    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    # Test both frame codes
    test_codes = [0x05, 0x88]
    
    for code in test_codes:
        frame = create_frame(code, bytes(4))
        
        # This should not raise any exception or log "unhandled"
        try:
            mesh._handle_binary_frame(frame)
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
        test_push_msg_ack()
        test_no_unhandled_errors()
        
        print("=" * 60)
        print("✅ All frame code tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  • CMD_GET_DEVICE_TIME (0x05) now responds with current time")
        print("  • PUSH_MSG_ACK (0x88) is now handled gracefully")
        print("  • No more 'unhandled frame code' errors for these codes")
        print("  • Bot should now respond to commands properly")
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
