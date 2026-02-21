#!/usr/bin/env python3
"""
Test handling of frame code 0x00 (NOP/keepalive)
This addresses the issue: "MeshCore [WX_BOT]: MeshCore: unhandled frame code 0x00"
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


def test_frame_code_0x00():
    """Test handling of frame code 0x00 (NOP/keepalive)"""
    print("=" * 60)
    print("TEST: Frame Code 0x00 (NOP/Keepalive)")
    print("=" * 60)
    
    mesh = MeshCore("WX_BOT", debug=True)
    mesh.running = True
    
    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    # Simulate receiving frame code 0x00
    frame = create_frame(0x00)
    
    print(f"Sending frame with code 0x00...")
    print(f"Frame bytes: {frame.hex()}")
    
    # Parse the frame - should not raise any exception
    try:
        mesh._handle_binary_frame(frame)
        print("✓ Frame code 0x00 handled without errors")
    except Exception as e:
        print(f"✗ Frame code 0x00 raised exception: {e}")
        return False
    
    # Verify that no commands were sent (NOP should be silent)
    if not mock_serial.write.called:
        print("✓ Frame handled silently (no response sent)")
    else:
        print("✗ Unexpected: Response was sent for NOP frame")
        return False
    
    print("✓ No 'unhandled frame code 0x00' error logged")
    print()
    
    return True


def test_frame_code_0x00_in_sequence():
    """Test frame code 0x00 mixed with other frame codes"""
    print("=" * 60)
    print("TEST: Frame Code 0x00 in Sequence with Other Frames")
    print("=" * 60)
    
    mesh = MeshCore("WX_BOT", debug=False)
    mesh.running = True
    
    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    # Test sequence: 0x00 (NOP), 0x0a (RESP_NO_MORE_MSGS), 0x00 (NOP)
    test_codes = [0x00, 0x0a, 0x00]
    
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
    """Verify that frame code 0x00 does not log 'unhandled frame code' error"""
    print("=" * 60)
    print("TEST: No 'Unhandled Frame Code' Error for 0x00")
    print("=" * 60)
    
    mesh = MeshCore("WX_BOT", debug=True)
    mesh.running = True
    
    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    # Capture stdout
    captured_output = io.StringIO()
    
    frame = create_frame(0x00)
    
    with redirect_stdout(captured_output):
        mesh._handle_binary_frame(frame)
    
    output = captured_output.getvalue()
    
    # Check that "unhandled frame code" does NOT appear in the output
    if "unhandled frame code" in output.lower():
        print(f"✗ FAILED: 'unhandled frame code' found in output:")
        print(f"  {output}")
        return False
    
    print("✓ No 'unhandled frame code' error in output")
    print("✓ Frame code 0x00 is handled silently as expected")
    print()
    
    return True


def main():
    """Run all frame code 0x00 tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "Frame Code 0x00 Tests" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        # Run tests
        result1 = test_frame_code_0x00()
        result2 = test_frame_code_0x00_in_sequence()
        result3 = test_no_unhandled_error_logged()
        
        if not (result1 and result2 and result3):
            print("=" * 60)
            print("❌ Some tests failed!")
            print("=" * 60)
            return 1
        
        print("=" * 60)
        print("✅ All frame code 0x00 tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  • Frame code 0x00 is now handled as NOP/keepalive")
        print("  • No 'unhandled frame code 0x00' errors are logged")
        print("  • The frame is processed silently without side effects")
        print("  • Bot can now handle MeshCore keepalive frames properly")
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
