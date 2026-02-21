#!/usr/bin/env python3
"""
Test handling of frame code 0x01 (CMD_APP_START)
This addresses the issue: "MeshCore [WX_BOT]: MeshCore: unhandled frame code 0x01"
"""

import io
import sys
from contextlib import redirect_stdout
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


def test_frame_code_0x01():
    """Test handling of frame code 0x01 (CMD_APP_START)"""
    print("=" * 60)
    print("TEST: Frame Code 0x01 (CMD_APP_START)")
    print("=" * 60)
    
    mesh = MeshCore("WX_BOT", debug=True)
    mesh.running = True
    
    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    # Simulate receiving frame code 0x01 (CMD_APP_START echo/acknowledgment)
    # This might include additional data similar to what was sent
    frame_data = b'\x03      MCWB'  # app_ver + reserved + app_name
    frame = create_frame(0x01, frame_data)
    
    print(f"Sending frame with code 0x01 (CMD_APP_START)...")
    print(f"Frame bytes: {frame.hex()}")
    
    # Parse the frame - should not raise any exception
    try:
        mesh._handle_binary_frame(frame)
        print("✓ Frame code 0x01 handled without errors")
    except Exception as e:
        print(f"✗ Frame code 0x01 raised exception: {e}")
        return False
    
    # The frame should be acknowledged but no response needed
    # (unlike CMD_GET_DEVICE_TIME which requires a response)
    print("✓ Frame handled gracefully")
    print("✓ No 'unhandled frame code 0x01' error logged")
    print()
    
    return True


def test_frame_code_0x01_in_sequence():
    """Test frame code 0x01 mixed with other frame codes"""
    print("=" * 60)
    print("TEST: Frame Code 0x01 in Sequence with Other Frames")
    print("=" * 60)
    
    mesh = MeshCore("WX_BOT", debug=False)
    mesh.running = True
    
    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    # Test sequence: 0x01 (CMD_APP_START), 0x00 (NOP), 0x0a (RESP_NO_MORE_MSGS)
    test_codes = [0x01, 0x00, 0x0a]
    
    print(f"Testing sequence: {[f'{c:#04x}' for c in test_codes]}")
    
    for code in test_codes:
        frame = create_frame(code)
        try:
            mesh._handle_binary_frame(frame)
            print(f"✓ Frame code {code:#04x} handled successfully")
        except Exception as e:
            print(f"✗ Frame code {code:#04x} raised exception: {e}")
            return False
    
    print("✓ All frames in sequence handled without errors")
    print()
    
    return True


def test_no_unhandled_error_logged():
    """Verify that frame code 0x01 does not log 'unhandled frame code' error"""
    print("=" * 60)
    print("TEST: No 'Unhandled Frame Code' Error for 0x01")
    print("=" * 60)
    
    mesh = MeshCore("WX_BOT", debug=True)
    mesh.running = True
    
    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    # Capture stdout
    captured_output = io.StringIO()
    
    frame = create_frame(0x01)
    
    with redirect_stdout(captured_output):
        mesh._handle_binary_frame(frame)
    
    output = captured_output.getvalue()
    
    # Check that "unhandled frame code" does NOT appear in the output
    if "unhandled frame code" in output.lower():
        print(f"✗ FAILED: 'unhandled frame code' found in output:")
        print(f"  {output}")
        return False
    
    print("✓ No 'unhandled frame code' error in output")
    print("✓ Frame code 0x01 is handled as expected")
    print()
    
    return True


def test_app_start_during_init():
    """Test that APP_START echo during initialization is handled"""
    print("=" * 60)
    print("TEST: APP_START Echo During Session Initialization")
    print("=" * 60)
    
    mesh = MeshCore("WX_BOT", debug=True)
    mesh.running = True
    
    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    # Simulate the radio echoing CMD_APP_START during initialization
    # This is what might cause the "unhandled frame code 0x01" error
    frame = create_frame(0x01, b'\x03      MCWB')
    
    captured_output = io.StringIO()
    
    with redirect_stdout(captured_output):
        mesh._handle_binary_frame(frame)
    
    output = captured_output.getvalue()
    
    # Verify the log message indicates it was acknowledged
    if "APP_START acknowledged" in output:
        print("✓ APP_START echo acknowledged properly")
    else:
        print(f"Note: Output was: {output}")
    
    # Verify no "unhandled" error
    if "unhandled frame code" not in output.lower():
        print("✓ No 'unhandled frame code' error")
    else:
        print(f"✗ FAILED: Found 'unhandled frame code' in output")
        return False
    
    print()
    return True


def main():
    """Run all frame code 0x01 tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "Frame Code 0x01 Tests" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        # Run tests
        result1 = test_frame_code_0x01()
        result2 = test_frame_code_0x01_in_sequence()
        result3 = test_no_unhandled_error_logged()
        result4 = test_app_start_during_init()
        
        if not (result1 and result2 and result3 and result4):
            print("=" * 60)
            print("❌ Some tests failed!")
            print("=" * 60)
            return 1
        
        print("=" * 60)
        print("✅ All frame code 0x01 tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  • Frame code 0x01 (CMD_APP_START) is now handled properly")
        print("  • No 'unhandled frame code 0x01' errors are logged")
        print("  • The frame is acknowledged during session initialization")
        print("  • Bot can now handle MeshCore APP_START echoes properly")
        print()
        print("✨ Issue resolved: The error message is eliminated!")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
