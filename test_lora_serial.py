#!/usr/bin/env python3
"""
Test script for LoRa serial communication support in MeshCore.
Uses unittest.mock to simulate serial hardware so tests run without
physical LoRa hardware attached.
"""

import sys
import json
from unittest.mock import MagicMock, patch
from meshcore import MeshCore, MeshCoreMessage


def test_meshcore_serial_params():
    """Test that MeshCore accepts and stores serial port parameters"""
    print("=" * 60)
    print("TEST 1: MeshCore Serial Port Parameters")
    print("=" * 60)

    mesh = MeshCore("node_lora", serial_port="/dev/ttyUSB0", baud_rate=115200)
    assert mesh.serial_port == "/dev/ttyUSB0"
    assert mesh.baud_rate == 115200
    assert mesh._serial is None
    print("✓ serial_port and baud_rate stored correctly")

    mesh2 = MeshCore("node_sim")
    assert mesh2.serial_port is None
    assert mesh2.baud_rate == 9600
    print("✓ defaults: serial_port=None, baud_rate=9600")

    print()


def test_send_over_lora():
    """Test that send_message writes JSON to serial port when connected"""
    print("=" * 60)
    print("TEST 2: Send Message Over LoRa")
    print("=" * 60)

    mock_serial = MagicMock()
    mock_serial.is_open = True

    mesh = MeshCore("lora_sender", serial_port="/dev/ttyUSB0", debug=False)
    mesh._serial = mock_serial  # inject mock
    mesh.running = True

    mesh.send_message("wx York", "text", channel="weather")

    # Verify serial.write was called with JSON-encoded message + newline
    assert mock_serial.write.called, "serial.write should have been called"
    written_bytes = mock_serial.write.call_args[0][0]
    written_str = written_bytes.decode("utf-8")
    assert written_str.endswith("\n"), "Transmitted data should end with newline"

    parsed = json.loads(written_str.strip())
    assert parsed["content"] == "wx York"
    assert parsed["channel"] == "weather"
    assert parsed["sender"] == "lora_sender"
    print("✓ send_message writes JSON message to serial port")
    print(f"  Transmitted: {written_str.strip()}")

    print()


def test_simulation_mode_no_write():
    """Test that send_message does NOT write to serial when no port is configured"""
    print("=" * 60)
    print("TEST 3: Simulation Mode (No Serial Port)")
    print("=" * 60)

    mesh = MeshCore("sim_node", debug=False)
    mesh.start()

    msg = mesh.send_message("wx London", "text", channel="weather")
    assert mesh._serial is None, "No serial object in simulation mode"
    assert msg.content == "wx London"
    print("✓ In simulation mode, no serial write attempted")

    mesh.stop()
    print()


def test_receive_message_from_lora():
    """Test that _listen_loop reads lines from serial and dispatches messages"""
    print("=" * 60)
    print("TEST 4: Receive Messages from LoRa")
    print("=" * 60)

    received = []

    def handler(message):
        received.append(message)

    # Build a JSON line that the listener should parse
    test_msg = MeshCoreMessage("remote_node", "wx London", "text", channel="weather")
    json_line = (test_msg.to_json() + "\n").encode("utf-8")

    mesh = MeshCore("bot_node", debug=False)
    mesh.register_handler("text", handler)
    mesh.running = True

    mock_serial = MagicMock()
    mock_serial.is_open = True

    # After the JSON line, stop the loop by clearing running flag
    def readline_side_effect():
        readline_side_effect.count += 1
        if readline_side_effect.count == 1:
            return json_line
        mesh.running = False  # signal loop to exit
        return b""

    readline_side_effect.count = 0
    mock_serial.readline.side_effect = lambda: readline_side_effect()
    mesh._serial = mock_serial

    mesh._listen_loop()

    assert len(received) == 1, f"Expected 1 message, got {len(received)}"
    assert received[0].content == "wx London"
    assert received[0].channel == "weather"
    assert received[0].sender == "remote_node"
    print("✓ _listen_loop parses incoming JSON and dispatches to handler")
    print(f"  Received: content='{received[0].content}', channel='{received[0].channel}'")

    print()


def test_invalid_lora_data_ignored():
    """Test that non-JSON data from LoRa does not crash the listener"""
    print("=" * 60)
    print("TEST 5: Invalid LoRa Data Ignored Gracefully")
    print("=" * 60)

    received = []

    def handler(message):
        received.append(message)

    valid_msg = MeshCoreMessage("sender", "wx York", "text")

    mesh = MeshCore("bot_node", debug=False)
    mesh.register_handler("text", handler)
    mesh.running = True

    mock_serial = MagicMock()
    mock_serial.is_open = True

    lines = [
        b"GARBAGE DATA\n",
        (valid_msg.to_json() + "\n").encode("utf-8"),
    ]

    def readline_side_effect():
        readline_side_effect.count += 1
        if readline_side_effect.count <= len(lines):
            return lines[readline_side_effect.count - 1]
        mesh.running = False
        return b""

    readline_side_effect.count = 0
    mock_serial.readline.side_effect = lambda: readline_side_effect()
    mesh._serial = mock_serial

    mesh._listen_loop()

    assert len(received) == 1, f"Expected 1 valid message, got {len(received)}"
    assert received[0].content == "wx York"
    print("✓ Garbage LoRa data ignored; valid message still dispatched")

    print()


def test_channel_filter_applied_to_lora_messages():
    """Test channel filtering works for messages received from LoRa"""
    print("=" * 60)
    print("TEST 6: Channel Filter Applied to LoRa Messages")
    print("=" * 60)

    received = []

    def handler(message):
        received.append(message)

    weather_msg = MeshCoreMessage("node_a", "wx London", "text", channel="weather")
    news_msg = MeshCoreMessage("node_b", "Breaking news", "text", channel="news")

    mesh = MeshCore("bot_node", debug=False)
    mesh.register_handler("text", handler)
    mesh.set_channel_filter("weather")
    mesh.running = True

    mock_serial = MagicMock()
    mock_serial.is_open = True

    lines = [
        (weather_msg.to_json() + "\n").encode("utf-8"),
        (news_msg.to_json() + "\n").encode("utf-8"),
    ]

    def readline_side_effect():
        readline_side_effect.count += 1
        if readline_side_effect.count <= len(lines):
            return lines[readline_side_effect.count - 1]
        mesh.running = False
        return b""

    readline_side_effect.count = 0
    mock_serial.readline.side_effect = lambda: readline_side_effect()
    mesh._serial = mock_serial

    mesh._listen_loop()

    assert len(received) == 1, f"Expected 1 message (weather only), got {len(received)}"
    assert received[0].channel == "weather"
    print("✓ Channel filter correctly accepts 'weather' and rejects 'news' messages")

    print()


def test_start_stop_with_mock_serial():
    """Test start/stop lifecycle with a mocked serial port"""
    print("=" * 60)
    print("TEST 7: Start/Stop Lifecycle with LoRa Serial")
    print("=" * 60)

    with patch("meshcore.SERIAL_AVAILABLE", True), \
         patch("meshcore.serial") as mock_serial_module:

        mock_port = MagicMock()
        mock_port.is_open = True
        # readline returns empty to let listener thread idle
        mock_port.readline.return_value = b""
        mock_serial_module.Serial.return_value = mock_port
        mock_serial_module.SerialException = Exception

        mesh = MeshCore("lora_bot", serial_port="/dev/ttyUSB0", baud_rate=9600, debug=False)
        mesh.start()

        mock_serial_module.Serial.assert_called_once_with(
            "/dev/ttyUSB0", 9600, timeout=1, rtscts=False, dsrdtr=False,
        )
        assert mesh._listener_thread is not None
        assert mesh._listener_thread.is_alive()
        print("✓ start() opens serial port and spawns listener thread")

        mesh.stop()
        assert not mesh.running
        print("✓ stop() sets running=False and closes serial port")

    print()


def test_rts_dtr_deasserted_after_connect():
    """Test that RTS and DTR are set to False after opening the serial port"""
    print("=" * 60)
    print("TEST 8: RTS and DTR Deasserted After Connect")
    print("=" * 60)

    with patch("meshcore.SERIAL_AVAILABLE", True), \
         patch("meshcore.serial") as mock_serial_module:

        mock_port = MagicMock()
        mock_port.is_open = True
        mock_port.readline.return_value = b""
        mock_serial_module.Serial.return_value = mock_port
        mock_serial_module.SerialException = Exception

        mesh = MeshCore("lora_bot", serial_port="/dev/ttyUSB0", baud_rate=9600, debug=False)
        mesh._connect_serial()

        # Verify RTS and DTR were explicitly set to False
        assert mock_port.rts is False, "RTS should be deasserted (False)"
        assert mock_port.dtr is False, "DTR should be deasserted (False)"
        print("✓ RTS set to False after port open (prevents unintended device resets)")
        print("✓ DTR set to False after port open (prevents unintended device resets)")

    print()


def test_invalid_baud_rate_rejected():
    """Test that an invalid baud rate prevents the serial port from being opened"""
    print("=" * 60)
    print("TEST 9: Invalid Baud Rate Rejected (Preflight)")
    print("=" * 60)

    with patch("meshcore.SERIAL_AVAILABLE", True), \
         patch("meshcore.serial") as mock_serial_module:

        mock_serial_module.SerialException = Exception

        mesh = MeshCore("lora_bot", serial_port="/dev/ttyUSB0", baud_rate=12345, debug=False)
        mesh._connect_serial()

        mock_serial_module.Serial.assert_not_called()
        assert mesh._serial is None, "_serial should remain None for invalid baud rate"
        print("✓ Serial port not opened for non-standard baud rate 12345")

    print()


def test_valid_baud_rates_accepted():
    """Test that all standard baud rates pass the preflight check"""
    print("=" * 60)
    print("TEST 10: Valid Baud Rates Accepted (Preflight)")
    print("=" * 60)

    from meshcore import VALID_BAUD_RATES

    for baud in sorted(VALID_BAUD_RATES):
        with patch("meshcore.SERIAL_AVAILABLE", True), \
             patch("meshcore.serial") as mock_serial_module:

            mock_port = MagicMock()
            mock_port.is_open = True
            mock_serial_module.Serial.return_value = mock_port
            mock_serial_module.SerialException = Exception

            mesh = MeshCore("node", serial_port="/dev/ttyUSB0", baud_rate=baud, debug=False)
            mesh._connect_serial()

            mock_serial_module.Serial.assert_called_once()
            assert mesh._serial is not None, f"Serial should open for valid baud rate {baud}"

    print(f"✓ All {len(VALID_BAUD_RATES)} standard baud rates accepted")

    print()


def main():
    """Run all LoRa serial tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "MeshCore LoRa Serial Tests" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_meshcore_serial_params()
        test_send_over_lora()
        test_simulation_mode_no_write()
        test_receive_message_from_lora()
        test_invalid_lora_data_ignored()
        test_channel_filter_applied_to_lora_messages()
        test_start_stop_with_mock_serial()
        test_rts_dtr_deasserted_after_connect()
        test_invalid_baud_rate_rejected()
        test_valid_baud_rates_accepted()

        print("=" * 60)
        print("✅ All LoRa serial tests passed!")
        print("=" * 60)
        print()
        print("To use with real LoRa hardware:")
        print("  python3 weather_bot.py --port /dev/ttyUSB0 --baud 9600 --channel weather")
        print("  python3 meshcore_send.py 'wx London' --port /dev/ttyUSB0 --channel weather")
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
