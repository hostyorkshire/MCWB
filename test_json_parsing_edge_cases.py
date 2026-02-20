#!/usr/bin/env python3
"""
Test script to verify that edge cases in LoRa message parsing are handled correctly.
This specifically tests the fix for "Expecting value: line 1 column 1 (char 0)" errors.
"""

import sys
from unittest.mock import MagicMock
from meshcore import MeshCore, MeshCoreMessage


def test_malformed_json_lines():
    """Test that various malformed inputs don't crash the listener"""
    print("=" * 60)
    print("TEST: Malformed JSON and Edge Cases")
    print("=" * 60)

    received = []

    def handler(message):
        received.append(message)

    mesh = MeshCore("test_node", debug=False)
    mesh.register_handler("text", handler)
    mesh.running = True

    mock_serial = MagicMock()
    mock_serial.is_open = True

    # Valid message for comparison
    valid_msg = MeshCoreMessage("sender", "test content", "text")

    # Test various edge cases that should be ignored
    test_lines = [
        b'>\n',  # Single character starting with >
        b'>j1M[MfO4(6?\n',  # The problematic line from the logs
        b'{\n',  # Just opening brace
        b'{invalid json}\n',  # Invalid JSON structure (starts and ends with braces)
        b'{ \x00\x01 \n',  # Opening brace with control chars, no closing brace
        b'\x00\x01\x02\n',  # Only control characters
        b'   \n',  # Only whitespace
        b'{test\n',  # Starts with { but doesn't end with }
        b'test}\n',  # Ends with } but doesn't start with {
        (valid_msg.to_json() + "\n").encode("utf-8"),  # Valid message at the end
    ]

    def readline_side_effect():
        readline_side_effect.count += 1
        if readline_side_effect.count <= len(test_lines):
            return test_lines[readline_side_effect.count - 1]
        mesh.running = False
        return b""

    readline_side_effect.count = 0
    mock_serial.readline.side_effect = lambda: readline_side_effect()
    mesh._serial = mock_serial

    # Run the listen loop
    mesh._listen_loop()

    # Should only receive the valid message
    print(f"✓ Processed {len(test_lines)} test inputs")
    print(f"✓ Received {len(received)} valid message(s)")
    assert len(received) == 1, f"Expected 1 valid message, got {len(received)}"
    assert received[0].content == "test content"
    print(f"✓ Valid message correctly parsed: '{received[0].content}'")
    print(f"✓ All malformed inputs were safely ignored")
    print()


def test_json_with_control_characters_before_brace():
    """Test that lines with control characters before { are handled"""
    print("=" * 60)
    print("TEST: Control Characters Before Opening Brace")
    print("=" * 60)

    received = []

    def handler(message):
        received.append(message)

    mesh = MeshCore("test_node", debug=False)
    mesh.register_handler("text", handler)
    mesh.running = True

    mock_serial = MagicMock()
    mock_serial.is_open = True

    # Valid message with control characters before it
    valid_msg = MeshCoreMessage("sender", "test", "text")
    valid_json = valid_msg.to_json()

    # After filtering control characters, this should become valid JSON starting with {
    test_lines = [
        (b'\x00\x01' + valid_json.encode("utf-8") + b'\n'),
        (valid_json.encode("utf-8") + b'\n'),
    ]

    def readline_side_effect():
        readline_side_effect.count += 1
        if readline_side_effect.count <= len(test_lines):
            return test_lines[readline_side_effect.count - 1]
        mesh.running = False
        return b""

    readline_side_effect.count = 0
    mock_serial.readline.side_effect = lambda: readline_side_effect()
    mesh._serial = mock_serial

    mesh._listen_loop()

    # Both messages should be received (control chars are filtered out)
    assert len(received) == 2, f"Expected 2 valid messages, got {len(received)}"
    print(f"✓ Both messages received after control character filtering")
    print()


def test_empty_json_object():
    """Test that empty JSON objects {} are handled"""
    print("=" * 60)
    print("TEST: Empty JSON Object")
    print("=" * 60)

    mesh = MeshCore("test_node", debug=False)
    mesh.running = True

    mock_serial = MagicMock()
    mock_serial.is_open = True

    # Empty JSON object should pass validation but fail parsing
    test_lines = [
        b'{}\n',
        b'{  }\n',
    ]

    def readline_side_effect():
        readline_side_effect.count += 1
        if readline_side_effect.count <= len(test_lines):
            return test_lines[readline_side_effect.count - 1]
        mesh.running = False
        return b""

    readline_side_effect.count = 0
    mock_serial.readline.side_effect = lambda: readline_side_effect()
    mesh._serial = mock_serial

    # This should not crash, just log errors
    mesh._listen_loop()

    print(f"✓ Empty JSON objects handled without crashing")
    print()


def main():
    """Run all edge case tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 8 + "JSON Parsing Edge Case Tests" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_malformed_json_lines()
        test_json_with_control_characters_before_brace()
        test_empty_json_object()

        print("=" * 60)
        print("✅ All edge case tests passed!")
        print("=" * 60)
        print()
        print("The fix successfully prevents:")
        print("  • 'Expecting value: line 1 column 1 (char 0)' errors")
        print("  • Parsing attempts on non-JSON data")
        print("  • Crashes from malformed LoRa radio frames")
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
