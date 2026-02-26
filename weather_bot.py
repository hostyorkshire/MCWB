#!/usr/bin/env python3
"""
MCWB - MeshCore Weather Bot
Lightweight weather bot for the MeshCore #weather channel.
Responds to: WX [location] or weather [location]
Uses the free Open-Meteo API (no API key required).
"""

import argparse
import os
import random
import re
import sys
import threading
import time
from pathlib import Path

from logging_config import get_weather_bot_logger, log_startup_info
from meshcore import MeshCore, MeshCoreMessage
from stats_tracker import StatsTracker

try:
    import requests
    from requests.exceptions import ConnectionError, RequestException, Timeout
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
_FRAME_OUT = 0x3E  # '>' radio→app frame start byte
_FRAME_IN = 0x3C  # '<' app→radio frame start byte
_CMD_APP_START = 0x01  # Initialise companion radio session
_CMD_GET_DEVICE_TIME = 0x05  # Radio requests current device time; app must respond
_CMD_SYNC_NEXT_MSG = 0x0A  # Request next queued message
_CMD_SEND_CHAN_MSG = 0x03  # Send a channel (flood) text message
_RESP_CURR_TIME = 0x09  # Response: current time (4-byte UNIX timestamp LE)
_RESP_CHANNEL_MSG = 0x08  # Channel message received
_RESP_CHANNEL_MSG_V3 = 0x11  # Channel message received (V3, includes SNR)
_RESP_CONTACT_MSG_V3 = 0x10  # Direct (contact) message received (V3, includes SNR)
_PUSH_BASE = 0x80  # Push: base flag for push notifications (bit 7 set)
_PUSH_SEND_CONFIRMED = 0x82  # Push: outgoing message ACK'd by mesh
_PUSH_MSG_WAITING = 0x83  # Push: new message queued
_PUSH_CHAN_MSG = 0x88  # Push: inline channel message (0x80 | RESP_CHANNEL_MSG)
_PUSH_NO_MORE_MSGS = 0x8A  # Push: no more messages (0x80 | CMD_SYNC_NEXT_MSG)
_PUSH_CONTACT_MSG_V3 = 0x90  # Push: inline contact message V3 (0x80 | RESP_CONTACT_MSG_V3)
_RESP_NO_MORE_MSGS = 0x0A  # No more messages in queue (same value as CMD_SYNC_NEXT_MSG)

# Channel message format constants
_OLD_FORMAT_HEADER_SIZE = 8  # code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4)
# code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4)
_V3_FORMAT_HEADER_SIZE = 11
_MIN_REALISTIC_SNR = 20  # Minimum typical SNR value for radio signals (dB)
_MAX_REALISTIC_SNR = 60  # Maximum typical SNR value for radio signals (dB)
_MAX_VALID_CHANNEL_IDX = 7  # Maximum valid channel index (0-7)

# Default sender name for messages without "SenderName: " prefix
# Matches meshcore.py's behavior in _dispatch_channel_message
_DEFAULT_SENDER = "channel"

# WMO weather interpretation codes
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers",
    81: "Moderate showers",
    82: "Violent showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm w/ slight hail",
    99: "Thunderstorm w/ heavy hail",
}

ANNOUNCE_INTERVAL = 3 * 60 * 60  # seconds between periodic announcements
ANNOUNCE_MESSAGE = (
    "Hello this is the WX BoT. To get a weather update simply type WX and your location. HELP? https://mcwb.netlify.app"
)
# Use absolute path for timestamp file to ensure it works regardless of working directory
ANNOUNCE_TIMESTAMP_FILE = Path(__file__).parent / "logs" / ".last_announce"

WEATHER_EMOJIS = [
    "☀️", "🌤️", "⛅", "🌥️", "☁️", "🌦️", "🌧️", "⛈️", "🌩️", "🌨️",
    "❄️", "🌪️", "🌫️", "🌈", "💨", "🌬️", "🌡️", "💧", "⛄", "☔",
    "🌊", "🌙", "⭐", "🌟", "🌂",
]


class WeatherBot:
    """Lightweight MeshCore weather bot."""

    def __init__(
        self,
        port=None,
        baud=115200,
        debug=False,
        announce=False,
        allowed_channel_idx=None,
        node_id=None,
        announce_channel=None,
        weather_channel_idx=None,
        country=None,
        channel=None,
        serial_port=None,
        baud_rate=None,
        verify_channels=False,
    ):
        # serial_port and baud_rate are aliases for port and baud
        self.port = serial_port or port
        self.baud = baud_rate or baud
        self.debug = debug
        self.announce = announce or (announce_channel is not None)
        self.allowed_channel_idx = allowed_channel_idx
        self._ser = None
        self._running = False
        # Set up logging
        self.logger, self.error_logger = get_weather_bot_logger(debug=debug)
        # channel_idx used for periodic announcements and weather responses
        # If weather_channel_idx is specified, use it; otherwise use first received message's channel
        self.weather_channel_idx = weather_channel_idx
        self._announce_channel_idx = weather_channel_idx if weather_channel_idx is not None else 0
        self.announce_channel = announce_channel
        # Country code for filtering geocoding results (e.g., "GB", "US", "FR")
        self.country = country
        # Channel verification mode - shows diagnostic info about encrypted messages
        self.verify_channels = verify_channels
        # Track channels with valid messages vs encrypted messages for diagnostics
        self._valid_channels = set()  # channel_idx with successfully decrypted messages
        self._encrypted_channels = set()  # channel_idx with encrypted/garbled messages
        # Parse comma-separated channel names (e.g. "weather,alerts") into a list.
        # Used for broadcasting responses and setting up channel name filtering via
        # the JSON-based MeshCore channel map rather than relying solely on
        # numeric channel_idx heuristics.
        if channel:
            self.channels = [ch.strip() for ch in channel.split(",") if ch.strip()]
        else:
            self.channels = []
        # Initialize stats tracker
        self.stats = StatsTracker()
        # State tracking for outlook feature
        # Maps (sender, channel_idx) -> (location, country, lat, lon, timestamp)
        self._pending_outlook = {}
        self._outlook_timeout = 30  # 30 seconds timeout for outlook requests
        # MeshCore integration for public message-handling API
        self.mesh = MeshCore(node_id=node_id or "MCWB", debug=debug, serial_port=self.port, baud_rate=self.baud)
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
        sanitized = "".join(char if (ord(char) >= 32 or char in "\n\t\r") else f"\\x{ord(char):02x}" for char in text)

        # Limit length to prevent log spam
        if len(sanitized) > self._MAX_LOG_LENGTH:
            sanitized = sanitized[: self._MAX_LOG_LENGTH] + f"... ({len(sanitized) - self._MAX_LOG_LENGTH} more chars)"

        return sanitized

    def _log(self, msg):
        """Log message to file"""
        self.logger.info(msg)

    # ------------------------------------------------------------------
    # Lifecycle helpers (mesh-level start/stop)
    # ------------------------------------------------------------------

    def start(self):
        """Start the MeshCore listener (mesh-level only)."""
        self.mesh.start()

    def stop(self):
        """Stop the MeshCore listener (mesh-level only)."""
        self.mesh.stop()

    def send_response(self, content: str, reply_to_channel: str = None, reply_to_channel_idx: int = None):
        """
        Send a weather response via the MeshCore mesh.

        If *reply_to_channel_idx* is given, the response is sent back on
        exactly that channel slot (the slot the query arrived on).
        Otherwise the response is broadcast to every channel in
        ``self.channels``.  When no channels are configured the message
        is sent without a channel identifier.
        """
        if reply_to_channel_idx is not None:
            self.mesh.send_message(content, "text", reply_to_channel, reply_to_channel_idx)
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
                p.device
                for p in list_ports.comports()
                if any(x in p.device for x in ("ttyUSB", "ttyACM", "ttyAMA", "COM"))
            ]
            if not candidates:
                msg = "No serial port found. Check USB connection and try --port."
                print(msg)
                self.logger.error(msg)
                return False
            port = candidates[0]
            msg = f"Auto-detected port: {port}"
            print(msg)
            self.logger.info(msg)

        try:
            self._ser = serial.Serial(port, self.baud, timeout=1, rtscts=False, dsrdtr=False)
            self._ser.rts = False
            self._ser.dtr = False
            # CMD_APP_START payload: code(1) + app_ver(1) + reserved(6 spaces) + app_name("MCWB")
            self._send_cmd(bytes([_CMD_APP_START, 0x03]) + b"      MCWB")
            time.sleep(0.1)
            msg = f"Connected to MeshCore on {port} at {self.baud} baud"
            print(msg)
            self.logger.info(msg)
            return True
        except serial.SerialException as e:
            msg = f"Failed to connect to {port}: {e}"
            print(msg)
            self.logger.error(msg)
            self.error_logger.error(msg)
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
        safe_text = self._sanitize_for_log(text)
        self._log(f"Sent on channel_idx={channel_idx}: {safe_text}")

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

    @staticmethod
    def _looks_like_valid_text(text: str) -> bool:
        """
        Simple check if decoded text looks like valid readable text.
        Uses the Jeff ping bot approach: just check if most characters are printable.
        Encrypted/garbled messages will have many non-printable or control characters.
        """
        if not text:
            return False
        # Count printable characters (space to ~, plus common whitespace)
        printable = sum(1 for c in text if 32 <= ord(c) <= 126 or c in "\n\t\r")
        # Require at least 70% printable - simpler than strict validation
        return (printable / len(text)) >= 0.70

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
        - After parsing, check if decoded text looks like valid readable text
        - Encrypted messages will have many non-printable/control characters
        - Uses simple printable character ratio check (Jeff ping bot approach)

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
            elif (
                reserved1 == 0x00
                and reserved2 == 0x00
                and snr_value > 0
                and 0 <= v3_channel_idx <= _MAX_VALID_CHANNEL_IDX
            ):
                use_v3_format = True

            # If any heuristic matched, parse as V3 format
            if use_v3_format:
                channel_idx = v3_channel_idx
                text_bytes = payload[_V3_FORMAT_HEADER_SIZE:]
                # Decode as UTF-8, ignoring invalid sequences, and strip whitespace
                text = text_bytes.decode("utf-8", "ignore").strip()
                # Check if text looks valid (not encrypted/garbled)
                # This uses the simple Jeff ping bot approach: just check printable ratio
                if not text or not self._looks_like_valid_text(text):
                    # Silently skip encrypted/garbled messages from channels without keys
                    # Track for diagnostics only if verification mode is enabled
                    if self.verify_channels and 0 <= channel_idx <= _MAX_VALID_CHANNEL_IDX:
                        self._encrypted_channels.add(channel_idx)
                        self._log(f"⚠️  Encrypted message on channel_idx={channel_idx}")
                    return (None, None)
                # Track successfully decrypted messages for diagnostics
                if self.verify_channels and 0 <= channel_idx <= _MAX_VALID_CHANNEL_IDX:
                    self._valid_channels.add(channel_idx)
                return (channel_idx, text)

        # Fall back to old format
        channel_idx = payload[1]
        # Validate channel_idx is in valid range (0-7)
        # Invalid indices indicate encrypted/garbled messages
        if not (0 <= channel_idx <= _MAX_VALID_CHANNEL_IDX):
            # Silently skip - this is expected for encrypted messages from other channels
            return (None, None)
        text_bytes = payload[_OLD_FORMAT_HEADER_SIZE:]
        # Decode as UTF-8, ignoring invalid sequences, and strip whitespace
        text = text_bytes.decode("utf-8", "ignore").strip()
        # Check if text looks valid (not encrypted/garbled)
        # This uses the simple Jeff ping bot approach: just check printable ratio
        if not text or not self._looks_like_valid_text(text):
            # Silently skip encrypted/garbled messages from channels without keys
            # Track for diagnostics only if verification mode is enabled
            if self.verify_channels:
                self._encrypted_channels.add(channel_idx)
                self._log(f"⚠️  Encrypted message on channel_idx={channel_idx}")
            return (None, None)
        # Track successfully decrypted messages for diagnostics
        if self.verify_channels:
            self._valid_channels.add(channel_idx)
        return (channel_idx, text)

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
            # code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) +
            # txt_type(1) + timestamp(4) = 11 bytes; text follows
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
        """Parse a raw channel message and respond if it is a weather command or outlook response."""
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
            content = text[colon + 2 :]
        else:
            # No "SenderName: " prefix found - treat as message from channel
            # This matches meshcore.py's behavior in _dispatch_channel_message
            sender = _DEFAULT_SENDER
            content = text
            safe_sender_for_log = self._sanitize_for_log(sender)
            self._log(
                f"channel_idx={channel_idx} message without SenderName: prefix, using sender='{safe_sender_for_log}'"
            )

        # Sanitize content for logging to prevent terminal corruption
        safe_sender = self._sanitize_for_log(sender)
        safe_content = self._sanitize_for_log(content)
        self._log(f"channel_idx={channel_idx} {safe_sender}: {safe_content}")

        # Remember this channel for periodic announcements (only if not explicitly configured)
        if self.weather_channel_idx is None:
            self._announce_channel_idx = channel_idx

        # Clean up expired outlook requests on every message
        self._cleanup_expired_outlook_requests()

        # Check if this is a weather command first (priority over outlook responses)
        location, country = self._parse_command(content)
        state_key = (sender, channel_idx)
        
        if location:
            # This is a new weather request - clear any pending outlook for this user
            if state_key in self._pending_outlook:
                del self._pending_outlook[state_key]
            # Sanitize sender for print output to prevent terminal corruption
            safe_sender_print = self._sanitize_for_log(sender)
            safe_location = self._sanitize_for_log(location)
            country_str = f" ({country})" if country else ""
            msg = f"WX request for '{safe_location}'{country_str} from {safe_sender_print}"
            print(msg, flush=True)
            self.logger.info(msg)

            # Get location data and weather
            try:
                r = self.geocode_location(location, country)
                if r is None:
                    response = f"Location not found: {location}"
                    self.logger.warning(response)
                    self.stats.record_error("location_not_found")
                    self._send_channel_msg(response, channel_idx)
                    return

                lat, lon = r["latitude"], r["longitude"]
                wx = self.get_weather(lat, lon)

                # Record successful request
                location_name = r.get("name", location)
                self.stats.record_request(location_name, user=sender)

                response = self.format_weather_response(r, wx)
                print(f"Response:\n{response}\n", flush=True)
                self.logger.info(f"Response: {response}")
                self._send_channel_msg(response, channel_idx)

                # Store state for potential outlook request and send prompt
                self._pending_outlook[state_key] = {
                    "location": location,
                    "country": country,
                    "lat": lat,
                    "lon": lon,
                    "location_data": r,
                    "timestamp": time.time(),
                }

                # Add delay to allow first message to be transmitted before sending prompt
                time.sleep(0.5)

                location_name = r.get("name", location)
                prompt = f"Would you like to see the outlook for {location_name}? (y/n)"
                self._send_channel_msg(prompt, channel_idx)

            except (ConnectionError, Timeout, RequestException) as e:
                # Handle network-related errors with user-friendly message
                response = "Sorry, I didn't get that due to network problems. But don't worry hit me with it again!"
                self.logger.error(f"Network error: {e}")
                self.error_logger.error(f"Network error: {e}", exc_info=True)
                self.stats.record_error("weather_api_error")
                self._send_channel_msg(response, channel_idx)
            except Exception as e:
                response = f"Weather error: {e}"
                self.logger.error(response)
                self.error_logger.error(response, exc_info=True)
                self.stats.record_error("weather_api_error")
                self._send_channel_msg(response, channel_idx)
        else:
            # Not a weather command - check if this is a yes/no response to a pending outlook request
            if state_key in self._pending_outlook:
                # Check if this request is still valid (after cleanup above)
                outlook_state = self._pending_outlook[state_key]
                if self._is_yes_response(content):
                    # User wants to see outlook
                    location_name = outlook_state["location"]
                    country = outlook_state["country"]
                    lat = outlook_state["lat"]
                    lon = outlook_state["lon"]
                    location_data = outlook_state["location_data"]

                    safe_location = self._sanitize_for_log(location_name)
                    msg = f"Outlook request for '{safe_location}' from {safe_sender}"
                    print(msg, flush=True)
                    self.logger.info(msg)

                    outlook_response = self._get_outlook(location_data, lat, lon)
                    print(f"Outlook Response:\n{outlook_response}\n", flush=True)
                    self.logger.info(f"Outlook Response: {outlook_response}")
                    self._send_channel_msg(outlook_response, channel_idx)

                    # Clear the pending state
                    del self._pending_outlook[state_key]
                    return
                else:
                    # User said no or something else, clear pending state and acknowledge
                    del self._pending_outlook[state_key]
                    emoji = random.choice(WEATHER_EMOJIS)
                    ok_msg = f"OK. Find out more about me and my commands at https://mcwb.netlify.app {emoji}"
                    self._send_channel_msg(ok_msg, channel_idx)
                    return

    @staticmethod
    def _parse_command(text: str):
        """Return (location, country) tuple if text matches WX/weather command, else (None, None).

        Supports formats:
        - "wx York" -> ("York", None)
        - "wx York UK" -> ("York", "GB")
        - "wx York USA" -> ("York", "US")
        - "wx York FR" -> ("York", "FR")
        - "wx York, UK" -> ("York, UK", None)  # Explicit format, no extraction
        """
        m = re.match(r"^(?:wx|weather)\s+(.+)$", text.strip(), re.IGNORECASE)
        if not m:
            return None, None

        location_str = m.group(1).strip()

        # Country code mappings (common variations that map to ISO codes)
        country_mappings = {
            "uk": "GB",
            "gb": "GB",
            "usa": "US",
            "us": "US",
            "united kingdom": "GB",
            "united states": "US",
        }

        # Try to extract country from end of location string
        # Pattern: location name followed by whitespace and country name/code
        # Only extract if there's no comma near the end (comma-separated format)
        words = location_str.split()
        if len(words) >= 2:
            # Check if last word could be a country code
            potential_country = words[-1].lower()

            # Check if there's a comma in the last few words (indicates comma-separated format)
            last_few_words = " ".join(words[-3:]) if len(words) >= 3 else " ".join(words)
            if "," in last_few_words:
                # Comma-separated format like "York, UK" - don't extract country
                return location_str, None

            # Map common country names to ISO codes, or use as-is if already valid
            if potential_country in country_mappings:
                country = country_mappings[potential_country]
                location = " ".join(words[:-1])
                return location, country
            elif len(potential_country) == 2:
                # Assume it's an ISO-3166-1 alpha-2 country code (2 letters)
                country = potential_country.upper()
                location = " ".join(words[:-1])
                return location, country

        return location_str, None

    @staticmethod
    def _is_yes_response(text: str) -> bool:
        """Check if the text is a yes response (y, Y, YES, yes)."""
        text = text.strip().lower()
        return text in ["y", "yes"]

    def _cleanup_expired_outlook_requests(self):
        """Remove outlook requests that have exceeded the timeout."""
        current_time = time.time()
        expired_keys = [
            key
            for key, state in self._pending_outlook.items()
            if current_time - state["timestamp"] > self._outlook_timeout
        ]
        for key in expired_keys:
            del self._pending_outlook[key]

    def _get_outlook(self, location_data: dict, lat: float, lon: float) -> str:
        """Fetch outlook for given coordinates and return a formatted string."""
        try:
            outlook = self.get_outlook(lat, lon)
            return self.format_outlook_response(location_data, outlook)
        except (ConnectionError, Timeout, RequestException) as e:
            msg = "Sorry, I couldn't fetch the outlook due to network problems."
            self.logger.error(f"Network error fetching outlook: {e}")
            self.error_logger.error(f"Network error fetching outlook: {e}", exc_info=True)
            self.stats.record_error("outlook_api_error")
            return msg
        except Exception as e:
            msg = f"Outlook error: {e}"
            self.logger.error(msg)
            self.error_logger.error(msg, exc_info=True)
            self.stats.record_error("outlook_api_error")
            return msg

    def parse_weather_command(self, text: str):
        """Public alias for _parse_command.

        Returns:
            tuple: (location, country) where country may be None
        """
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
            f"https://mcwb.netlify.app"
        )

    def handle_message(self, msg: MeshCoreMessage):
        """Handle a MeshCoreMessage and send a weather response via self.mesh."""
        location, country = self._parse_command(msg.content)
        if location:
            response = self._get_weather(location, country)
            # Reply on the exact channel slot the query arrived on (when known),
            # or broadcast to all configured channels.  Using send_response
            # keeps the routing logic in one place.
            self.send_response(response, reply_to_channel=msg.channel, reply_to_channel_idx=msg.channel_idx)

    def send_announcement(self):
        """Send the periodic announcement message to the configured announce channel."""
        if self.announce_channel is None:
            return
        self.mesh.send_message(ANNOUNCE_MESSAGE, "text", self.announce_channel)

    def _get_last_announce_time(self):
        """Read the last announcement timestamp from file. Returns 0 if file doesn't exist."""
        try:
            if ANNOUNCE_TIMESTAMP_FILE.exists():
                with open(ANNOUNCE_TIMESTAMP_FILE, "r") as f:
                    return float(f.read().strip())
        except (IOError, ValueError) as e:
            self._log(f"Could not read last announce time: {e}")
        return 0

    def _save_last_announce_time(self, timestamp):
        """Save the last announcement timestamp to file."""
        try:
            # Ensure logs directory exists
            ANNOUNCE_TIMESTAMP_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(ANNOUNCE_TIMESTAMP_FILE, "w") as f:
                f.write(str(timestamp))
                f.flush()  # Explicitly flush to ensure data is written
                os.fsync(f.fileno())  # Force write to disk
            self._log(f"Saved last announcement time to {ANNOUNCE_TIMESTAMP_FILE}")
        except IOError as e:
            self._log(f"Could not save last announce time: {e}")

    # ------------------------------------------------------------------
    # Weather data
    # ------------------------------------------------------------------

    def geocode_location(self, location: str, country_override: str = None):
        """Geocode *location* name via Open-Meteo.  Returns the first result
        dict (with ``latitude``, ``longitude``, ``name``, etc.) or ``None``.

        Args:
            location: City/location name to geocode
            country_override: Optional country code to filter results (e.g., "GB", "US").
                            Takes precedence over self.country if provided.
        """
        # Per-query country override takes precedence over bot's default country
        country = country_override if country_override is not None else self.country
        # Request multiple results so we can filter by country_code client-side.
        # The Open-Meteo geocoding API does not support a server-side country filter.
        count = 10 if country else 1
        geo_params = {"name": location, "count": count, "language": "en", "format": "json"}
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params=geo_params,
            timeout=10,
        ).json()
        if "results" not in geo or not geo["results"]:
            return None
        results = geo["results"]
        if country:
            filtered = [r for r in results if r.get("country_code", "").upper() == country.upper()]
            if filtered:
                return filtered[0]
        return results[0]

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

    def get_outlook(self, lat: float, lon: float) -> dict:
        """Fetch daily weather outlook for the given coordinates.  Returns the raw
        Open-Meteo response dict (with a ``"daily"`` key)."""
        return requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": ("temperature_2m_max,temperature_2m_min," "weather_code"),
                "timezone": "auto",
                "forecast_days": 3,
            },
            timeout=10,
        ).json()

    def format_outlook_response(self, location_data: dict, outlook_data: dict) -> str:
        """Format a concise outlook response from pre-fetched location and outlook data."""
        name = location_data.get("name", "Unknown")

        daily = outlook_data.get("daily", {})
        times = daily.get("time", [])
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        weather_codes = daily.get("weather_code", [])

        lines = [f"{name} 3-day:"]

        # Only show 3 days to keep message short
        for i in range(min(3, len(times))):
            date = times[i] if i < len(times) else "N/A"
            # Extract just month-day (e.g., "2026-02-25" -> "02-25")
            date_short = date[5:] if len(date) >= 10 else date
            tmax = temp_max[i] if i < len(temp_max) else "N/A"
            tmin = temp_min[i] if i < len(temp_min) else "N/A"
            wcode = weather_codes[i] if i < len(weather_codes) else 0

            # Use shorter weather descriptions
            condition_map = {
                0: "Clear",
                1: "Clear",
                2: "Cloudy",
                3: "Overcast",
                45: "Fog",
                48: "Fog",
                51: "Drizzle",
                53: "Drizzle",
                55: "Drizzle",
                61: "Rain",
                63: "Rain",
                65: "Rain",
                71: "Snow",
                73: "Snow",
                75: "Snow",
                80: "Showers",
                81: "Showers",
                82: "Showers",
                95: "Storm",
                96: "Storm+hail",
                99: "Storm+hail",
            }
            # Fallback chain: short map -> full WEATHER_CODES -> "C{code}" format
            condition = condition_map.get(wcode, WEATHER_CODES.get(wcode, f"C{wcode}"))

            lines.append(f"{date_short}: {condition} {tmin}-{tmax}°C")

        return "\n".join(lines)

    def _get_weather(self, location: str, country: str = None, user: str = None) -> str:
        """Fetch weather for *location* and return a formatted string.

        Args:
            location: City/location name to get weather for
            country: Optional country code to filter geocoding results (e.g., "GB", "US")
            user: Optional user/sender name for statistics tracking
        """
        try:
            r = self.geocode_location(location, country)
            if r is None:
                msg = f"Location not found: {location}"
                self.logger.warning(msg)
                self.stats.record_error("location_not_found")
                return msg
            lat, lon = r["latitude"], r["longitude"]
            wx = self.get_weather(lat, lon)

            # Record successful request
            location_name = r.get("name", location)
            self.stats.record_request(location_name, user=user)

            return self.format_weather_response(r, wx)
        except (ConnectionError, Timeout, RequestException) as e:
            # Handle network-related errors with user-friendly message
            msg = "Sorry, I didn't get that due to network problems. But don't worry hit me with it again!"
            self.logger.error(f"Network error: {e}")
            self.error_logger.error(f"Network error: {e}", exc_info=True)
            self.stats.record_error("weather_api_error")
            return msg
        except Exception as e:
            msg = f"Weather error: {e}"
            self.logger.error(msg)
            self.error_logger.error(msg, exc_info=True)
            self.stats.record_error("weather_api_error")
            return msg

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
        # Log startup information
        log_startup_info(self.logger, "MCWB Weather Bot", "2.0.0")

        if not self._connect():
            return

        self._running = True
        listener = threading.Thread(target=self._listen_loop, daemon=True, name="mcwb-listener")
        listener.start()

        # Drain any messages queued while the bot was offline
        self._send_cmd(bytes([_CMD_SYNC_NEXT_MSG]))

        # Give listener thread time to initialize and process sync response
        # This prevents race condition where announcement is sent before radio is ready
        time.sleep(0.5)

        if self.weather_channel_idx is not None:
            msg = f"MCWB running. Weather channel configured as channel_idx={self.weather_channel_idx}."
            print(msg)
            self.logger.info(msg)
            msg2 = f"Listening ONLY on channel_idx={self.weather_channel_idx}."
            print(msg2)
            self.logger.info(msg2)
            print("Send 'WX [location]' or 'weather [location]' on that channel.")
        elif self.allowed_channel_idx is not None:
            msg = f"MCWB running. Listening ONLY on channel_idx={self.allowed_channel_idx}."
            print(msg)
            self.logger.info(msg)
            print("Send 'WX [location]' or 'weather [location]' on that channel.")
        else:
            msg = "MCWB running. Send 'WX [location]' or 'weather [location]' on any channel."
            print(msg)
            self.logger.info(msg)

        if self.verify_channels:
            print("\n📡 Channel Verification Mode: Monitoring channel encryption status...")
            print("   Will report which channels are properly configured with decryption keys.\n")

        print("Press Ctrl+C to stop.\n", flush=True)

        # Announce on startup (always announce when bot starts with --announce flag)
        last_announce = self._get_last_announce_time()
        current_time = time.time()

        if last_announce > 0:
            hours_since = (current_time - last_announce) / 3600
            self._log(f"Last announcement was {hours_since:.2f} hours ago (file: {ANNOUNCE_TIMESTAMP_FILE})")
        else:
            self._log(f"No previous announcement found (file: {ANNOUNCE_TIMESTAMP_FILE})")

        # Always announce on startup to let users know the bot is operational
        if self.announce:
            self._send_channel_msg(ANNOUNCE_MESSAGE, self._announce_channel_idx)
            last_announce = current_time
            self._save_last_announce_time(last_announce)
            print("Sent startup announcement")
            self.logger.info("Sent startup announcement")

        try:
            while self._running:
                time.sleep(1)
                if self.announce and (time.time() - last_announce >= ANNOUNCE_INTERVAL):
                    self._send_channel_msg(ANNOUNCE_MESSAGE, self._announce_channel_idx)
                    last_announce = time.time()
                    self._save_last_announce_time(last_announce)
        except KeyboardInterrupt:
            msg = "Stopping..."
            print(f"\n{msg}")
            self.logger.info(msg)
        finally:
            self._running = False
            if self.verify_channels:
                self._print_channel_diagnostic()
            if self._ser:
                self._ser.close()
            msg = "MCWB stopped."
            print(msg)
            self.logger.info(msg)

    def _print_channel_diagnostic(self):
        """Print diagnostic summary of channel encryption status."""
        print("\n" + "=" * 70)
        print("📡 CHANNEL VERIFICATION REPORT")
        print("=" * 70)

        if self._valid_channels:
            print("\n✅ Channels with successfully decrypted messages:")
            for ch_idx in sorted(self._valid_channels):
                print(f"   • channel_idx {ch_idx} - Radio has valid keys for this channel")

        if self._encrypted_channels:
            print("\n⚠️  Channels with encrypted messages (could not decrypt):")
            for ch_idx in sorted(self._encrypted_channels):
                print(f"   • channel_idx {ch_idx} - Radio does not have keys for this channel")

            print("\n💡 WHAT THIS MEANS:")
            print("   The radio received messages on channels it's not subscribed to.")
            print("   This is normal! The bot automatically works on subscribed channels.")
            print()
            print("   If you need the bot to work on these encrypted channels:")
            print("   1. Join/subscribe to those channels in your MeshCore app")
            print("   2. Ensure the same channel is configured on all devices in your mesh")
            print("   3. The radio will then perform Diffie-Hellman key exchange")
            print("   4. Future messages on those channels will be automatically decrypted")
            print()
            print("   Note: The bot seamlessly works on any channels your radio is")
            print("         already subscribed to. No app configuration needed!")

        if not self._valid_channels and not self._encrypted_channels:
            print("\n📭 No messages received during this session.")
            print("   This is just a diagnostic tool. Try sending messages to test.")

        print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="MCWB – MeshCore Weather Bot for the #weather channel")
    parser.add_argument("-p", "--port", help="Serial port (e.g. /dev/ttyUSB0). Auto-detects if omitted.")
    parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument("-a", "--announce", action="store_true", help="Send periodic announcements every 3 hours")
    parser.add_argument(
        "--channel",
        help="Comma-separated list of MeshCore hashtag channel names to listen "
        "and respond on (e.g. 'weather' or 'weather,alerts'). "
        "Binary-protocol frames without a channel name are always accepted. "
        "When omitted the bot responds on any channel.",
    )
    parser.add_argument(
        "-c", "--channel-idx", type=int, help="Only respond to messages from this channel index (e.g., 1 for #weather)"
    )
    parser.add_argument(
        "-w",
        "--weather-channel-idx",
        type=int,
        help="Specify which channel index to use for announcements. "
        "Bot will still respond to messages from ANY channel "
        "unless --channel-idx is also specified.",
    )
    parser.add_argument(
        "--country",
        help="Default country code for geocoding (e.g., GB, US, FR). "
        "Filters location searches to prefer cities in this country.",
    )
    parser.add_argument(
        "--verify-channels",
        action="store_true",
        help="Enable channel verification mode. Shows diagnostic info about which "
        "channels are properly configured with decryption keys. Useful for "
        "troubleshooting when the radio receives encrypted messages it cannot decrypt.",
    )
    parser.add_argument("-l", "--location", help="Look up weather for LOCATION and exit (no radio needed)")
    args = parser.parse_args()

    # --weather-channel-idx controls announcement channel only
    # --channel-idx controls message filtering (if set, only accept messages from that channel)
    # If neither is set, accept messages from all channels (default behavior)
    weather_idx = args.weather_channel_idx
    allowed_idx = args.channel_idx  # Only filter if explicitly set via --channel-idx

    bot = WeatherBot(
        port=args.port,
        baud=args.baud,
        debug=args.debug,
        announce=args.announce,
        allowed_channel_idx=allowed_idx,
        weather_channel_idx=weather_idx,
        country=args.country,
        channel=args.channel,
        verify_channels=args.verify_channels,
    )

    if args.location:
        print(bot._get_weather(args.location))
        return

    bot.run()


if __name__ == "__main__":
    main()
