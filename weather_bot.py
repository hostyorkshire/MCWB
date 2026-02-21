#!/usr/bin/env python3
"""
MeshCore Weather Bot - UK Weather Bot for MeshCore mesh radio network
This bot responds to weather requests (wx [location]) with real-time weather data from Open-Meteo API.
"""

import sys
import re
import time
import argparse
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

from meshcore import MeshCore, MeshCoreMessage
from logging_config import get_weather_bot_logger, log_startup_info, log_exception


# Weather parameters to request from Open-Meteo API
WEATHER_PARAMETERS = "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m"

# Periodic announcement settings
ANNOUNCE_INTERVAL = 3 * 60 * 60  # 3 hours in seconds
ANNOUNCE_MESSAGE = "Hello this is the WX BoT. To get a weather update simply type WX and your location."

# WMO Weather codes mapping
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
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
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

# Country name to country code mapping
# Note: For United Kingdom, we use "UK" as it's more recognizable to users,
# even though the ISO 3166-1 alpha-2 code is "GB"
COUNTRY_CODES = {
    "United Kingdom": "UK",
    "Great Britain": "GB",
    "United States": "US",
    "United States of America": "US",
    "France": "FR",
    "Germany": "DE",
    "Spain": "ES",
    "Italy": "IT",
    "Netherlands": "NL",
    "Belgium": "BE",
    "Switzerland": "CH",
    "Austria": "AT",
    "Ireland": "IE",
    "Poland": "PL",
    "Czech Republic": "CZ",
    "Denmark": "DK",
    "Sweden": "SE",
    "Norway": "NO",
    "Finland": "FI",
    "Portugal": "PT",
    "Greece": "GR",
    "Canada": "CA",
    "Australia": "AU",
    "New Zealand": "NZ",
    "Japan": "JP",
    "China": "CN",
    "India": "IN",
    "Brazil": "BR",
    "Mexico": "MX",
    "Argentina": "AR",
    "South Africa": "ZA"
}


class WeatherBot:
    """Weather Bot for MeshCore network"""

    def __init__(self, node_id: str = "weather_bot", debug: bool = False,
                 serial_port: Optional[str] = None, baud_rate: int = 9600,
                 channel: Optional[str] = None,
                 announce_channel: Optional[str] = "wxtest"):
        """
        Initialize Weather Bot

        Args:
            node_id: Unique identifier for this bot node
            debug: Enable debug output
            serial_port: Serial port for LoRa module (e.g., /dev/ttyUSB0).
                         When None, the bot operates in simulation mode.
            baud_rate: Baud rate for LoRa serial connection (default: 9600)
            channel: Optional channel filter. When specified, the bot ONLY accepts
                    messages from these channels. Can be a single channel name or
                    comma-separated list (e.g., "weather" or "weather,alerts").
                    When None (default), accepts messages from ALL channels.
            announce_channel: Channel to broadcast periodic announcements on
                    (default: "wxtest"). Set to None to disable announcements.
        
        Note:
            - Without channel filter: Bot accepts queries from ALL channels
            - With channel filter: Bot ONLY accepts queries from specified channel(s)
            - Bot always replies on the same channel_idx where each query came from
        """
        self.mesh = MeshCore(node_id, debug=debug, serial_port=serial_port, baud_rate=baud_rate)
        self.debug = debug
        
        # Set up logging
        self.logger, self.error_logger = get_weather_bot_logger(debug=debug)

        # Open-Meteo API endpoints
        self.geocoding_api = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_api = "https://api.open-meteo.com/v1/forecast"

        # Configure channel filtering
        # Parse comma-separated channel names if provided
        if channel:
            self.channels = [ch.strip() for ch in channel.split(',') if ch.strip()]
            # Only set the channel filter if we have valid channels after parsing
            if self.channels:
                self.mesh.set_channel_filter(self.channels)
        else:
            self.channels = []
            # No channel filtering - accept messages from all channels

        # Announcement channel (None disables periodic announcements)
        self.announce_channel = announce_channel

        # Register message handler
        self.mesh.register_handler("text", self.handle_message)

    def log(self, message: str, level: str = "debug"):
        """
        Log messages to both console (if debug) and file.
        
        Args:
            message: Message to log
            level: Log level (debug, info, warning, error, critical)
        """
        # Also print to console if debug mode
        if self.debug:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] WeatherBot: {message}")
        
        # Log to file
        log_func = getattr(self.logger, level.lower(), self.logger.debug)
        log_func(message)

    def geocode_location(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Convert location name to coordinates using Open-Meteo Geocoding API

        Args:
            location: Location name (city, town)

        Returns:
            Dictionary with location data or None if not found
        """
        try:
            self.log(f"Geocoding location: {location}", "info")

            params = {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            }

            response = requests.get(self.geocoding_api, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                self.log(f"Found location: {result.get('name')}, {result.get('country')}", "info")
                return result
            else:
                self.log(f"Location not found: {location}", "warning")
                return None

        except requests.RequestException as e:
            msg = f"Geocoding error: {e}"
            self.log(msg, "error")
            log_exception(self.logger, self.error_logger, e, "Geocoding request failed")
            return None
        except Exception as e:
            msg = f"Unexpected error during geocoding: {e}"
            self.log(msg, "error")
            log_exception(self.logger, self.error_logger, e, "Geocoding unexpected error")
            return None

    def get_weather(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Get weather data from Open-Meteo API

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Dictionary with weather data or None if error
        """
        try:
            self.log(f"Fetching weather for coordinates: {latitude}, {longitude}", "info")

            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": WEATHER_PARAMETERS,
                "timezone": "Europe/London"
            }

            response = requests.get(self.weather_api, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            self.log("Weather data received successfully", "info")
            return data

        except requests.RequestException as e:
            msg = f"Weather API error: {e}"
            self.log(msg, "error")
            log_exception(self.logger, self.error_logger, e, "Weather API request failed")
            return None
        except Exception as e:
            msg = f"Unexpected error fetching weather: {e}"
            self.log(msg, "error")
            log_exception(self.logger, self.error_logger, e, "Weather fetch unexpected error")
            return None

    def get_weather_description(self, weather_code: int) -> str:
        """
        Convert WMO weather code to human-readable description

        Args:
            weather_code: WMO weather code

        Returns:
            Weather description string
        """
        return WEATHER_CODES.get(weather_code, f"Unknown (code: {weather_code})")

    def get_country_code(self, country: str) -> str:
        """
        Convert country name to country code

        Args:
            country: Country name (e.g., "United Kingdom", "GB", "UK")

        Returns:
            Country code (e.g., "UK", "GB", "US") - typically 2 characters
        """
        # If it's already a 2-letter code, return as is
        if len(country) == 2:
            return country
        
        # Look up in mapping, otherwise return original
        return COUNTRY_CODES.get(country, country)

    def format_weather_response(self, location_data: Dict[str, Any], weather_data: Dict[str, Any]) -> str:
        """
        Format weather data into a readable message

        Args:
            location_data: Location information from geocoding
            weather_data: Weather information from API

        Returns:
            Formatted weather message string
        """
        location_name = location_data.get("name", "Unknown")
        country = location_data.get("country", "")

        current = weather_data.get("current", {})

        temp = current.get("temperature_2m", "N/A")
        feels_like = current.get("apparent_temperature", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")
        wind_speed = current.get("wind_speed_10m", "N/A")
        wind_dir = current.get("wind_direction_10m", "N/A")
        precip = current.get("precipitation", "N/A")
        weather_code = current.get("weather_code", 0)

        condition = self.get_weather_description(weather_code)

        # Build response message with country code and shortened labels
        response = f"{location_name}"
        if country:
            country_code = self.get_country_code(country)
            response += f", {country_code}"
        response += "\n"
        response += f"Cond: {condition}\n"
        response += f"Temp: {temp}°C (feels {feels_like}°C)\n"
        response += f"Humid: {humidity}%\n"
        response += f"Wind: {wind_speed} km/h at {wind_dir}°\n"
        response += f"Precip: {precip} mm"

        return response

    def parse_weather_command(self, content: str) -> Optional[str]:
        """
        Parse weather command from message content

        Args:
            content: Message content

        Returns:
            Location string if valid weather command, None otherwise
        """
        # Match "wx" or "weather" followed by location
        # Case insensitive matching
        pattern = r'^(?:wx|weather)\s+(.+)$'
        match = re.match(pattern, content.strip(), re.IGNORECASE)

        if match:
            location = match.group(1).strip()
            return location

        return None

    def handle_message(self, message: MeshCoreMessage):
        """
        Handle incoming messages and respond to weather requests

        Args:
            message: MeshCoreMessage to process
        """
        self.log(f"Processing message from {message.sender}: {message.content}")

        # Parse weather command
        location = self.parse_weather_command(message.content)

        if location:
            self.log(f"Weather request for location: {location}")

            # Geocode location
            location_data = self.geocode_location(location)

            if not location_data:
                response = f"Sorry, I couldn't find the location: {location}"
                # Always reply on the channel where the message came from
                # This ensures the sender receives the reply regardless of their channel_idx mapping
                self.send_response(response, reply_to_channel=message.channel,
                                   reply_to_channel_idx=message.channel_idx)
                return

            # Get weather data
            latitude = location_data.get("latitude")
            longitude = location_data.get("longitude")

            weather_data = self.get_weather(latitude, longitude)

            if not weather_data:
                response = f"Sorry, I couldn't get weather data for {location}"
                # Always reply on the channel where the message came from
                # This ensures the sender receives the reply regardless of their channel_idx mapping
                self.send_response(response, reply_to_channel=message.channel,
                                   reply_to_channel_idx=message.channel_idx)
                return

            # Format and send response
            response = self.format_weather_response(location_data, weather_data)
            # Always reply on the channel where the message came from
            # This ensures the sender receives the reply regardless of their channel_idx mapping
            self.send_response(response, reply_to_channel=message.channel,
                               reply_to_channel_idx=message.channel_idx)
        else:
            self.log(f"Not a weather command: {message.content}")

    def _print_response(self, content: str, description: str):
        """Helper method to print response message with channel info"""
        print(f"\n{content}")
        print(f"[{description}]\n")

    def send_response(self, content: str, reply_to_channel: Optional[str] = None,
                      reply_to_channel_idx: Optional[int] = None):
        """
        Send a response message.

        When replying to a query, the bot replies on the same channel_idx where the
        message came from. For bot-initiated broadcasts (when no reply_to info is
        provided), the bot broadcasts to all its configured channel(s) or default channel.

        Args:
            content: Response message content
            reply_to_channel: Channel name to reply to (from incoming message)
            reply_to_channel_idx: Raw channel index to reply to (from incoming message)
        """
        # Priority 1: Reply using the raw channel_idx from the incoming message
        # This is the most reliable method and works regardless of channel name mappings
        if reply_to_channel_idx is not None:
            self.log(f"Replying on channel_idx {reply_to_channel_idx}: {content}")
            self.mesh.send_message(content, "text", channel=None, channel_idx=reply_to_channel_idx)
            self._print_response(content, f"Reply on channel_idx: {reply_to_channel_idx}")
        # Priority 2: Fallback to named channel
        elif reply_to_channel:
            self.log(f"Replying on channel '{reply_to_channel}': {content}")
            self.mesh.send_message(content, "text", reply_to_channel)
            self._print_response(content, f"Reply on channel: '{reply_to_channel}'")
        # Priority 3: Bot-initiated broadcast - send to all configured channels
        elif self.channels:
            # Bot has configured channel(s) - broadcast to all of them
            for channel in self.channels:
                self.log(f"Broadcasting on channel '{channel}': {content}")
                self.mesh.send_message(content, "text", channel)
            channels_str = ", ".join(f"'{ch}'" for ch in self.channels)
            self._print_response(content, f"Broadcast on channel(s): {channels_str}")
        # Priority 4: No channel info and no configured channels - use default channel
        else:
            self.log(f"Sending response on default channel: {content}")
            self.mesh.send_message(content, "text", None)
            self._print_response(content, "Reply on default channel")

    def send_announcement(self):
        """Send a periodic announcement to the announce channel"""
        if not self.announce_channel:
            return
        self.log(f"Sending announcement on channel '{self.announce_channel}'")
        self.mesh.send_message(ANNOUNCE_MESSAGE, "text", self.announce_channel)
        self._print_response(ANNOUNCE_MESSAGE, f"Announcement on channel: '{self.announce_channel}'")

    def start(self):
        """Start the weather bot"""
        log_startup_info(self.logger, "Weather Bot", "1.0.0")
        self.logger.info(f"Node ID: {self.mesh.node_id}")
        self.logger.info(f"Serial port: {self.mesh.serial_port or 'Simulation mode'}")
        self.logger.info(f"Baud rate: {self.mesh.baud_rate}")
        self.logger.info(f"Announce channel: {self.announce_channel or 'Disabled'}")
        if self.channels:
            self.logger.info(f"Channel filter: {', '.join(self.channels)}")
        else:
            self.logger.info("Channel filter: Disabled (accepts from all channels)")
        
        self.mesh.start()
        if self.channels:
            channel_str = ", ".join(self.channels)
            print(f"Weather Bot started. ONLY accepts queries from channel(s): {channel_str}")
            self.logger.info(f"Started with channel filter: {channel_str}")
        else:
            print("Weather Bot started. Accepts queries from ALL channels.")
            self.logger.info("Started - accepting queries from ALL channels")
        print("Send 'wx [location]' to get weather.")
        print("Example: wx London")
        print("Listening for messages...")
        print()
        print("NOTE: If using MeshCore companion radio hardware, ensure the device")
        print("      is properly configured and subscribed to the appropriate channels")
        print("      in the MeshCore app or firmware configuration.")

    def stop(self):
        """Stop the weather bot"""
        self.mesh.stop()
        print("Weather Bot stopped.")

    def run_interactive(self):
        """Run bot in interactive mode for testing"""
        self.start()

        try:
            while True:
                try:
                    user_input = input("\nEnter command (or 'quit' to exit): ")

                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break

                    if user_input.strip():
                        # Create a simulated message
                        msg = MeshCoreMessage(
                            sender="user",
                            content=user_input,
                            message_type="text"
                        )

                        # Process the message
                        self.handle_message(msg)

                except KeyboardInterrupt:
                    print("\nInterrupted by user")
                    break

        finally:
            self.stop()


def main():
    """Main entry point for weather bot"""
    parser = argparse.ArgumentParser(
        description="MeshCore Weather Bot - UK Weather via mesh radio network"
    )

    parser.add_argument(
        "-n", "--node-id",
        default="weather_bot",
        help="Node ID for this bot (default: weather_bot)"
    )

    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug output"
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode for testing"
    )

    parser.add_argument(
        "-p", "--port",
        help="Serial port for LoRa module (e.g., /dev/ttyUSB0). "
             "Use 'auto' to automatically detect available ports. "
             "When omitted the bot runs in simulation mode (no radio hardware required)."
    )

    parser.add_argument(
        "-b", "--baud",
        type=int,
        default=9600,
        help="Baud rate for LoRa serial connection (default: 9600)"
    )

    parser.add_argument(
        "-c", "--channel",
        help="Channel filter: only accept messages from specified channel(s). "
             "Can be a single channel (e.g., 'weather') or comma-separated list "
             "(e.g., 'weather,alerts'). When omitted, accepts messages from ALL channels."
    )

    parser.add_argument(
        "-a", "--announce-channel",
        default="wxtest",
        help="Channel to broadcast periodic announcements on every 3 hours "
             "(default: wxtest). Pass an empty string to disable announcements."
    )

    parser.add_argument(
        "-l", "--location",
        help="Get weather for a specific location and exit"
    )

    args = parser.parse_args()

    # Handle auto-detection of serial port
    serial_port = args.port
    if serial_port and serial_port.lower() == 'auto':
        from meshcore import find_serial_ports
        available_ports = find_serial_ports(debug=args.debug)
        if available_ports:
            serial_port = available_ports[0]
            print(f"Auto-detected serial port: {serial_port}")
        else:
            print("No serial ports found. Running in simulation mode.")
            serial_port = None

    # Create bot instance with optional channel filtering
    bot = WeatherBot(node_id=args.node_id, debug=args.debug,
                     serial_port=serial_port, baud_rate=args.baud,
                     channel=args.channel,
                     announce_channel=args.announce_channel or None)

    if args.location:
        # One-shot mode: get weather for location and exit
        bot.start()
        msg = MeshCoreMessage(
            sender="cli",
            content=f"wx {args.location}",
            message_type="text"
        )
        bot.handle_message(msg)
        bot.stop()
    elif args.interactive:
        # Interactive mode for testing
        bot.run_interactive()
    else:
        # Normal daemon mode
        bot.start()
        try:
            # Send initial announcement, then repeat every ANNOUNCE_INTERVAL seconds
            bot.send_announcement()
            last_announce = time.time()
            while bot.mesh.is_running():
                time.sleep(1)
                now = time.time()
                if now - last_announce >= ANNOUNCE_INTERVAL:
                    bot.send_announcement()
                    last_announce = now
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            bot.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
