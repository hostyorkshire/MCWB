#!/usr/bin/env python3
"""
Test to verify that garbled LoRa data is NOT logged with "LoRa RX:"
This addresses the issue where corrupted data was showing up in logs.
"""

import sys
import io
from contextlib import redirect_stdout
from unittest.mock import MagicMock
from meshcore import MeshCore, MeshCoreMessage


def test_garbled_data_not_logged():
    """Test that garbled data doesn't show up in LoRa RX logs"""
    print("=" * 60)
    print("TEST: Garbled Data Logging Fix")
    print("=" * 60)

    mesh = MeshCore("WX_BOT", debug=True)
    mesh.running = True

    mock_serial = MagicMock()
    mock_serial.is_open = True

    # Simulate the exact problematic data from the issue
    garbled_data = '7v7^Aȟn%\'qx/~(:+v&lt;_̼f}#DFjH.9R"c6Kc bfO39.s,[jn[rH_Zb&gt;SF)=7.d&gt;D8'
    # After HTML unescaping, this becomes:
    import html
    garbled_data_unescaped = html.unescape(garbled_data)
    
    # Create a valid message for comparison
    valid_msg = MeshCoreMessage("sender", "valid content", "text")
    valid_json = valid_msg.to_json()

    test_lines = [
        (garbled_data.encode("utf-8") + b'\n'),  # Garbled data
        (valid_json.encode("utf-8") + b'\n'),    # Valid JSON
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

    # Capture stdout to check what gets logged
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        mesh._listen_loop()

    output = captured_output.getvalue()
    
    # Check results
    print(f"\nCaptured output:\n{output}")
    
    # The garbled data (either escaped or unescaped) should NOT appear in "LoRa RX:" logs
    garbled_in_lora_rx = False
    for line in output.split('\n'):
        if 'LoRa RX:' in line and (garbled_data in line or garbled_data_unescaped in line):
            garbled_in_lora_rx = True
            break
    
    # The valid JSON should appear in "LoRa RX:" logs
    valid_in_lora_rx = False
    for line in output.split('\n'):
        if 'LoRa RX:' in line and 'valid content' in line:
            valid_in_lora_rx = True
            break
    
    # Should see "Ignoring non-JSON LoRa data" for garbled data
    ignoring_message_present = 'Ignoring non-JSON LoRa data' in output
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"✓ Garbled data in 'LoRa RX:' log: {garbled_in_lora_rx} (should be False)")
    print(f"✓ Valid JSON in 'LoRa RX:' log: {valid_in_lora_rx} (should be True)")
    print(f"✓ 'Ignoring non-JSON' message present: {ignoring_message_present} (should be True)")
    
    assert not garbled_in_lora_rx, "Garbled data should NOT be logged with 'LoRa RX:'"
    assert valid_in_lora_rx, "Valid JSON should be logged with 'LoRa RX:'"
    assert ignoring_message_present, "Should log 'Ignoring non-JSON LoRa data'"
    
    print("\n✅ Fix verified: Garbled data is no longer logged with 'LoRa RX:'")
    print()


def main():
    """Run the test"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Garbled Data Logging Fix Test" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_garbled_data_not_logged()
        
        print("=" * 60)
        print("✅ Test passed!")
        print("=" * 60)
        print()
        print("The fix successfully prevents garbled LoRa data from")
        print("appearing in 'LoRa RX:' log entries, while still logging")
        print("that non-JSON data is being ignored.")
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
