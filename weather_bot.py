#!/usr/bin/env python3
"""
MCWBv2 - MeshCore Weather Bot
Lightweight weather bot for the MeshCore #weather channel.
Responds to: WX [location] or weather [location]
Uses the free Open-Meteo API (no API key required).
"""

import sys
import re
import time
import threading
import argparse

from meshcore import MeshCore, MeshCoreMessage

try:
    import requests
except ImportError:
    print("Error: requests not found. Install with: pip install requests")
    sys.exit(1)

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("Error: pyserial not found. Install with: pip install pyserial")
    sys.exit(1)

# ---------------------------------------------------------------------------
# MeshCore companion radio binary protocol constants
# Reference: https://github.com/meshcore-dev/MeshCore/wiki/Companion-Radio-Protocol
# ---------------------------------------------------------------------------
_FRAME_OUT = 0x3E           # '>' radio→app frame start byte
_FRAME_IN = 0x3C            # '<' app→radio frame start byte
_CMD_APP_START = 0x01       # Initialise companion radio session
_CMD_GET_DEVICE_TIME = 0x05 # Radio requests current device time; app must respond
_CMD_SYNC_NEXT_MSG = 0x0A   # Request next queued message
_CMD_SEND_CHAN_MSG = 0x03    # Send a channel (flood) text message
_RESP_CURR_TIME = 0x09      # Response: current time (4-byte UNIX timestamp LE)
_RESP_CHANNEL_MSG = 0x08    # Channel message received
_RESP_CHANNEL_MSG_V3 = 0x11 # Channel message received (V3, includes SNR)
_RESP_CONTACT_MSG_V3 = 0x10 # Direct (contact) message received (V3, includes SNR)
_PUSH_BASE = 0x80           # Push: base flag for push notifications (bit 7 set)
_PUSH_SEND_CONFIRMED = 0x82 # Push: outgoing message ACK'd by mesh
_PUSH_MSG_WAITING = 0x83    # Push: new message queued
_PUSH_CHAN_MSG = 0x88        # Push: inline channel message (0x80 | RESP_CHANNEL_MSG)
_PUSH_NO_MORE_MSGS = 0x8A   # Push: no more messages (0x80 | CMD_SYNC_NEXT_MSG)
_PUSH_CONTACT_MSG_V3 = 0x90 # Push: inline contact message V3 (0x80 | RESP_CONTACT_MSG_V3)
_RESP_NO_MORE_MSGS = 0x0A   # No more messages in queue (same value as CMD_SYNC_NEXT_MSG)

# Channel message format constants
_OLD_FORMAT_HEADER_SIZE = 8   # code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4)
_V3_FORMAT_HEADER_SIZE = 11   # code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4)
_MIN_REALISTIC_SNR = 20       # Minimum typical SNR value for radio signals (dB)
_MAX_REALISTIC_SNR = 60       # Maximum typical SNR value for radio signals (dB)
_MAX_VALID_CHANNEL_IDX = 7    # Maximum valid channel index (0-7)

# Default sender name for messages without "SenderName: " prefix
# Matches meshcore.py's behavior in _dispatch_channel_message
_DEFAULT_SENDER = "channel"

# WMO weather interpretation codes
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm w/ slight hail", 99: "Thunderstorm w/ heavy hail",
}

ANNOUNCE_INTERVAL = 3 * 60 * 60  # seconds between periodic announcements
ANNOUNCE_MESSAGE = "Hello this is the WX BoT. To get a weather update simply type WX and your location."


class WeatherBot:
    """Lightweight MeshCore weather bot."""

    def __init__(self, port=None, baud=115200, debug=False, announce=False,
                 allowed_channel_idx=None, node_id=None, announce_channel=None,
                 weather_channel_idx=None, country=None, channel=None,
                 serial_port=None, baud_rate=None):
        # serial_port and baud_rate are aliases for port and baud
        self.port = serial_port or port
        self.baud = baud_rate or baud
        self.debug = debug
        self.announce = announce or (announce_channel is not None)
        self.allowed_channel_idx = allowed_channel_idx
        self._ser = None
        self._running = False
        # channel_idx used for periodic announcements and weather responses
        # If weather_channel_idx is specified, use it; otherwise use first received message's channel
        self.weather_channel_idx = weather_channel_idx
        self._announce_channel_idx = weather_channel_idx if weather_channel_idx is not None else 0
        self.announce_channel = announce_channel
        # Country code for filtering geocoding results (e.g., "GB", "US", "FR")
        self.country = country
        # Parse comma-separated channel names (e.g. "weather,alerts") into a list.
        # Used for broadcasting responses and setting up channel name filtering via
        # the JSON-based MeshCore channel map rather than relying solely on
        # numeric channel_idx heuristics.
        if channel:
            self.channels = [ch.strip() for ch in channel.split(",") if ch.strip()]
        else:
            self.channels = []
        # MeshCore integration for public message-handling API
        self.mesh = MeshCore(node_id=node_id or "MCWB", debug=debug,
                             serial_port=self.port, baud_rate=self.baud)
        # Register this bot as the text message handler so that binary-protocol
        # frames dispatched by meshcore._parse_binary_frame reach handle_message.
        self.mesh.register_handler("text", self.handle_message)
        # Apply channel name filter when specific channels are configured.
        # Binary-protocol frames (channel=None) are always accepted regardless
        # of this filter – see meshcore.receive_message for details.
        if self.channels:
            self.mesh.set_channel_filter(self.channels)

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    # Maximum length for logged content to prevent log spam
    _MAX_LOG_LENGTH = 200

    def _sanitize_for_log(self, text: str) -> str:
        """
        Sanitize text for safe logging by removing control characters and
        limiting length. This prevents terminal corruption from garbled/encrypted data.
        """
        if not text:
            return text
        
        # Remove control characters except newline, tab, carriage return
        sanitized = ''.join(
            char if (ord(char) >= 32 or char in '\n\t\r') else f'\\x{ord(char):02x}'
            for char in text
        )
        
        # Limit length to prevent log spam
        if len(sanitized) > self._MAX_LOG_LENGTH:
            sanitized = sanitized[:self._MAX_LOG_LENGTH] + f"... ({len(sanitized) - self._MAX_LOG_LENGTH} more chars)"
        
        return sanitized

    def _log(self, msg):
        if self.debug:
            print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

    # ------------------------------------------------------------------
    # Lifecycle helpers (mesh-level start/stop)
    # ------------------------------------------------------------------

    def start(self):
        """Start the MeshCore listener (mesh-level only)."""
        self.mesh.start()

    def stop(self):
        """Stop the MeshCore listener (mesh-level only)."""
        self.mesh.stop()

    def send_response(self, content: str, reply_to_channel: str = None,
                      reply_to_channel_idx: int = None):
        """
        Send a weather response via the MeshCore mesh.

        If *reply_to_channel_idx* is given, the response is sent back on
        exactly that channel slot (the slot the query arrived on).
        Otherwise the response is broadcast to every channel in
        ``self.channels``.  When no channels are configured the message
        is sent without a channel identifier.
        """
        if reply_to_channel_idx is not None:
            self.mesh.send_message(content, "text", reply_to_channel,
                                   reply_to_channel_idx)
        elif self.channels:
            for ch in self.channels:
                self.mesh.send_message(content, "text", ch)
        else:
            self.mesh.send_message(content, "text", None)

    # ------------------------------------------------------------------
    # Serial / MeshCore protocol helpers
    # ------------------------------------------------------------------

    def _connect(self):
        """Open the serial port and initialise the MeshCore session."""
        port = self.port
        if not port:
            candidates = [
                p.device for p in list_ports.comports()
                if any(x in p.device for x in ("ttyUSB", "ttyACM", "ttyAMA", "COM"))
            ]
            if not candidates:
                print("No serial port found. Check USB connection and try --port.")
                return False
            port = candidates[0]
            print(f"Auto-detected port: {port}")

        try:
            self._ser = serial.Serial(port, self.baud, timeout=1,
                                      rtscts=False, dsrdtr=False)
            self._ser.rts = False
            self._ser.dtr = False
            # CMD_APP_START payload: code(1) + app_ver(1) + reserved(6 spaces) + app_name("MCWB")
            self._send_cmd(bytes([_CMD_APP_START, 0x03]) + b"      MCWB")
            time.sleep(0.1)
            print(f"Connected to MeshCore on {port} at {self.baud} baud")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to {port}: {e}")
            return False

    def _send_cmd(self, data: bytes):
        """Wrap data in an inbound frame and write to serial."""
        frame = bytes([_FRAME_IN]) + len(data).to_bytes(2, "little") + data
        self._ser.write(frame)
        self._log(f"TX: {data.hex()}")

    def _send_channel_msg(self, text: str, channel_idx: int):
        """Send a text message on the given channel slot."""
        ts = int(time.time()).to_bytes(4, "little")
        payload = bytes([_CMD_SEND_CHAN_MSG, 0, channel_idx]) + ts + text.encode("utf-8")
        self._send_cmd(payload)
        self._log(f"Sent on channel_idx={channel_idx}: {text}")

    def _read_frame(self):
        """Read one binary frame from serial. Returns payload bytes or None."""
        try:
            if not self._ser.in_waiting:
                return None
            first = self._ser.read(1)
            if not first or first[0] != _FRAME_OUT:
                return None
            lb = self._ser.read(2)
            if len(lb) < 2:
                return None
            length = int.from_bytes(lb, "little")
            if length == 0 or length > 300:
                return None
            payload = self._ser.read(length)
            if len(payload) < length:
                return None
            return payload
        except serial.SerialException:
            return None

    def _parse_channel_message(self, payload: bytes):
        """
        Parse channel message payload and extract channel_idx and text.
        Handles both old format and V3 format (with SNR).
        
        Format Detection Heuristics:
        - If payload >= 12 bytes and SNR (byte 1) is in realistic range (20-60 dB)
          and channel_idx (byte 4) is valid (0-7), use V3 format
        - If payload >= 12 bytes and byte 1 > 7 (impossible as channel_idx in old format)
          and byte 4 is valid channel_idx, use V3 format
        - If payload >= 12 bytes and bytes 2-3 (reserved in V3) are both 0x00
          and byte 4 is a valid channel_idx, use V3 format
        - Otherwise, use old format
        
        Encryption Detection:
        - After parsing, check if raw message bytes contain reasonable printable characters
        - Encrypted messages will have mostly non-printable/control characters in raw bytes
        
        V3 format: code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
        Old format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
        
        Returns:
            tuple: (channel_idx, text) or (None, None) if parsing fails or message is encrypted
        """
        # Minimum 8 bytes required for old format header
        if len(payload) < _OLD_FORMAT_HEADER_SIZE:
            self._log(f"Message too short ({len(payload)} bytes, need >= {_OLD_FORMAT_HEADER_SIZE})")
            return (None, None)
        
        # Try V3 format if payload is long enough (minimum 12 bytes for V3 header + text)
        if len(payload) >= _V3_FORMAT_HEADER_SIZE + 1:
            snr_value = payload[1]
            reserved1 = payload[2]
            reserved2 = payload[3]
            v3_channel_idx = payload[4]
            old_channel_idx = payload[1]
            
            # Check if this looks like V3 format using multiple heuristics
            use_v3_format = False
            
            # Heuristic 1: SNR in realistic range AND valid channel_idx = V3 format
            if _MIN_REALISTIC_SNR <= snr_value <= _MAX_REALISTIC_SNR and 0 <= v3_channel_idx <= _MAX_VALID_CHANNEL_IDX:
                use_v3_format = True
            
            # Heuristic 2: Old format would be invalid (channel_idx > 7), but V3 is valid
            # This handles cases where the old format interpretation doesn't make sense
            elif old_channel_idx > _MAX_VALID_CHANNEL_IDX and 0 <= v3_channel_idx <= _MAX_VALID_CHANNEL_IDX:
                use_v3_format = True
            
            # Heuristic 3: Reserved bytes are 0x00 AND valid channel_idx at position 4 = V3 format
            # This handles V3 messages with low SNR values (0-7) that could be confused with
            # old format channel_idx. The reserved bytes being 0x00 is a strong V3 indicator.
            # However, exclude SNR=0 as it's unrealistic (signals need some SNR to be received)
            elif reserved1 == 0x00 and reserved2 == 0x00 and snr_value > 0 and 0 <= v3_channel_idx <= _MAX_VALID_CHANNEL_IDX:
                use_v3_format = True
            
            # If any heuristic matched, parse as V3 format
            if use_v3_format:
                channel_idx = v3_channel_idx
                text_bytes = payload[_V3_FORMAT_HEADER_SIZE:]
                # Check if raw bytes are encrypted (mostly non-printable/control characters)
                if not self._is_valid_message_bytes(text_bytes):
                    self._log(f"V3 format: Message appears encrypted/garbled (channel_idx={channel_idx})")
                    return (None, None)
                text = text_bytes.decode("utf-8", "ignore")
                return (channel_idx, text)
        
        # Fall back to old format
        channel_idx = payload[1]
        # Validate channel_idx is in valid range (0-7)
        # Invalid indices indicate encrypted/garbled messages
        if not (0 <= channel_idx <= _MAX_VALID_CHANNEL_IDX):
            self._log(f"Old format: Invalid channel_idx={channel_idx} (valid range: 0-{_MAX_VALID_CHANNEL_IDX})")
            return (None, None)
        text_bytes = payload[_OLD_FORMAT_HEADER_SIZE:]
        # Check if raw bytes are encrypted (mostly non-printable/control characters)
        if not self._is_valid_message_bytes(text_bytes):
            self._log(f"Old format: Message appears encrypted/garbled (channel_idx={channel_idx})")
            return (None, None)
        text = text_bytes.decode("utf-8", "ignore")
        return (channel_idx, text)

    def _is_valid_message_bytes(self, data: bytes) -> bool:
        """
        Check if raw message bytes appear to be valid text (not encrypted/garbled).
        
        Encrypted messages typically contain many non-printable control characters.
        Valid messages should have mostly printable ASCII/UTF-8 bytes.
        
        This checks the RAW bytes before UTF-8 decoding to avoid losing information
        about invalid byte sequences that would be stripped by decode("utf-8", "ignore").
        
        Args:
            data: The raw message bytes (after header)
            
        Returns:
            True if bytes appear to be valid text, False if likely encrypted/garbled
        """
        if not data:
            return False
        
        # First, try to decode as UTF-8 to check for valid encoding
        # Encrypted/garbled data often has invalid UTF-8 sequences
        try:
            decoded = data.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            # If it can't be decoded as valid UTF-8, it's likely encrypted/garbled
            return False
        
        # Count printable ASCII characters in the decoded string
        # Encrypted data, even if it happens to decode as UTF-8, will have
        # many control characters or unprintable Unicode characters
        printable_count = 0
        control_count = 0
        for char in decoded:
            char_code = ord(char)
            # Printable ASCII (space through ~) or newline/tab/carriage return
            if 32 <= char_code <= 126 or char_code in (9, 10, 13):
                printable_count += 1
            # Control characters (excluding whitespace)
            elif char_code < 32 or char_code == 127:
                control_count += 1
            # For non-ASCII Unicode characters (> 127), count as printable if they're
            # in commonly used Unicode ranges. We use 0x1000 (4096) as the threshold
            # which covers most Latin, Cyrillic, Greek, and other common scripts
            # while excluding more exotic Unicode blocks that are unlikely in normal text.
            elif char_code < 0x1000:
                printable_count += 1
        
        # Reject if too many control characters
        if len(decoded) > 0 and control_count / len(decoded) > 0.1:
            return False
        
        # Require at least 70% printable characters
        if len(decoded) > 0:
            printable_ratio = printable_count / len(decoded)
            return printable_ratio >= 0.70
        
        return False

    def _dispatch(self, payload: bytes):
        """Dispatch a received frame payload."""
        code = payload[0]
        self._log(f"RX code={code:#04x} len={len(payload)}")

        if code == 0x00:
            pass  # NOP / keepalive – ignore silently

        elif code == _CMD_APP_START:
            pass  # APP_START echo from radio – session already initialised

        elif code == _CMD_GET_DEVICE_TIME:
            # Radio requests the current wall-clock time so it can keep its RTC
            # in sync. Respond immediately with RESP_CURR_TIME + 4-byte LE timestamp.
            ts = int(time.time()).to_bytes(4, "little")
            self._send_cmd(bytes([_RESP_CURR_TIME]) + ts)
            self._log("Responded to CMD_GET_DEVICE_TIME")

        elif code == _PUSH_SEND_CONFIRMED:
            self._log("Send confirmed by mesh network")

        elif code == _PUSH_MSG_WAITING:
            self._send_cmd(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _PUSH_CHAN_MSG and len(payload) >= 8:
            # Parse channel message (handles both old format and V3 format with SNR)
            channel_idx, text = self._parse_channel_message(payload)
            if channel_idx is not None:
                self._handle_channel_message(text, channel_idx)
            self._send_cmd(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _RESP_CHANNEL_MSG and len(payload) >= 8:
            # Parse channel message (handles both old format and V3 format with SNR)
            channel_idx, text = self._parse_channel_message(payload)
            if channel_idx is not None:
                self._handle_channel_message(text, channel_idx)
            self._send_cmd(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _RESP_CHANNEL_MSG_V3 and len(payload) >= 12:
            # code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) = 11 bytes; text follows
            channel_idx = payload[4]
            # Validate channel_idx is in valid range (0-7)
            if 0 <= channel_idx <= _MAX_VALID_CHANNEL_IDX:
                text = payload[11:].decode("utf-8", "ignore")
                self._handle_channel_message(text, channel_idx)
            self._send_cmd(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _RESP_NO_MORE_MSGS:
            pass  # queue empty – nothing to do

        elif code == _PUSH_BASE:
            # Base push notification frame (0x80) - may occur on some firmware versions
            pass  # ignore silently

        elif code == _PUSH_NO_MORE_MSGS:
            # Push notification: no more messages (0x8a = 0x80 | 0x0a)
            pass  # queue empty – nothing to do

        elif code == _PUSH_CONTACT_MSG_V3:
            # Push notification: inline contact message V3 (0x90 = 0x80 | 0x10)
            # Contact (direct) messages are not handled by weather bot
            self._log("Received contact message (ignored by weather bot)")

        else:
            self._log(f"Unhandled frame code {code:#04x}")

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    def _handle_channel_message(self, text: str, channel_idx: int):
        """Parse a raw channel message and respond if it is a weather command."""
        # Filter by channel_idx if specified
        if self.allowed_channel_idx is not None and channel_idx != self.allowed_channel_idx:
            self._log(f"Ignoring message from channel_idx={channel_idx} (filter={self.allowed_channel_idx})")
            return

        # MeshCore prepends "SenderName: " to channel messages.
        # However, messages from new hashtag channels or self-sent messages
        # may not have this prefix, so we should still process them.
        colon = text.find(": ")
        if colon > 0:
            sender = text[:colon]
            content = text[colon + 2:]
        else:
            # No "SenderName: " prefix found - treat as message from channel
            # This matches meshcore.py's behavior in _dispatch_channel_message
            sender = _DEFAULT_SENDER
            content = text
            self._log(f"channel_idx={channel_idx} message without SenderName: prefix, using sender='{sender}'")

        # Sanitize content for logging to prevent terminal corruption
        safe_sender = self._sanitize_for_log(sender)
        safe_content = self._sanitize_for_log(content)
        self._log(f"channel_idx={channel_idx} {safe_sender}: {safe_content}")

        # Remember this channel for periodic announcements (only if not explicitly configured)
        if self.weather_channel_idx is None:
            self._announce_channel_idx = channel_idx

        location = self._parse_command(content)
        if location:
            print(f"WX request for '{location}' from {sender}", flush=True)
            response = self._get_weather(location)
            print(f"Response:\n{response}\n", flush=True)
            self._send_channel_msg(response, channel_idx)

    @staticmethod
    def _parse_command(text: str):
        """Return location string if text matches WX/weather command, else None."""
        m = re.match(r"^(?:wx|weather)\s+(.+)$", text.strip(), re.IGNORECASE)
        return m.group(1).strip() if m else None

    def parse_weather_command(self, text: str):
        """Public alias for _parse_command."""
        return self._parse_command(text)

    def get_weather_description(self, code: int) -> str:
        """Return human-readable description for a WMO weather code."""
        return WEATHER_CODES.get(code, f"Code {code}")

    def format_weather_response(self, location_data: dict, weather_data: dict) -> str:
        """Format a weather response from pre-fetched location and weather data."""
        name = location_data.get("name", "Unknown")
        country = location_data.get("country_code", location_data.get("country", ""))
        loc_str = f"{name}, {country}" if country else name
        c = weather_data.get("current", {})
        weather_code = c.get("weather_code", 0)
        cond = WEATHER_CODES.get(weather_code, f"Code {weather_code}")
        return (
            f"{loc_str}\n"
            f"{cond}\n"
            f"Temp: {c.get('temperature_2m', 'N/A')}°C "
            f"(feels {c.get('apparent_temperature', 'N/A')}°C)\n"
            f"Humid: {c.get('relative_humidity_2m', 'N/A')}%\n"
            f"Wind: {c.get('wind_speed_10m', 'N/A')} km/h "
            f"at {c.get('wind_direction_10m', 'N/A')}°\n"
            f"Precip: {c.get('precipitation', 'N/A')} mm"
        )

    def handle_message(self, msg: MeshCoreMessage):
        """Handle a MeshCoreMessage and send a weather response via self.mesh."""
        location = self._parse_command(msg.content)
        if location:
            response = self._get_weather(location)
            # Reply on the exact channel slot the query arrived on (when known),
            # or broadcast to all configured channels.  Using send_response
            # keeps the routing logic in one place.
            self.send_response(response, reply_to_channel=msg.channel,
                               reply_to_channel_idx=msg.channel_idx)

    def send_announcement(self):
        """Send the periodic announcement message to the configured announce channel."""
        if self.announce_channel is None:
            return
        self.mesh.send_message(ANNOUNCE_MESSAGE, "text", self.announce_channel)

    # ------------------------------------------------------------------
    # Weather data
    # ------------------------------------------------------------------

    def geocode_location(self, location: str):
        """Geocode *location* name via Open-Meteo.  Returns the first result
        dict (with ``latitude``, ``longitude``, ``name``, etc.) or ``None``."""
        geo_params = {"name": location, "count": 1, "language": "en", "format": "json"}
        if self.country:
            geo_params["country"] = self.country
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params=geo_params,
            timeout=10,
        ).json()
        if "results" not in geo or not geo["results"]:
            return None
        return geo["results"][0]

    def get_weather(self, lat: float, lon: float) -> dict:
        """Fetch current weather for the given coordinates.  Returns the raw
        Open-Meteo response dict (with a ``"current"`` key)."""
        return requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "temperature_2m,apparent_temperature,"
                    "relative_humidity_2m,precipitation,"
                    "weather_code,wind_speed_10m,wind_direction_10m"
                ),
                "timezone": "auto",
            },
            timeout=10,
        ).json()

    def _get_weather(self, location: str) -> str:
        """Fetch weather for *location* and return a formatted string."""
        try:
            r = self.geocode_location(location)
            if r is None:
                return f"Location not found: {location}"
            lat, lon = r["latitude"], r["longitude"]
            wx = self.get_weather(lat, lon)
            return self.format_weather_response(r, wx)
        except Exception as e:
            return f"Weather error: {e}"

    # ------------------------------------------------------------------
    # Main run loop
    # ------------------------------------------------------------------

    def _listen_loop(self):
        """Background thread: read and dispatch frames from the radio."""
        while self._running and self._ser and self._ser.is_open:
            payload = self._read_frame()
            if payload:
                self._dispatch(payload)
            else:
                time.sleep(0.05)

    def run(self):
        """Connect and run the bot until Ctrl-C."""
        if not self._connect():
            return

        self._running = True
        listener = threading.Thread(target=self._listen_loop, daemon=True,
                                    name="mcwb-listener")
        listener.start()

        # Drain any messages queued while the bot was offline
        self._send_cmd(bytes([_CMD_SYNC_NEXT_MSG]))

        if self.weather_channel_idx is not None:
            print(f"MCWBv2 running. Weather channel configured as channel_idx={self.weather_channel_idx}.")
            print(f"Listening ONLY on channel_idx={self.weather_channel_idx}.")
            print(f"Send 'WX [location]' or 'weather [location]' on that channel.")
        elif self.allowed_channel_idx is not None:
            print(f"MCWBv2 running. Listening ONLY on channel_idx={self.allowed_channel_idx}.")
            print(f"Send 'WX [location]' or 'weather [location]' on that channel.")
        else:
            print("MCWBv2 running. Send 'WX [location]' or 'weather [location]' on any channel.")
        print("Press Ctrl+C to stop.\n", flush=True)

        last_announce = time.time()
        if self.announce:
            self._send_channel_msg(ANNOUNCE_MESSAGE, self._announce_channel_idx)

        try:
            while self._running:
                time.sleep(1)
                if self.announce and (time.time() - last_announce >= ANNOUNCE_INTERVAL):
                    self._send_channel_msg(ANNOUNCE_MESSAGE, self._announce_channel_idx)
                    last_announce = time.time()
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self._running = False
            if self._ser:
                self._ser.close()
            print("MCWBv2 stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="MCWBv2 – MeshCore Weather Bot for the #weather channel"
    )
    parser.add_argument("-p", "--port",
                        help="Serial port (e.g. /dev/ttyUSB0). Auto-detects if omitted.")
    parser.add_argument("-b", "--baud", type=int, default=115200,
                        help="Baud rate (default: 115200)")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Enable debug output")
    parser.add_argument("-a", "--announce", action="store_true",
                        help="Send periodic announcements every 3 hours")
    parser.add_argument("--channel",
                        help="Comma-separated list of MeshCore hashtag channel names to listen "
                             "and respond on (e.g. 'weather' or 'weather,alerts'). "
                             "Binary-protocol frames without a channel name are always accepted. "
                             "When omitted the bot responds on any channel.")
    parser.add_argument("-c", "--channel-idx", type=int,
                        help="Only respond to messages from this channel index (e.g., 1 for #weather)")
    parser.add_argument("-w", "--weather-channel-idx", type=int,
                        help="Specify which channel index to use for announcements. "
                             "Bot will still respond to messages from ANY channel unless --channel-idx is also specified.")
    parser.add_argument("--country",
                        help="Default country code for geocoding (e.g., GB, US, FR). "
                             "Filters location searches to prefer cities in this country.")
    parser.add_argument("-l", "--location",
                        help="Look up weather for LOCATION and exit (no radio needed)")
    args = parser.parse_args()

    # --weather-channel-idx controls announcement channel only
    # --channel-idx controls message filtering (if set, only accept messages from that channel)
    # If neither is set, accept messages from all channels (default behavior)
    weather_idx = args.weather_channel_idx
    allowed_idx = args.channel_idx  # Only filter if explicitly set via --channel-idx

    bot = WeatherBot(port=args.port, baud=args.baud,
                     debug=args.debug, announce=args.announce,
                     allowed_channel_idx=allowed_idx,
                     weather_channel_idx=weather_idx,
                     country=args.country,
                     channel=args.channel)

    if args.location:
        print(bot._get_weather(args.location))
        return

    bot.run()


if __name__ == "__main__":
    main()
