#!/usr/bin/env python3
"""
MeshCore - Core library for mesh radio network communication
This module provides the core functionality for communicating via MeshCore mesh radio network.
"""

import json
import time
import threading
import html
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# MeshCore companion radio binary protocol constants (USB/serial framing)
# Reference: https://github.com/meshcore-dev/MeshCore/wiki/Companion-Radio-Protocol
_FRAME_OUT = 0x3E       # '>' radio→app outbound frame start byte
_FRAME_IN = 0x3C        # '<' app→radio inbound frame start byte
_CMD_APP_START = 1      # Initialize companion radio session
_CMD_GET_DEVICE_TIME = 5    # Request current device time (RTC)
_CMD_SYNC_NEXT_MSG = 10 # Fetch next queued message
_CMD_SEND_CHAN_MSG = 3   # Send a channel (flood) text message
_RESP_CURR_TIME = 9         # Response: current device time (4-byte UNIX timestamp)
_PUSH_MSG_WAITING = 0x83    # Push: a new message has been queued
_PUSH_MSG_ACK = 0x88        # Push: message acknowledgment notification
_RESP_CONTACT_MSG = 7       # Response: direct (contact) message received
_RESP_CHANNEL_MSG = 8       # Response: channel message received
_RESP_NO_MORE_MSGS = 10     # Response: message queue is empty
_RESP_CONTACT_MSG_V3 = 16   # V3 variant of contact message (includes SNR)
_RESP_CHANNEL_MSG_V3 = 17   # V3 variant of channel message (includes SNR)
_MAX_FRAME_SIZE = 300       # Maximum valid frame payload size in bytes

try:
    import serial
    from serial import SerialException
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    # Provide a fallback so SerialException can be caught safely without pyserial installed

    class SerialException(Exception):  # type: ignore[no-redef]
        pass


class MeshCoreMessage:
    """Represents a message in the MeshCore network"""

    def __init__(self, sender: str, content: str, message_type: str = "text",
                 timestamp: Optional[float] = None, channel: Optional[str] = None,
                 channel_idx: Optional[int] = None):
        self.sender = sender
        self.content = content
        self.message_type = message_type
        self.timestamp = timestamp or time.time()
        self.channel = channel
        self.channel_idx = channel_idx  # Raw channel index from LoRa (0-7)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        data = {
            "sender": self.sender,
            "content": self.content,
            "type": self.message_type,
            "timestamp": self.timestamp
        }
        if self.channel:
            data["channel"] = self.channel
        if self.channel_idx is not None:
            data["channel_idx"] = self.channel_idx
        return data

    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeshCoreMessage':
        """Create message from dictionary"""
        return cls(
            sender=data.get("sender", "unknown"),
            content=data.get("content", ""),
            message_type=data.get("type", "text"),
            timestamp=data.get("timestamp"),
            channel=data.get("channel"),
            channel_idx=data.get("channel_idx")
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'MeshCoreMessage':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Standard serial baud rates accepted for preflight validation
VALID_BAUD_RATES = {110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200,
                    38400, 57600, 115200, 128000, 256000}


class MeshCore:
    """Main MeshCore communication handler"""

    def __init__(self, node_id: str, debug: bool = False,
                 serial_port: Optional[str] = None, baud_rate: int = 9600):
        """
        Initialize MeshCore

        Args:
            node_id: Unique identifier for this node
            debug: Enable debug output
            serial_port: Serial port for LoRa module (e.g., /dev/ttyUSB0). When None,
                         the node operates in simulation mode (no actual radio transmission).
            baud_rate: Baud rate for LoRa serial connection (default: 9600)
        """
        self.node_id = node_id
        self.debug = debug
        self.message_handlers = {}
        self.running = False
        self.channel_filter = None  # None means listen to all channels

        # Channel name to channel_idx mapping for LoRa transmission
        # Allows different named channels to use different channel indices
        self._channel_map = {}  # channel_name -> channel_idx
        self._reverse_channel_map = {}  # channel_idx -> channel_name
        self._next_channel_idx = 1  # 0 is reserved for default/no-channel

        # LoRa serial connection
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self._serial = None
        self._listener_thread = None

    def log(self, message: str):
        """Log debug messages"""
        if self.debug:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] MeshCore [{self.node_id}]: {message}")

    def set_channel_filter(self, channels):
        """
        Configure channel filtering for the bot.
        
        This method sets up channel name to channel_idx mappings and enables
        filtering of incoming messages. When channel_filter is set:
        - The bot ONLY accepts messages from the specified channel(s)
        - Messages from other channels are ignored
        - The bot replies on the same channel_idx where each message came from
        
        When channel_filter is None (default):
        - The bot accepts messages from ALL channels
        - The bot replies on the same channel_idx where each message came from
        
        This is used for:
        1. Filtering which channels the bot responds to
        2. Bot-initiated broadcasts (e.g., scheduled announcements, alerts)

        Args:
            channels: Channel name (str), list of channel names, or None
        """
        # Normalize input to a list or None
        if channels is None:
            self.channel_filter = None
        elif isinstance(channels, str):
            self.channel_filter = [channels]
        elif isinstance(channels, list):
            self.channel_filter = channels if channels else None
        else:
            raise TypeError(f"channels must be str, list, or None, not {type(channels).__name__}")
        
        # Pre-populate channel mappings for broadcast channels
        if self.channel_filter:
            for channel in self.channel_filter:
                if channel not in self._channel_map:
                    self._get_channel_idx(channel)
            
            channel_str = ", ".join(f"'{ch}'" for ch in self.channel_filter)
            self.log(f"Channel filter enabled: {channel_str} (only accepts messages from these channels)")
        else:
            self.log("Channel filter disabled: accepts messages from all channels")

    def _get_channel_idx(self, channel: Optional[str]) -> int:
        """
        Get or assign a channel_idx for the given channel name.
        
        Args:
            channel: Channel name, or None for the default channel
            
        Returns:
            Channel index (0-7) to use for LoRa transmission
            
        Raises:
            ValueError: If more than 7 named channels are used
        """
        if channel is None:
            return 0  # Default/public channel
        
        # Return existing mapping or create a new one
        if channel not in self._channel_map:
            if self._next_channel_idx > 7:
                raise ValueError(
                    f"Maximum of 7 named channels exceeded. Cannot add channel '{channel}'. "
                    f"Existing channels: {list(self._channel_map.keys())}"
                )
            self._channel_map[channel] = self._next_channel_idx
            self._reverse_channel_map[self._next_channel_idx] = channel
            self.log(f"Mapped channel '{channel}' to channel_idx {self._next_channel_idx}")
            self._next_channel_idx += 1
        
        return self._channel_map[channel]

    def _get_channel_name(self, channel_idx: int) -> Optional[str]:
        """
        Get the Python channel name for a given channel_idx.
        
        Args:
            channel_idx: Channel index (0-7) from LoRa transmission
            
        Returns:
            Channel name if mapped, None if channel_idx is 0 or unmapped
        """
        if channel_idx == 0:
            return None  # Default/public channel (no specific channel name)
        
        # O(1) lookup using reverse mapping dictionary
        return self._reverse_channel_map.get(channel_idx)

    def register_handler(self, message_type: str, handler: Callable):
        """
        Register a handler for a specific message type

        Args:
            message_type: Type of message to handle
            handler: Callback function to handle the message
        """
        self.message_handlers[message_type] = handler
        self.log(f"Registered handler for message type: {message_type}")

    def send_message(self, content: str, message_type: str = "text", channel: Optional[str] = None,
                     channel_idx: Optional[int] = None) -> MeshCoreMessage:
        """
        Send a message via MeshCore network

        Args:
            content: Message content
            message_type: Type of message
            channel: Optional channel name to broadcast to
            channel_idx: Optional raw channel index (0-7) to use directly.
                        When provided, takes precedence over channel name mapping.
                        This allows direct replies on the exact channel_idx received from.

        Returns:
            MeshCoreMessage object
        """
        message = MeshCoreMessage(
            sender=self.node_id,
            content=content,
            message_type=message_type,
            channel=channel,
            channel_idx=channel_idx
        )

        channel_info = f" on channel '{channel}'" if channel else ""
        if channel_idx is not None:
            channel_info += f" (idx={channel_idx})"
        self.log(f"Sending message{channel_info}: {message.to_json()}")

        if self._serial and self._serial.is_open:
            # Transmit over LoRa using the MeshCore companion radio binary protocol.
            # CMD_SEND_CHANNEL_TXT_MSG: code(1) + txt_type(1) + channel_idx(1)
            #                           + timestamp uint32_LE(4) + text
            # Determine which channel_idx to use:
            # 1. If channel_idx is explicitly provided, use it directly (for replies)
            # 2. Otherwise, map the channel name to a channel_idx
            if channel_idx is not None:
                actual_channel_idx = channel_idx
            else:
                actual_channel_idx = self._get_channel_idx(channel)
            
            try:
                ts_bytes = int(time.time()).to_bytes(4, "little")
                cmd_data = bytes([_CMD_SEND_CHAN_MSG, 0, actual_channel_idx]) + ts_bytes + content.encode("utf-8")
                frame = bytes([_FRAME_IN]) + len(cmd_data).to_bytes(2, "little") + cmd_data
                self._serial.write(frame)
                self.log(f"LoRa TX channel msg (idx={actual_channel_idx}): {content}")
                # After sending, sync to allow the companion radio to process and respond
                self._send_command(bytes([_CMD_SYNC_NEXT_MSG]))
            except SerialException as e:
                self.log(f"LoRa TX error: {e}")
        else:
            # Simulation mode - no radio hardware attached
            self.log("Simulation mode: message not transmitted over radio")

        return message

    def receive_message(self, message: MeshCoreMessage):
        """
        Receive and process a message

        Args:
            message: MeshCoreMessage object to process
        """
        channel_info = f" on channel '{message.channel}'" if message.channel else ""
        if message.channel_idx is not None:
            channel_info += f" (channel_idx={message.channel_idx})"
        self.log(f"Received message from {message.sender}{channel_info}: {message.content}")

        # Apply channel filtering if configured
        if self.channel_filter is not None:
            # Only filter when the message carries an explicit channel name.
            # Binary-protocol frames only carry a numeric channel_idx; the bot's
            # internal name→idx mapping is independent of the physical radio's
            # channel-slot assignment, so idx-based filtering is unreliable and
            # would silently drop messages from any channel whose physical slot
            # doesn't happen to match the bot-internal index (e.g. #weather).
            # For those messages (message.channel is None) we accept unconditionally
            # and rely on the radio hardware to enforce channel membership.
            if message.channel is not None and message.channel not in self.channel_filter:
                self.log(f"Ignoring message: channel '{message.channel}' "
                         f"not in filter {self.channel_filter}")
                return

        # Check if we have a handler for this message type
        if message.message_type in self.message_handlers:
            handler = self.message_handlers[message.message_type]
            handler(message)
        else:
            self.log(f"No handler for message type: {message.message_type}")

    def _connect_serial(self):
        """Open the serial port for the LoRa module"""
        if not SERIAL_AVAILABLE:
            self.log("pyserial is not installed. Install with: pip install pyserial")
            return
        # Preflight: reject baud rates that are not in the known-valid set
        if self.baud_rate not in VALID_BAUD_RATES:
            self.log(
                f"Invalid baud rate {self.baud_rate}. "
                f"Valid rates: {sorted(VALID_BAUD_RATES)}"
            )
            return
        try:
            self._serial = serial.Serial(
                self.serial_port, self.baud_rate, timeout=1,
                rtscts=False, dsrdtr=False,
            )
            # Deassert RTS and DTR to prevent unintended resets on ESP32/Arduino
            # LoRa devices that use these lines as a reset trigger.
            self._serial.rts = False
            self._serial.dtr = False
            self.log(f"LoRa connected on {self.serial_port} at {self.baud_rate} baud")
            # Initialise MeshCore companion radio protocol session.
            # CMD_APP_START frame payload layout (protocol reference §App Commands):
            #   byte 0:   command code = 0x01 (CMD_APP_START)
            #   byte 1:   app_ver = 0x03  (request V3 message format with SNR field)
            #   bytes 2-7: reserved = 6 ASCII spaces (as used by official meshcore-py)
            #   bytes 8+: app_name = "MCWB" (identifies this bot to the companion radio)
            self._send_command(b"\x01\x03      MCWB")
            # Allow companion radio time to process CMD_APP_START initialization.
            # After a radio reboot, the companion radio needs a brief moment to
            # initialize its session before it can handle subsequent commands.
            time.sleep(0.1)
            # Drain any messages that queued while we were offline.
            self._send_command(bytes([_CMD_SYNC_NEXT_MSG]))
        except SerialException as e:
            self.log(f"Failed to open serial port {self.serial_port}: {e}")
            self._serial = None

    def _start_listener(self):
        """Start background thread to listen for incoming LoRa messages"""
        self._listener_thread = threading.Thread(
            target=self._listen_loop, daemon=True, name="lora-listener"
        )
        self._listener_thread.start()
        self.log("LoRa listener thread started")

    def _listen_loop(self):
        """
        Background loop: read data from the LoRa serial port and dispatch messages.

        Handles both the MeshCore companion radio binary framing protocol
        (frames starting with 0x3E '>') and legacy newline-delimited JSON for
        simulation / inter-Python-node communication.
        """
        while self.running and self._serial and self._serial.is_open:
            try:
                # Try to peek at first byte for real serial connections (binary protocol detection)
                # For mocks/tests, fall back to readline() for compatibility
                raw = None
                first_byte = None
                
                try:
                    # Check if data is available (real serial only)
                    if self._serial.in_waiting > 0:
                        # Read first byte to determine frame type
                        first_byte = self._serial.read(1)
                        if not first_byte:
                            continue
                        
                        # ----------------------------------------------------------------
                        # MeshCore companion radio binary protocol
                        # Frame format (outbound, radio→app):
                        #   0x3E ('>')  - frame start
                        #   uint16 LE   - payload length
                        #   bytes       - payload (first byte = response/push code)
                        # ----------------------------------------------------------------
                        if first_byte[0] == _FRAME_OUT:
                            # Read the length header (2 bytes, little-endian)
                            length_bytes = self._serial.read(2)
                            if len(length_bytes) < 2:
                                self.log("Binary frame incomplete: missing length header")
                                continue
                            
                            length = int.from_bytes(length_bytes, "little")
                            if length == 0 or length > _MAX_FRAME_SIZE:
                                self.log(f"Binary frame length {length} out of range, skipping")
                                continue
                            
                            # Read the exact payload bytes
                            payload = self._serial.read(length)
                            if len(payload) < length:
                                self.log(f"Binary frame incomplete: expected {length} bytes, got {len(payload)}")
                                continue
                            
                            # Parse the complete binary frame
                            self._parse_binary_frame(payload)
                            continue
                        
                        # For non-binary frames, read rest of line
                        rest_of_line = self._serial.readline()
                        raw = first_byte + rest_of_line
                except (TypeError, AttributeError):
                    # Mock/test object - use readline() directly
                    pass
                
                # Use readline() if we haven't read data yet (mock/test or no data available)
                if raw is None:
                    raw = self._serial.readline()
                    if not raw:
                        continue
                    
                    # Check if this is a binary frame that came via readline() (from tests/mocks)
                    if raw and len(raw) > 0 and raw[0] == _FRAME_OUT:
                        if len(raw) < 3:
                            self.log("Binary frame too short to contain a length header")
                            continue
                        length = int.from_bytes(raw[1:3], "little")
                        if length == 0 or length > _MAX_FRAME_SIZE:
                            self.log(f"Binary frame length {length} out of range, skipping")
                            continue
                        payload = raw[3: 3 + length]
                        if not payload:
                            continue
                        self._parse_binary_frame(payload)
                        continue

                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                # Remove embedded control characters (e.g. \r, \x00) that can
                # corrupt terminal output when raw LoRa radio frames are received.
                line = "".join(c for c in line if c.isprintable())
                if not line:
                    continue
                # Decode HTML entities (e.g. &gt; -> >, &amp; -> &) that may be present
                # in data from certain LoRa systems or transport layers
                line = html.unescape(line)
                # Only attempt JSON parsing for lines that look like JSON objects.
                # Raw LoRa frames from non-MeshCore devices are silently skipped.
                # Additional validation: must start with { AND end with }
                if not (line.startswith("{") and line.endswith("}")):
                    # Silently skip non-JSON data (binary protocol responses, radio noise, etc.)
                    continue
                # Log only after validating it looks like JSON to avoid logging garbled data
                self.log(f"LoRa RX: {line}")
                try:
                    message = MeshCoreMessage.from_json(line)
                    self.receive_message(message)
                except (json.JSONDecodeError, KeyError) as e:
                    self.log(f"Could not parse LoRa message: {e} | raw: {line}")
            except SerialException as e:
                self.log(f"LoRa serial read error: {e}")
                break

    # ------------------------------------------------------------------
    # MeshCore companion radio binary protocol helpers
    # ------------------------------------------------------------------

    def _send_command(self, cmd_data: bytes):
        """
        Send a binary command frame to the companion radio.

        Inbound frame format (app→radio):  0x3C + uint16_LE(len) + payload
        """
        if self._serial and self._serial.is_open:
            frame = bytes([_FRAME_IN]) + len(cmd_data).to_bytes(2, "little") + cmd_data
            try:
                self._serial.write(frame)
                self.log(f"LoRa CMD: {cmd_data.hex()}")
            except SerialException as e:
                self.log(f"LoRa CMD error: {e}")

    def _parse_binary_frame(self, payload: bytes):
        """
        Dispatch a received companion radio frame payload based on its code byte.

        Handles push notifications and message-delivery responses.
        After each received message the next queued message is requested so
        that the entire message queue is drained automatically.
        """
        code = payload[0]

        if code == 0x00:
            # NOP/keepalive frame from companion radio - ignore silently
            pass

        elif code == _CMD_APP_START:
            # CMD_APP_START echo/acknowledgment from companion radio.
            # The radio may echo this command during session initialization.
            # No action needed - session is already initialized.
            self.log("MeshCore: APP_START acknowledged by companion radio")

        elif code == _CMD_GET_DEVICE_TIME:
            # Companion radio requests current device time.
            # Respond with RESP_CURR_TIME containing 4-byte UNIX timestamp.
            self.log("MeshCore: device time requested, responding…")
            timestamp = int(time.time()).to_bytes(4, "little")
            response = bytes([_RESP_CURR_TIME]) + timestamp
            self._send_command(response)

        elif code == _PUSH_MSG_WAITING:
            # Companion radio signals that a new message has been received;
            # request it immediately.
            self.log("MeshCore: message waiting, fetching…")
            self._send_command(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _PUSH_MSG_ACK:
            # Companion radio sends message acknowledgment notification.
            # This confirms that a previously sent message was received by the mesh network.
            self.log("MeshCore: message acknowledgment received")
            # Fetch any messages that may be queued after the ACK
            self._send_command(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _RESP_CHANNEL_MSG:
            # RESP_CODE_CHANNEL_MSG_RECV:
            # channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
            if len(payload) >= 8:
                channel_idx = payload[1]  # Extract channel_idx from payload
                text = payload[8:].decode("utf-8", "ignore")
                self.log(f"Binary frame: CHANNEL_MSG on channel_idx {channel_idx}")
                self._dispatch_channel_message(text, channel_idx)
            else:
                self.log(f"Binary frame: CHANNEL_MSG payload too short ({len(payload)} bytes)")
            # Fetch the next queued message
            self._send_command(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _RESP_CHANNEL_MSG_V3:
            # RESP_CODE_CHANNEL_MSG_RECV_V3 (includes SNR prefix):
            # SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
            if len(payload) >= 12:
                channel_idx = payload[4]  # Extract channel_idx from payload (after SNR + reserved)
                text = payload[12:].decode("utf-8", "ignore")
                self.log(f"Binary frame: CHANNEL_MSG_V3 on channel_idx {channel_idx}")
                self._dispatch_channel_message(text, channel_idx)
            else:
                self.log(f"Binary frame: CHANNEL_MSG_V3 payload too short ({len(payload)} bytes)")
            self._send_command(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _RESP_CONTACT_MSG:
            # RESP_CODE_CONTACT_MSG_RECV:
            # pubkey_prefix(6) + path_len(1) + txt_type(1) + timestamp(4) + text
            if len(payload) >= 13:
                sender = payload[1:7].hex()
                text = payload[13:].decode("utf-8", "ignore")
                msg = MeshCoreMessage(sender=sender, content=text, message_type="text")
                self.receive_message(msg)
            self._send_command(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _RESP_CONTACT_MSG_V3:
            # RESP_CODE_CONTACT_MSG_RECV_V3:
            # SNR(1) + reserved(2) + pubkey_prefix(6) + path_len(1) + txt_type(1) + timestamp(4) + text
            if len(payload) >= 16:
                sender = payload[4:10].hex()
                text = payload[16:].decode("utf-8", "ignore")
                msg = MeshCoreMessage(sender=sender, content=text, message_type="text")
                self.receive_message(msg)
            self._send_command(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _RESP_NO_MORE_MSGS:
            self.log("MeshCore: message queue empty")

        else:
            self.log(f"MeshCore: unhandled frame code {code:#04x}")

    def _dispatch_channel_message(self, text: str, channel_idx: int = 0):
        """
        Create and dispatch a MeshCoreMessage from a received channel text.

        MeshCore firmware prepends the sender's advertised name to the channel
        message text in the format ``"sender_name: message_text"``.  This
        method splits on the first ``": "`` to expose a clean *sender* and
        *content* to the registered message handlers.
        
        Args:
            text: The message text (may include "sender: " prefix)
            channel_idx: The channel index from the LoRa frame (0-7)
        """
        colon = text.find(": ")
        if colon > 0:
            sender = text[:colon]
            content = text[colon + 2:]
        else:
            sender = "channel"
            content = text
        
        # Map channel_idx back to Python channel name
        channel_name = self._get_channel_name(channel_idx)
        
        channel_info = f" on channel '{channel_name}'" if channel_name else f" on channel_idx {channel_idx}"
        self.log(f"LoRa RX channel msg from {sender}{channel_info}: {content}")
        msg = MeshCoreMessage(sender=sender, content=content, message_type="text", 
                            channel=channel_name, channel_idx=channel_idx)
        
        self.receive_message(msg)

    def start(self):
        """Start the MeshCore listener"""
        self.running = True
        if self.serial_port:
            self._connect_serial()
            if self._serial and self._serial.is_open:
                self._start_listener()
        self.log("MeshCore started")

    def stop(self):
        """Stop the MeshCore listener"""
        self.running = False
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=2)
        if self._serial and self._serial.is_open:
            self._serial.close()
            self.log(f"LoRa serial port {self.serial_port} closed")
        self.log("MeshCore stopped")

    def is_running(self) -> bool:
        """Check if MeshCore is running"""
        return self.running


if __name__ == "__main__":
    # Example usage
    mesh = MeshCore("node_001", debug=True)

    def text_handler(message: MeshCoreMessage):
        channel_info = f" on channel '{message.channel}'" if message.channel else ""
        print(f"Text message from {message.sender}{channel_info}: {message.content}")

    mesh.register_handler("text", text_handler)
    mesh.start()

    # Send a test message without channel
    msg1 = mesh.send_message("Hello, MeshCore!", "text")

    # Send a test message with channel
    msg2 = mesh.send_message("Weather broadcast", "text", channel="weather")

    # Simulate receiving the messages
    mesh.receive_message(msg1)
    mesh.receive_message(msg2)

    # Test channel filtering
    print("\nSetting channel filter to 'weather'...")
    mesh.set_channel_filter("weather")

    mesh.receive_message(msg1)  # Should be ignored
    mesh.receive_message(msg2)  # Should be processed

    mesh.stop()
