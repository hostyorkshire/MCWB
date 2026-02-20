#!/usr/bin/env python3
"""
MeshCore - Core library for mesh radio network communication

Target hardware : Heltec WiFi LoRa 32 V2  /  ESP32-D0WDQ6
USB bridge      : Silicon Labs CP2102  VID=0x10C4  PID=0xEA60
Firmware        : MeshCore v1.13.0  (companion radio protocol)

CRITICAL - RTS/DTR fix
    On the Heltec V2 the CP2102 RTS pin is wired to ESP32 EN (reset)
    and DTR is wired to IO0 (boot select). pyserial may inherit an
    asserted state from a previous process (Arduino IDE, esptool, etc.)
    which holds the ESP32 permanently in reset, producing no response
    to any serial command. We deassert both lines immediately after open.

Frame format (ArduinoSerialInterface.cpp)
    Host to Node : '<'  len_lo  len_hi  payload
    Node to Host : '>'  len_lo  len_hi  payload
"""

import json
import struct
import time
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime

try:
    import serial
    import serial.tools.list_ports
    from serial import SerialException
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    class SerialException(Exception):  # type: ignore[no-redef]
        pass


# Hardware constants
TARGET_VID   = 0x10C4   # Silicon Labs CP2102
TARGET_PID   = 0xEA60
DEFAULT_BAUD = 115200   # MeshCore firmware default (NOT 9600)

# MeshCore binary protocol constants
MAX_FRAME_SIZE   = 172
FRAME_TO_NODE    = ord('<')   # 0x3C
FRAME_FROM_NODE  = ord('>')   # 0x3E
FIRMWARE_VER     = 9

# Commands (host to radio)
CMD_APP_START            = 1
CMD_SEND_TXT_MSG         = 2
CMD_SEND_CHANNEL_TXT_MSG = 3
CMD_GET_DEVICE_TIME      = 5
CMD_SET_DEVICE_TIME      = 6
CMD_SEND_SELF_ADVERT     = 7
CMD_SYNC_NEXT_MESSAGE    = 10
CMD_GET_BATT_AND_STORAGE = 20
CMD_DEVICE_QUERY         = 22
CMD_GET_CHANNEL          = 31
CMD_GET_STATS            = 56

# Response codes (radio to host)
RESP_OK                  = 0
RESP_ERR                 = 1
RESP_SELF_INFO           = 5
RESP_SENT                = 6
RESP_CHANNEL_MSG_RECV    = 8
RESP_CURR_TIME           = 9
RESP_NO_MORE_MESSAGES    = 10
RESP_BATT_AND_STORAGE    = 12
RESP_DEVICE_INFO         = 13
RESP_CHANNEL_MSG_RECV_V3 = 17
RESP_CHANNEL_INFO        = 18

# Push codes (unsolicited, radio to host)
PUSH_MSG_WAITING         = 0x83
PUSH_LOG_RX_DATA         = 0x88
PUSH_NEW_ADVERT          = 0x8A

TXT_TYPE_PLAIN = 1


class PreFlightError(RuntimeError):
    """Raised when a pre-flight check fails and the bot should not start."""
    pass


def run_preflight(port, baud=DEFAULT_BAUD, verbose=True):
    """
    Run hardware pre-flight checks before starting the weather bot.

    Checks (in order):
      1. pyserial installed
      2. Port exists / CP2102 VID+PID matches
      3. Port can be opened
      4. RTS/DTR deasserted (ESP32 not held in reset)
      5. Node responds to CMD_DEVICE_QUERY within 4 s
      6. Node responds to CMD_APP_START (SELF_INFO)

    Returns a dict of discovered node properties on success.
    Raises PreFlightError with a human-readable message on failure.
    """

    def log(msg):
        if verbose:
            ts = datetime.now().strftime("%H:%M:%S")
            print("  [{}] preflight: {{}}".format(ts, msg))

    result = {}

    # 1. pyserial
    if not SERIAL_AVAILABLE:
        raise PreFlightError("pyserial not installed. Run: pip install pyserial")
    log("OK pyserial available")

    # 2. Port / VID+PID
    port_info = None
    for p in serial.tools.list_ports.comports():
        if p.device == port:
            port_info = p
            break
    if port_info is None:
        available = [p.device for p in serial.tools.list_ports.comports()]
        raise PreFlightError(
            "Port {} not found. Available: {{}}".format(port, available or ["(none)"])
        )
    vid = port_info.vid
    pid = port_info.pid
    if vid != TARGET_VID or pid != TARGET_PID:
        log("WARNING VID=0x{{:04X}} PID=0x{{:04X}} - expected CP2102 (VID=0x{{:04X}} PID=0x{{:04X}})".format(
            vid, pid, TARGET_VID, TARGET_PID))
    else:
        log("OK CP2102 detected VID=0x{{:04X}} PID=0x{{:04X}}".format(vid, pid))
    result["port_description"] = port_info.description

    # 3. Open port
    try:
        ser = serial.Serial(
            port, baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.05,
            write_timeout=2,
            rtscts=False,
            dsrdtr=False,
        )
    except SerialException as e:
        raise PreFlightError("Cannot open {}: {{}}".format(port, e))
    log("OK Port opened {{}} @ {{}} baud".format(port, baud))

    # 4. Deassert RTS/DTR
    rts_was = ser.rts
    dtr_was = ser.dtr
    ser.rts = False
    ser.dtr = False
    if rts_was or dtr_was:
        log("WARNING RTS={{}} DTR={{}} were asserted - deasserted now (ESP32 was held in reset!)".format(
            rts_was, dtr_was))
        time.sleep(2.0)
    else:
        log("OK RTS/DTR already deasserted")
    ser.reset_input_buffer()

    # 5. CMD_DEVICE_QUERY
    frame_dq = bytes([FRAME_TO_NODE, 2, 0, CMD_DEVICE_QUERY, FIRMWARE_VER])
    ser.write(frame_dq)
    ser.flush()

    raw = bytearray()
    deadline = time.time() + 4.0
    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            raw += chunk
            if FRAME_FROM_NODE in raw:
                idx = raw.index(FRAME_FROM_NODE)
                if len(raw) >= idx + 3:
                    length = raw[idx + 1] | (raw[idx + 2] << 8)
                    if len(raw) >= idx + 3 + length:
                        payload = raw[idx + 3:idx + 3 + length]
                        if payload and payload[0] == RESP_DEVICE_INFO:
                            break

    if not raw or FRAME_FROM_NODE not in raw:
        ser.close()
        raise PreFlightError(
            "No response from node on {} @ {{}} baud.\n"
            "  Wrong baud rate? (try 115200)\n"
            "  Wrong firmware? (needs MeshCore companion radio build)".format(port, baud)
        )

    # Parse DEVICE_INFO response
    idx = raw.index(FRAME_FROM_NODE)
    if len(raw) >= idx + 3:
        length = raw[idx + 1] | (raw[idx + 2] << 8)
        payload = raw[idx + 3:idx + 3 + length] if len(raw) >= idx + 3 + length else raw[idx + 3:]
        if payload and payload[0] == RESP_DEVICE_INFO:
            fw_ver_code  = payload[1] if len(payload) > 1 else 0
            max_contacts = payload[2] * 2 if len(payload) > 2 else 0
            if len(payload) >= 80:
                result["build_date"]   = payload[7:19].decode("utf-8", errors="replace").rstrip("\x00")
                result["manufacturer"] = payload[19:59].decode("utf-8", errors="replace").rstrip("\x00")
                result["fw_version"]   = payload[59:79].decode("utf-8", errors="replace").rstrip("\x00")
            result["fw_ver_code"]  = fw_ver_code
            result["max_contacts"] = max_contacts
            log("OK DEVICE_INFO fw_ver={{}} max_contacts={{}} fw={{}}".format(
                fw_ver_code, max_contacts, result.get("fw_version", "?")))
            if fw_ver_code != FIRMWARE_VER:
                log("WARNING fw_ver_code={{}}, expected {{}} (MeshCore v1.13.0) - continuing".format(
                    fw_ver_code, FIRMWARE_VER))

    # 6. CMD_APP_START
    app_name = b"MCWB"
    payload_as = bytes([CMD_APP_START]) + bytes(7) + app_name
    n = len(payload_as)
    frame_as = bytes([FRAME_TO_NODE, n & 0xFF, (n >> 8) & 0xFF]) + payload_as
    ser.write(frame_as)
    ser.flush()

    raw2 = bytearray()
    deadline2 = time.time() + 3.0
    while time.time() < deadline2:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            raw2 += chunk
            if FRAME_FROM_NODE in raw2:
                idx2 = raw2.index(FRAME_FROM_NODE)
                if len(raw2) >= idx2 + 3:
                    length2 = raw2[idx2 + 1] | (raw2[idx2 + 2] << 8)
                    if len(raw2) >= idx2 + 3 + length2:
                        p2 = raw2[idx2 + 3:idx2 + 3 + length2]
                        if p2 and p2[0] == RESP_SELF_INFO:
                            if len(p2) >= 60:
                                result["node_name"] = p2[56:].decode("utf-8", errors="replace").rstrip("\x00")
                            log("OK APP_START node_name={{}}".format(result.get("node_name", "?")))
                            break

    if not raw2 or FRAME_FROM_NODE not in raw2:
        log("WARNING No SELF_INFO from APP_START - node connected but handshake failed")

    ser.close()
    log("OK Pre-flight complete - hardware OK")
    return result


class MeshCoreMessage:
    """Represents a message in the MeshCore network"""

    def __init__(self, sender, content, message_type="text",
                 timestamp=None, channel=None):
        self.sender       = sender
        self.content      = content
        self.message_type = message_type
        self.timestamp    = timestamp or time.time()
        self.channel      = channel

    def to_dict(self):
        """Convert message to dictionary"""
        data = {
            "sender":    self.sender,
            "content":   self.content,
            "type":      self.message_type,
            "timestamp": self.timestamp,
        }
        if self.channel:
            data["channel"] = self.channel
        return data

    def to_json(self):
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        """Create message from dictionary"""
        return cls(
            sender=data.get("sender", "unknown"),
            content=data.get("content", ""),
            message_type=data.get("type", "text"),
            timestamp=data.get("timestamp"),
            channel=data.get("channel"),
        )

    @classmethod
    def from_json(cls, json_str):
        """Create message from JSON string"""
        return cls.from_dict(json.loads(json_str))


class MeshCore:
    """
    MeshCore companion radio connection.

    Wraps the ArduinoSerialInterface binary frame protocol.
    Default baud rate is 115200 (MeshCore firmware default).
    RTS/DTR are always deasserted on open to avoid holding the ESP32 in reset.
    """

    def __init__(self, node_id, debug=False, serial_port=None, baud_rate=DEFAULT_BAUD):
        """
        Initialize MeshCore

        Args:
            node_id: Unique identifier for this node
            debug: Enable debug output
            serial_port: Serial port for LoRa module (e.g., /dev/ttyUSB1). When None,
                         the node operates in simulation mode (no actual radio transmission).
            baud_rate: Baud rate for serial connection (default: 115200 for MeshCore firmware)
        """
        self.node_id      = node_id
        self.debug        = debug
        self.serial_port  = serial_port
        self.baud_rate    = baud_rate

        self.running      = False
        self.channel_filter = None
        self.message_handlers = {}

        self._serial = None
        self._listener_thread = None
        self._recv_buf = bytearray()
        self._lock = threading.Lock()

        self.node_name    = None
        self.pub_key_hex  = None
        self.fw_version   = None
        self.manufacturer = None
        self.freq_mhz     = None

    def log(self, message):
        """Log debug messages"""
        if self.debug:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("[{{}}] MeshCore [{{}}]: {{}}".format(timestamp, self.node_id, message))

    def set_channel_filter(self, channel):
        """Set channel filter for receiving messages"""       
        Args:
            channel: Channel name to filter on, or None to receive all channels
        """
        self.channel_filter = channel
        self.log("Channel filter set to: {{}}".format(channel))

    def register_handler(self, message_type, handler):
        """Register a handler function for a given message type"""
        self.message_handlers[message_type] = handler
        self.log("Registered handler for message type: {{}}".format(message_type))

    def _encode_frame(self, payload):
        n = len(payload)
        return bytes([FRAME_TO_NODE, n & 0xFF, (n >> 8) & 0xFF]) + payload

    def _pump_frames(self):
        while len(self._recv_buf) >= 3:
            if self._recv_buf[0] != FRAME_FROM_NODE:
                idx = bytes(self._recv_buf).find(FRAME_FROM_NODE)
                if idx < 0:
                    self._recv_buf.clear()
                    return
                self._recv_buf = self._recv_buf[idx:]
                continue
            length = self._recv_buf[1] | (self._recv_buf[2] << 8)
            if length == 0 or length > MAX_FRAME_SIZE:
                self._recv_buf = self._recv_buf[1:]
                continue
            if len(self._recv_buf) < 3 + length:
                break
            payload = bytes(self._recv_buf[3:3 + length])
            self._recv_buf = self._recv_buf[3 + length:]
            self._dispatch(payload)

    def _dispatch(self, payload):
        if not payload:
            return
        code = payload[0]

        if code == RESP_SELF_INFO and len(payload) >= 56:
            self.node_name = payload[56:].decode("utf-8", errors="replace").rstrip("\x00")

        elif code == RESP_DEVICE_INFO and len(payload) >= 80:
            self.fw_version   = payload[59:79].decode("utf-8", errors="replace").rstrip("\x00")
            self.manufacturer = payload[19:59].decode("utf-8", errors="replace").rstrip("\x00")

        elif code in (RESP_CHANNEL_MSG_RECV, RESP_CHANNEL_MSG_RECV_V3):
            v3 = (code == RESP_CHANNEL_MSG_RECV_V3)
            i = 1
            if v3:
                i += 3
            if len(payload) > i:
                i += 1
            if len(payload) > i:
                i += 1
            if len(payload) > i:
                i += 1
            if len(payload) >= i + 4:
                i += 4
            text = payload[i:].decode("utf-8", errors="replace") if len(payload) > i else ""
            msg = MeshCoreMessage(
                sender="mesh",
                content=text,
                message_type="text",
                timestamp=time.time(),
            )
            handler = self.message_handlers.get("text")
            if handler:
                try:
                    handler(msg)
                except Exception as e:
                    self.log("Handler error: {{}}".format(e))

        elif code == PUSH_MSG_WAITING:
            self._send_raw(self._encode_frame(bytes([CMD_SYNC_NEXT_MESSAGE])))

    def _send_raw(self, frame):
        if not self._serial or not self._serial.is_open:
            return False
        try:
            with self._lock:
                self._serial.write(frame)
                self._serial.flush()
            return True
        except SerialException as e:
            self.log("Write error: {{}}".format(e))
            return False

    def _reader_loop(self):
        while self.running and self._serial and self._serial.is_open:
            try:
                waiting = self._serial.in_waiting
                chunk = self._serial.read(waiting if waiting > 0 else 1)
                if chunk:
                    self._recv_buf += chunk
                    self._pump_frames()
            except SerialException as e:
                if self.running:
                    self.log("Serial read error: {{}}".format(e))
                break
            except Exception as e:
                if self.running:
                    self.log("Reader exception: {{}}".format(e))

    def start(self):
        """Open serial port (if specified) and begin receiving frames."""
        self.running = True
        if self.serial_port and SERIAL_AVAILABLE:
            try:
                self._serial = serial.Serial(
                    self.serial_port, self.baud_rate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.05,
                    write_timeout=2,
                    rtscts=False,   # CRITICAL: do not assert RTS (wired to ESP32 EN/reset)
                    dsrdtr=False,   # CRITICAL: do not assert DTR (wired to ESP32 IO0/boot)
                )
                # Explicitly deassert both lines in case a previous process left them high
                self._serial.rts = False
                self._serial.dtr = False
                time.sleep(0.1)
                self._serial.reset_input_buffer()

                self.log("Serial opened: {{}} @ {{}} baud RTS={{}} DTR={{}}".format(
                    self.serial_port, self.baud_rate,
                    self._serial.rts, self._serial.dtr))

                self._send_raw(self._encode_frame(bytes([CMD_DEVICE_QUERY, FIRMWARE_VER])))
                time.sleep(0.2)
                self._send_raw(self._encode_frame(
                    bytes([CMD_APP_START]) + bytes(7) + self.node_id.encode("utf-8")[:32]
                ))
                time.sleep(0.3)
                self._serial.reset_input_buffer()

                self._listener_thread = threading.Thread(
                    target=self._reader_loop, daemon=True, name="mc-reader"
                )
                self._listener_thread.start()
                self.log("Listener thread started")

            except SerialException as e:
                self.log("Could not open serial port: {{}}".format(e))
                self._serial = None
        else:
            self.log("No serial port - running in simulation mode")

    def stop(self):
        """Stop receiving and close the serial port."""
        self.running = False
        if self._listener_thread:
            self._listener_thread.join(timeout=2)
        if self._serial and self._serial.is_open:
            self._serial.close()
        self.log("Stopped")

    def send_message(self, content, message_type="text", channel=None):
        """Send a plain-text message (channel broadcast or simulation)."""
        msg = MeshCoreMessage(
            sender=self.node_id,
            content=content,
            message_type=message_type,
            channel=channel,
        )
        if self._serial and self._serial.is_open:
            ch_idx = 0
            ts = int(time.time())
            payload = (
                bytes([CMD_SEND_CHANNEL_TXT_MSG, TXT_TYPE_PLAIN, ch_idx])
                + struct.pack("<I", ts)
                + content.encode("utf-8")
            )
            self._send_raw(self._encode_frame(payload))
            self.log("Sent via LoRa ch{{}}: {{}}".format(ch_idx, content[:60]))
        else:
            self.log("[SIMULATION] {{}} -> {{}}".format(message_type, content[:80]))
        return msg

    def send_channel_message(self, content, channel_idx=0):
        """Send a text message to a specific MeshCore channel index."""
        if not self._serial or not self._serial.is_open:
            self.log("[SIMULATION] ch{{}}: {{}}".format(channel_idx, content))
            return True
        ts = int(time.time())
        payload = (
            bytes([CMD_SEND_CHANNEL_TXT_MSG, TXT_TYPE_PLAIN, channel_idx])
            + struct.pack("<I", ts)
            + content.encode("utf-8")
        )
        return self._send_raw(self._encode_frame(payload))

    def sync_time(self):
        """Sync the node RTC to current system time."""
        ts = int(time.time())
        payload = bytes([CMD_SET_DEVICE_TIME]) + struct.pack("<I", ts)
        self._send_raw(self._encode_frame(payload))
        self.log("RTC synced to {{}} UTC".format(datetime.utcfromtimestamp(ts)))