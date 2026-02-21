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
    """Test that send_message writes a binary CMD_SEND_CHANNEL_TXT_MSG frame to serial port"""
    print("=" * 60)
    print("TEST 2: Send Message Over LoRa")
    print("=" * 60)

    mock_serial = MagicMock()
    mock_serial.is_open = True

    mesh = MeshCore("lora_sender", serial_port="/dev/ttyUSB0", debug=False)
    mesh._serial = mock_serial  # inject mock
    mesh.running = True

    mesh.send_message("wx York", "text", channel="weather")

    # Verify serial.write was called with a binary MeshCore companion protocol frame
    assert mock_serial.write.called, "serial.write should have been called"
    # After our fix, write is called twice: once for the message, once for CMD_SYNC_NEXT_MSG
    assert mock_serial.write.call_count == 2, "write should be called twice (message + sync)"
    
    # Check the first call (the actual message)
    written_bytes = mock_serial.write.call_args_list[0][0][0]

    # Frame format (app→radio):  0x3C '<' + uint16_LE(length) + payload
    assert written_bytes[0:1] == b'\x3c', "Frame must start with '<' (0x3C) inbound marker"
    length = int.from_bytes(written_bytes[1:3], "little")
    assert len(written_bytes) == 3 + length, "Frame length field must match actual payload size"

    # Payload: CMD_SEND_CHANNEL_TXT_MSG(1) + txt_type(1) + channel_idx(1) + ts(4) + text
    payload = written_bytes[3:]
    assert payload[0] == 3, "Payload must begin with CMD_SEND_CHANNEL_TXT_MSG (3)"
    assert payload[1] == 0, "txt_type must be 0 (plain text)"
    # Channel 'weather' should be mapped to channel_idx 1 (not 0, which is for default/None)
    assert payload[2] == 1, "channel_idx must be 1 (weather channel)"
    text = payload[7:].decode("utf-8")
    assert text == "wx York", f"Message text mismatch: expected 'wx York', got '{text}'"
    print("✓ send_message writes binary CMD_SEND_CHANNEL_TXT_MSG frame to serial port")
    print(f"  Frame (hex): {written_bytes.hex()}")
    print(f"  Channel 'weather' mapped to channel_idx=1")
    
    # Check the second call (CMD_SYNC_NEXT_MSG)
    sync_bytes = mock_serial.write.call_args_list[1][0][0]
    assert sync_bytes[0:1] == b'\x3c', "Sync frame must start with '<' (0x3C)"
    assert sync_bytes[3:4] == b'\x0a', "Second call must be CMD_SYNC_NEXT_MSG (0x0A)"
    print("✓ send_message follows up with CMD_SYNC_NEXT_MSG to complete protocol exchange")

    print()


def test_send_without_channel():
    """Test that sending without a channel uses channel_idx 0"""
    print("=" * 60)
    print("TEST 2b: Send Message Without Channel")
    print("=" * 60)

    mock_serial = MagicMock()
    mock_serial.is_open = True

    mesh = MeshCore("lora_sender", serial_port="/dev/ttyUSB0", debug=False)
    mesh._serial = mock_serial
    mesh.running = True

    mesh.send_message("broadcast message", "text", channel=None)

    # Check the first call (the actual message)
    written_bytes = mock_serial.write.call_args_list[0][0][0]
    payload = written_bytes[3:]
    # Verify channel_idx is 0 for no-channel (broadcast)
    assert payload[2] == 0, "channel_idx must be 0 for broadcast (no channel)"
    print("✓ send_message without channel uses channel_idx=0 (broadcast)")


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


def test_binary_control_chars_sanitized():
    """Test that binary LoRa data with embedded control characters is handled safely"""
    print("=" * 60)
    print("TEST 5b: Binary / Control-Character Data Sanitized")
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
        # Raw LoRa AT-command response (no JSON, no control chars)
        b">08\n",
        # Binary frame with embedded \r that would corrupt terminal output
        b"jad3\x0d\x00binary\x1b\n",
        # Another non-JSON line starting with printable ASCII
        b"+L 1p\r\n_gx*\x02A2h\n",
        # Valid JSON message that must still be dispatched
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
    print("✓ Binary data with control characters handled safely; valid message dispatched")

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


def _build_binary_frame(payload: bytes) -> bytes:
    """Build a radio→app binary frame: 0x3E + uint16_LE(len) + payload."""
    return bytes([0x3E]) + len(payload).to_bytes(2, "little") + payload


def _build_channel_msg_frame(text: str, channel_idx: int = 0, path_len: int = 0,
                              txt_type: int = 0, timestamp: int = 0) -> bytes:
    """Build a RESP_CODE_CHANNEL_MSG_RECV (code 8) binary frame."""
    payload = bytes([8, channel_idx, path_len, txt_type]) + timestamp.to_bytes(4, "little") + text.encode("utf-8")
    return _build_binary_frame(payload)


def _build_push_msg_waiting_frame() -> bytes:
    """Build a PUSH_CODE_MSG_WAITING (code 0x83) binary frame."""
    return _build_binary_frame(bytes([0x83]))


def test_receive_binary_channel_message():
    """Test that a binary CHANNEL_MSG_RECV frame from a MeshCore device is processed"""
    print("=" * 60)
    print("TEST 11: Receive Binary Channel Message (MeshCore protocol)")
    print("=" * 60)

    received = []

    def handler(message):
        received.append(message)

    mesh = MeshCore("bot_node", debug=False)
    mesh.register_handler("text", handler)
    mesh.running = True

    mock_serial = MagicMock()
    mock_serial.is_open = True

    # Simulate a channel message: "Tim Bristol: wx London"
    # This is how MeshCore firmware formats channel messages (sender: message)
    frame = _build_channel_msg_frame("Tim Bristol: wx London")

    lines = [frame]

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

    assert len(received) == 1, f"Expected 1 message, got {len(received)}"
    assert received[0].sender == "Tim Bristol", f"Expected sender 'Tim Bristol', got '{received[0].sender}'"
    assert received[0].content == "wx London", f"Expected content 'wx London', got '{received[0].content}'"
    print(f"✓ Binary CHANNEL_MSG_RECV frame parsed correctly")
    print(f"  sender='{received[0].sender}', content='{received[0].content}'")
    print()


def test_receive_binary_channel_message_no_sender_prefix():
    """Test a binary channel message where the text has no sender prefix"""
    print("=" * 60)
    print("TEST 12: Binary Channel Message Without Sender Prefix")
    print("=" * 60)

    received = []

    def handler(message):
        received.append(message)

    mesh = MeshCore("bot_node", debug=False)
    mesh.register_handler("text", handler)
    mesh.running = True

    mock_serial = MagicMock()
    mock_serial.is_open = True

    # Message without sender prefix (older firmware or direct format)
    frame = _build_channel_msg_frame("wx York")

    lines = [frame]

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

    assert len(received) == 1, f"Expected 1 message, got {len(received)}"
    assert received[0].content == "wx York", f"Expected 'wx York', got '{received[0].content}'"
    print(f"✓ Binary channel message without sender prefix handled correctly")
    print(f"  content='{received[0].content}'")
    print()


def test_push_msg_waiting_triggers_sync():
    """Test that PUSH_CODE_MSG_WAITING causes a CMD_SYNC_NEXT_MESSAGE to be sent"""
    print("=" * 60)
    print("TEST 13: PUSH_MSG_WAITING Triggers CMD_SYNC_NEXT_MESSAGE")
    print("=" * 60)

    mesh = MeshCore("bot_node", debug=False)
    mesh.running = True

    mock_serial = MagicMock()
    mock_serial.is_open = True

    lines = [_build_push_msg_waiting_frame()]

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

    # CMD_SYNC_NEXT_MESSAGE frame: 0x3C + len(1 LE) + 0x0A
    assert mock_serial.write.called, "write() should be called for CMD_SYNC_NEXT_MESSAGE"
    written = mock_serial.write.call_args[0][0]
    assert written[0:1] == b'\x3c', "Frame start byte must be '<' (0x3C)"
    assert written[3:4] == b'\x0a', "Command byte must be CMD_SYNC_NEXT_MESSAGE (0x0A)"
    print("✓ PUSH_MSG_WAITING triggers CMD_SYNC_NEXT_MESSAGE command")
    print(f"  Sent frame (hex): {written.hex()}")
    print()


def test_connect_serial_sends_app_start():
    """Test that _connect_serial sends CMD_APP_START to initialise the companion radio"""
    print("=" * 60)
    print("TEST 14: _connect_serial Sends CMD_APP_START")
    print("=" * 60)

    with patch("meshcore.SERIAL_AVAILABLE", True), \
         patch("meshcore.serial") as mock_serial_module:

        mock_port = MagicMock()
        mock_port.is_open = True
        mock_serial_module.Serial.return_value = mock_port
        mock_serial_module.SerialException = Exception

        mesh = MeshCore("lora_bot", serial_port="/dev/ttyUSB0", baud_rate=9600, debug=False)
        mesh._connect_serial()

        assert mock_port.write.called, "write() must be called during _connect_serial"
        # First write should be CMD_APP_START frame
        first_write = mock_port.write.call_args_list[0][0][0]
        assert first_write[0:1] == b'\x3c', "CMD_APP_START frame must start with '<'"
        assert first_write[3:4] == b'\x01', "First command byte must be CMD_APP_START (0x01)"
        print("✓ _connect_serial sends CMD_APP_START on connection")
        print(f"  CMD_APP_START frame (hex): {first_write.hex()}")

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
        test_send_without_channel()
        test_simulation_mode_no_write()
        test_receive_message_from_lora()
        test_invalid_lora_data_ignored()
        test_binary_control_chars_sanitized()
        test_channel_filter_applied_to_lora_messages()
        test_start_stop_with_mock_serial()
        test_rts_dtr_deasserted_after_connect()
        test_invalid_baud_rate_rejected()
        test_valid_baud_rates_accepted()
        test_receive_binary_channel_message()
        test_receive_binary_channel_message_no_sender_prefix()
        test_push_msg_waiting_triggers_sync()
        test_connect_serial_sends_app_start()

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
