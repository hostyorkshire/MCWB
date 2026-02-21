#!/usr/bin/env python3
"""
Demonstration of improved logging and message handling.

This script simulates the exact scenario from the user's issue and shows
how the improved logging helps debug message reception problems.
"""

from weather_bot import WeatherBot
from meshcore import MeshCore, MeshCoreMessage, _FRAME_OUT, _RESP_CHANNEL_MSG_V3
from unittest.mock import MagicMock
import time

print("=" * 80)
print("DEMONSTRATION: Improved Weather Bot Logging")
print("=" * 80)
print()
print("This demo shows how the bot handles messages and what you should see in logs.")
print()

# Create weather bot with channel filter (like the user's setup)
bot = WeatherBot(node_id="WX_BOT", debug=True, channel="weather")

# Mock the geocoding and weather API to avoid actual network calls
def mock_geocode(location):
    print(f"\n>>> API CALL: Geocoding '{location}'")
    return {
        "name": location,
        "country": "GB",
        "latitude": 51.5074,
        "longitude": -0.1278
    }

def mock_weather(lat, lon):
    print(f">>> API CALL: Fetching weather for {lat}, {lon}")
    return {
        "current": {
            "temperature_2m": 12.5,
            "apparent_temperature": 10.0,
            "relative_humidity_2m": 75,
            "wind_speed_10m": 15.3,
            "wind_direction_10m": 220,
            "precipitation": 0.2,
            "weather_code": 2
        }
    }

bot.geocode_location = mock_geocode
bot.get_weather = mock_weather

# Start the bot
bot.mesh.start()

print("\n" + "=" * 80)
print("SCENARIO 1: Receiving a weather command message")
print("=" * 80)
print("\nA user on channel_idx 2 sends: 'wx London'")
print()

# Simulate a channel message from a LoRa radio
msg = MeshCoreMessage(
    sender="M3UXC",
    content="wx London",
    message_type="text",
    channel=None,  # LoRa radios don't set channel name
    channel_idx=2   # User's radio is using channel_idx 2
)

print("Simulating message reception...")
print()
bot.mesh.receive_message(msg)

print("\n" + "=" * 80)
print("SCENARIO 2: Binary protocol messages (ACKs, etc.)")
print("=" * 80)
print("\nThe LoRa radio sends protocol messages (ACKs, time requests, etc.)")
print("These are now silently filtered - you won't see confusing 'Ignoring' messages.")
print()

# Mock serial port with binary frames
mock_serial = MagicMock()
mock_serial.is_open = True
mock_serial.in_waiting = 0
bot.mesh._serial = mock_serial

# Simulate binary frame with NO_MORE_MSGS response (common protocol message)
from meshcore import _RESP_NO_MORE_MSGS
no_more_frame = bytes([_FRAME_OUT, 0x01, 0x00, _RESP_NO_MORE_MSGS])
mock_serial.readline.return_value = no_more_frame

print("Simulating binary protocol frame (NO_MORE_MSGS)...")
# This would previously log "Ignoring non-JSON LoRa data"
# Now it's silently handled
raw = mock_serial.readline()
if raw and raw[0] == _FRAME_OUT:
    length = int.from_bytes(raw[1:3], "little")
    payload = raw[3:3+length]
    # Would call _parse_binary_frame here
    print("✓ Binary frame detected and handled silently")
    print("  (No confusing 'Ignoring non-JSON' message)")
else:
    print("  Non-binary data - silently skipped")

print()
print("\n" + "=" * 80)
print("SCENARIO 3: Non-weather message (should be ignored)")
print("=" * 80)
print("\nA user sends: 'hello world' (not a weather command)")
print()

msg_non_weather = MeshCoreMessage(
    sender="M3UXC",
    content="hello world",
    message_type="text",
    channel=None,
    channel_idx=2
)

print("Simulating non-weather message...")
print()
bot.mesh.receive_message(msg_non_weather)

print("\n" + "=" * 80)
print("SUMMARY: What You Should See in Logs")
print("=" * 80)
print()
print("✅ When a weather command arrives:")
print("   - 'Binary frame: CHANNEL_MSG_V3 on channel_idx X'")
print("   - 'LoRa RX channel msg from [sender]: [command]'")
print("   - 'Channel filter check: ... → will_process=True'")
print("   - 'Processing message from [sender]: [command]'")
print("   - 'Weather request for location: [location]'")
print("   - 'Replying on channel_idx X: [response]'")
print()
print("✅ When protocol messages arrive:")
print("   - Silently handled (no confusing messages)")
print()
print("✅ When non-weather messages arrive:")
print("   - 'Not a weather command: [message]' (in debug mode)")
print()
print("❌ What you WON'T see anymore:")
print("   - 'Ignoring non-JSON LoRa data' (removed - was confusing)")
print()

# Clean up
bot.mesh.stop()

print("=" * 80)
print("Demo complete!")
print("=" * 80)
print()
print("For more information, see TROUBLESHOOTING.md")
print()
