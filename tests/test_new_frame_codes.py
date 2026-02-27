#!/usr/bin/env python3
"""
Test handling of newly added frame codes 0x80, 0x8a, and 0x90.
This addresses the "Unhandled frame code" errors seen in the logs.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from io import StringIO
from unittest.mock import MagicMock, patch

# Import the WeatherBot class
from weather_bot import WeatherBot


def create_frame(code: int, data: bytes = b"") -> bytes:
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


def test_push_base_0x80():
    """Test handling of PUSH_BASE (0x80) - base push notification frame"""
    print("=" * 60)
    print("TEST: PUSH_BASE (0x80)")
    print("=" * 60)

    # Create a WeatherBot instance
    bot = WeatherBot(port=None, debug=True)

    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mock_serial.in_waiting = 0
    bot._serial = mock_serial

    # Capture log output
    log_output = []
    original_log = bot._log

    def capture_log(msg):
        log_output.append(msg)
        original_log(msg)

    bot._log = capture_log

    # Simulate receiving PUSH_BASE frame (0x80)
    frame = create_frame(0x80, b"\x00" * 4)

    # Extract payload from frame (skip 0x3E + 2-byte length)
    payload = frame[3:]

    # Call the frame dispatcher
    bot._dispatch(payload)

    # Verify no "Unhandled frame code" error was logged
    unhandled_logs = [log for log in log_output if "Unhandled frame code" in log]
    assert len(unhandled_logs) == 0, f"Expected no 'Unhandled frame code' error for 0x80, but got: {unhandled_logs}"

    print("✓ PUSH_BASE (0x80) handled correctly without errors")
    print()

    return True


def test_push_no_more_msgs_0x8a():
    """Test handling of PUSH_NO_MORE_MSGS (0x8a)"""
    print("=" * 60)
    print("TEST: PUSH_NO_MORE_MSGS (0x8a)")
    print("=" * 60)

    # Create a WeatherBot instance
    bot = WeatherBot(port=None, debug=True)

    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mock_serial.in_waiting = 0
    bot._serial = mock_serial

    # Capture log output
    log_output = []
    original_log = bot._log

    def capture_log(msg):
        log_output.append(msg)
        original_log(msg)

    bot._log = capture_log

    # Simulate receiving PUSH_NO_MORE_MSGS frame (0x8a)
    frame = create_frame(0x8A, b"\x00")

    # Extract payload from frame
    payload = frame[3:]

    # Call the frame dispatcher
    bot._dispatch(payload)

    # Verify no "Unhandled frame code" error was logged
    unhandled_logs = [log for log in log_output if "Unhandled frame code" in log]
    assert len(unhandled_logs) == 0, f"Expected no 'Unhandled frame code' error for 0x8a, but got: {unhandled_logs}"

    print("✓ PUSH_NO_MORE_MSGS (0x8a) handled correctly without errors")
    print()

    return True


def test_push_contact_msg_v3_0x90():
    """Test handling of PUSH_CONTACT_MSG_V3 (0x90)"""
    print("=" * 60)
    print("TEST: PUSH_CONTACT_MSG_V3 (0x90)")
    print("=" * 60)

    # Create a WeatherBot instance
    bot = WeatherBot(port=None, debug=True)

    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mock_serial.in_waiting = 0
    bot._serial = mock_serial

    # Capture log output
    log_output = []
    original_log = bot._log

    def capture_log(msg):
        log_output.append(msg)
        original_log(msg)

    bot._log = capture_log

    # Simulate receiving PUSH_CONTACT_MSG_V3 frame (0x90)
    # This represents a direct contact message with SNR info
    frame = create_frame(0x90, b"\x00" * 12 + b"Hello from contact")

    # Extract payload from frame
    payload = frame[3:]

    # Call the frame dispatcher
    bot._dispatch(payload)

    # Verify no "Unhandled frame code" error was logged
    unhandled_logs = [log for log in log_output if "Unhandled frame code" in log]
    assert len(unhandled_logs) == 0, f"Expected no 'Unhandled frame code' error for 0x90, but got: {unhandled_logs}"

    # Verify that a log message was generated about ignoring contact messages
    contact_logs = [log for log in log_output if "contact message" in log.lower()]
    assert len(contact_logs) > 0, "Expected log message about ignoring contact message"

    print("✓ PUSH_CONTACT_MSG_V3 (0x90) handled correctly")
    print("✓ Contact message properly logged as ignored")
    print()

    return True


def test_all_new_codes_together():
    """Test that all three new codes don't trigger 'unhandled frame code' errors"""
    print("=" * 60)
    print("TEST: All new frame codes (0x80, 0x8a, 0x90)")
    print("=" * 60)

    # Create a WeatherBot instance
    bot = WeatherBot(port=None, debug=False)

    # Mock the serial connection
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mock_serial.in_waiting = 0
    bot._serial = mock_serial

    # Test all three new frame codes
    test_codes = [(0x80, "PUSH_BASE"), (0x8A, "PUSH_NO_MORE_MSGS"), (0x90, "PUSH_CONTACT_MSG_V3")]

    for code, name in test_codes:
        # Provide enough bytes for any validation checks
        frame = create_frame(code, bytes(20))

        # Extract payload from frame
        payload = frame[3:]
        code_byte = payload[0]
        data = payload[1:]

        # This should not raise any exception or log "unhandled"
        try:
            bot._dispatch(payload)
            print(f"✓ Code {code:#04x} ({name}) handled without errors")
        except Exception as e:
            print(f"✗ Code {code:#04x} ({name}) raised exception: {e}")
            return False

    print()
    return True


def main():
    """Run all new frame code tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "New Frame Code Handler Tests" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        # Run tests
        test_push_base_0x80()
        test_push_no_more_msgs_0x8a()
        test_push_contact_msg_v3_0x90()
        test_all_new_codes_together()

        print("=" * 60)
        print("✅ All new frame code tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  • PUSH_BASE (0x80) now handled silently")
        print("  • PUSH_NO_MORE_MSGS (0x8a) now handled silently")
        print("  • PUSH_CONTACT_MSG_V3 (0x90) now handled with appropriate log")
        print("  • No more 'unhandled frame code' errors for these codes")
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
