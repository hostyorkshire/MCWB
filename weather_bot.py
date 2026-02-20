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


# Weather parameters to request from Open-Meteo API
WEATHER_PARAMETERS = "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m"

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


class WeatherBot:
    """Weather Bot for MeshCore network"""

    def __init__(self, node_id: str = "weather_bot", debug: bool = False,
                 channel: Optional[str] = None, serial_port: Optional[str] = None,
                 baud_rate: int = 9600):
        """
        Initialize Weather Bot

        Args:
            node_id: Unique identifier for this bot node
            debug: Enable debug output
            channel: Optional channel to broadcast responses on
            serial_port: Serial port for LoRa module (e.g., /dev/ttyUSB0).
                         When None, the bot operates in simulation mode.
            baud_rate: Baud rate for LoRa serial connection (default: 9600)
        """
        self.mesh = MeshCore(node_id, debug=debug, serial_port=serial_port, baud_rate=baud_rate)
        self.debug = debug
        self.channel = channel

        # Open-Meteo API endpoints
        self.geocoding_api = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_api = "https://api.open-meteo.com/v1/forecast"

        # Register message handler
        self.mesh.register_handler("text", self.handle_message)

    def log(self, message: str):
        """Log debug messages"""
        if self.debug:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] WeatherBot: {message}")

    def geocode_location(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Convert location name to coordinates using Open-Meteo Geocoding API

        Args:
            location: Location name (city, town)

        Returns:
            Dictionary with location data or None if not found
        """
        try:
            self.log(f"Geocoding location: {location}")

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
                self.log(f"Found location: {result.get('name')}, {result.get('country')}")
                return result
            else:
                self.log(f"Location not found: {location}")
                return None

        except requests.RequestException as e:
            self.log(f"Geocoding error: {e}")
            return None
        except Exception as e:
            self.log(f"Unexpected error during geocoding: {e}")
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
            self.log(f"Fetching weather for coordinates: {latitude}, {longitude}")

            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": WEATHER_PARAMETERS,
                "timezone": "Europe/London"
            }

            response = requests.get(self.weather_api, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            self.log("Weather data received successfully")
            return data

        except requests.RequestException as e:
            self.log(f"Weather API error: {e}")
            return None
        except Exception as e:
            self.log(f"Unexpected error fetching weather: {e}")
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

        # Build response message
        response = f"Weather for {location_name}"
        if country:
            response += f", {country}"
        response += "\n"
        response += f"Conditions: {condition}\n"
        response += f"Temp: {temp}°C (feels like {feels_like}°C)\n"
        response += f"Humidity: {humidity}%\n"
        response += f"Wind: {wind_speed} km/h at {wind_dir}°\n"
        response += f"Precipitation: {precip} mm"

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
                self.send_response(response)
                return

            # Get weather data
            latitude = location_data.get("latitude")
            longitude = location_data.get("longitude")

            weather_data = self.get_weather(latitude, longitude)

            if not weather_data:
                response = f"Sorry, I couldn't get weather data for {location}"
                self.send_response(response)
                return

            # Format and send response
            response = self.format_weather_response(location_data, weather_data)
            self.send_response(response)
        else:
            self.log(f"Not a weather command: {message.content}")

    def send_response(self, content: str):
        """
        Send a response message

        Args:
            content: Response message content
        """
        channel_info = f" on channel '{self.channel}'" if self.channel else ""
        self.log(f"Sending response{channel_info}: {content}")
        self.mesh.send_message(content, "text", self.channel)

        # Also print to console for visibility
        print(f"\n{content}\n")

    def start(self):
        """Start the weather bot"""
        self.mesh.start()
        print("Weather Bot started. Send 'wx [location]' to get weather.")
        print("Example: wx London")
        print("Listening for messages...")

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
        "-c", "--channel",
        help="Channel to broadcast responses on (optional)"
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
             "When omitted the bot runs in simulation mode (no radio hardware required)."
    )

    parser.add_argument(
        "-b", "--baud",
        type=int,
        default=9600,
        help="Baud rate for LoRa serial connection (default: 9600)"
    )

    parser.add_argument(
        "-l", "--location",
        help="Get weather for a specific location and exit"
    )

    args = parser.parse_args()

    # Create bot instance
    bot = WeatherBot(node_id=args.node_id, debug=args.debug, channel=args.channel,
                     serial_port=args.port, baud_rate=args.baud)

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
            # Keep running
            while bot.mesh.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            bot.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
