#!/usr/bin/env python3
"""
Integration test: Complete weather outlook conversation flow.
This demonstrates the full user experience - weather followed by automatic outlook.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from unittest.mock import MagicMock, patch

from weather_bot import WeatherBot


def integration_test():
    """Full integration test of outlook feature"""
    print("=" * 70)
    print("INTEGRATION TEST: Complete Weather Outlook Flow")
    print("=" * 70)
    print()

    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()

    print("Simulating a complete user conversation:")
    print("-" * 70)

    with patch("weather_bot.requests.get") as mock_get:
        # ===== Step 1: Initial weather request =====
        print("\n[User on #weather channel]: wx York UK")
        print()

        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [
                {
                    "name": "York",
                    "country": "United Kingdom",
                    "country_code": "GB",
                    "latitude": 53.9599,
                    "longitude": -1.0873,
                }
            ]
        }

        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 11.2,
                "apparent_temperature": 9.5,
                "relative_humidity_2m": 78,
                "wind_speed_10m": 16.5,
                "wind_direction_10m": 240,
                "precipitation": 0.0,
                "weather_code": 3,
            }
        }

        outlook_response = MagicMock()
        outlook_response.json.return_value = {
            "daily": {
                "time": ["2026-02-25", "2026-02-26", "2026-02-27"],
                "temperature_2m_max": [15.0, 16.5, 14.0],
                "temperature_2m_min": [8.0, 9.5, 7.0],
                "weather_code": [3, 61, 2],
            }
        }

        mock_get.side_effect = [geocoding_response, weather_response, outlook_response]
        bot._handle_channel_message("UserNode123: wx York UK", 1)

        # Extract bot responses
        calls = bot._ser.write.call_args_list
        print("[WeatherBot responses]:")
        for i, call in enumerate(calls, 1):
            msg_bytes = call[0][0]
            try:
                text = msg_bytes[7:].decode("utf-8", "ignore")
                print(f"\n{i}. {text}")
            except Exception:
                pass

        print()
        print("=" * 70)
        print("✅ INTEGRATION TEST COMPLETE")
        print("=" * 70)
        print()

        # Verify messages
        if len(calls) >= 2:
            print("✅ Bot sent weather and outlook automatically")
            
            # Check second message is outlook
            second_msg = calls[1][0][0]
            if b"3-day" in second_msg and b"https://mcwb.netlify.app" in second_msg:
                print("✅ Outlook sent automatically with link")
            else:
                print("❌ Outlook not properly formatted")
                return False
        else:
            print(f"❌ Expected 2 messages, got {len(calls)}")
            return False

        return True


def test_character_limits():
    """Verify outlook messages fit within MeshCore limits"""
    print("\n" + "=" * 70)
    print("CHARACTER LIMIT VERIFICATION")
    print("=" * 70)
    print()

    bot = WeatherBot(debug=False)

    # Test with long city name
    location_data = {"name": "Birmingham", "country_code": "GB"}

    outlook_data = {
        "daily": {
            "time": ["2026-02-25", "2026-02-26", "2026-02-27"],
            "temperature_2m_max": [15.0, 16.5, 14.0],
            "temperature_2m_min": [8.0, 9.5, 7.0],
            "weather_code": [96, 99, 95],  # Longest condition names
        }
    }

    outlook = bot.format_outlook_response(location_data, outlook_data)
    print("Longest possible outlook message:")
    print(outlook)
    print()
    print(f"Length: {len(outlook)} characters")
    print()

    # LoRa typically supports 200-237 bytes per message
    if len(outlook) < 150:
        print(f"✅ PASS: Message fits comfortably in MeshCore limits ({len(outlook)} < 150)")
        return True
    elif len(outlook) < 200:
        print(f"⚠ WARNING: Message is getting close to limits ({len(outlook)} chars)")
        return True
    else:
        print(f"❌ FAIL: Message may be too long ({len(outlook)} chars)")
        return False


if __name__ == "__main__":
    success = True
    success = integration_test() and success
    success = test_character_limits() and success

    if success:
        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        sys.exit(1)
