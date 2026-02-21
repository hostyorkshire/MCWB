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
_PUSH_SEND_CONFIRMED = 0x82 # Push: outgoing message ACK'd by mesh
_PUSH_MSG_WAITING = 0x83    # Push: new message queued
_PUSH_CHAN_MSG = 0x88        # Push: inline channel message (0x80 | RESP_CHANNEL_MSG)
_RESP_NO_MORE_MSGS = 0x0A   # No more messages in queue (same value as CMD_SYNC_NEXT_MSG)

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

    def __init__(self, port=None, baud=115200, debug=False, announce=False, allowed_channel_idx=None):
        self.port = port
        self.baud = baud
        self.debug = debug
        self.announce = announce
        self.allowed_channel_idx = allowed_channel_idx
        self._ser = None
        self._running = False
        # channel_idx used for periodic announcements (set on first received message)
        self._announce_channel_idx = 0

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def _log(self, msg):
        if self.debug:
            print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

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
            # code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) = 8 bytes; text follows
            channel_idx = payload[1]
            text = payload[8:].decode("utf-8", "ignore")
            self._handle_channel_message(text, channel_idx)
            self._send_cmd(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _RESP_CHANNEL_MSG and len(payload) >= 8:
            # code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) = 8 bytes; text follows
            channel_idx = payload[1]
            text = payload[8:].decode("utf-8", "ignore")
            self._handle_channel_message(text, channel_idx)
            self._send_cmd(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _RESP_CHANNEL_MSG_V3 and len(payload) >= 12:
            # code(1) + SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) = 11 bytes; text follows
            channel_idx = payload[4]
            text = payload[11:].decode("utf-8", "ignore")
            self._handle_channel_message(text, channel_idx)
            self._send_cmd(bytes([_CMD_SYNC_NEXT_MSG]))

        elif code == _RESP_NO_MORE_MSGS:
            pass  # queue empty – nothing to do

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

        # MeshCore prepends "SenderName: " to channel messages
        colon = text.find(": ")
        if colon > 0:
            sender = text[:colon]
            content = text[colon + 2:]
        else:
            sender = "unknown"
            content = text

        self._log(f"channel_idx={channel_idx} {sender}: {content}")

        # Remember this channel for periodic announcements
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

    # ------------------------------------------------------------------
    # Weather data
    # ------------------------------------------------------------------

    def _get_weather(self, location: str) -> str:
        """Fetch weather for *location* and return a formatted string."""
        try:
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1, "language": "en", "format": "json"},
                timeout=10,
            ).json()

            if "results" not in geo or not geo["results"]:
                return f"Location not found: {location}"

            r = geo["results"][0]
            name = r.get("name", location)
            country = r.get("country", "")
            lat, lon = r["latitude"], r["longitude"]

            wx = requests.get(
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

            c = wx.get("current", {})
            cond = WEATHER_CODES.get(c.get("weather_code", 0), f"Code {c.get('weather_code', 0)}")
            loc_str = f"{name}, {country}" if country else name

            return (
                f"{loc_str}\n"
                f"Conditions: {cond}\n"
                f"Temp: {c.get('temperature_2m', 'N/A')}°C "
                f"(feels like {c.get('apparent_temperature', 'N/A')}°C)\n"
                f"Humidity: {c.get('relative_humidity_2m', 'N/A')}%\n"
                f"Wind: {c.get('wind_speed_10m', 'N/A')} km/h "
                f"at {c.get('wind_direction_10m', 'N/A')}°\n"
                f"Precipitation: {c.get('precipitation', 'N/A')} mm"
            )
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

        if self.allowed_channel_idx is not None:
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
    parser.add_argument("-c", "--channel-idx", type=int,
                        help="Only respond to messages from this channel index (e.g., 1 for #weather)")
    parser.add_argument("-l", "--location",
                        help="Look up weather for LOCATION and exit (no radio needed)")
    args = parser.parse_args()

    bot = WeatherBot(port=args.port, baud=args.baud,
                     debug=args.debug, announce=args.announce,
                     allowed_channel_idx=args.channel_idx)

    if args.location:
        print(bot._get_weather(args.location))
        return

    bot.run()


if __name__ == "__main__":
    main()
