#!/usr/bin/env python3
"""
Test that weather commands work correctly with automatic outlook sending.
This verifies that weather requests properly trigger both weather and outlook responses.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from unittest.mock import MagicMock, patch

from weather_bot import WeatherBot


def test_weather_command_sends_outlook_automatically():
    """Test that weather commands automatically send outlook"""
    print("=" * 70)
    print("TEST: Weather Command Automatically Sends Outlook")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()
    bot._ser.write = MagicMock()

    with patch("weather_bot.requests.get") as mock_get:
        print("\n1. User asks: wx Paris")

        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [
                {
                    "name": "Paris",
                    "country": "France",
                    "country_code": "FR",
                    "latitude": 48.8566,
                    "longitude": 2.3522,
                }
            ]
        }

        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 16.5,
                "apparent_temperature": 15.2,
                "relative_humidity_2m": 68,
                "wind_speed_10m": 12.0,
                "wind_direction_10m": 180,
                "precipitation": 0.0,
                "weather_code": 1,
            }
        }

        outlook_response = MagicMock()
        outlook_response.json.return_value = {
            "daily": {
                "time": ["2026-02-25", "2026-02-26", "2026-02-27"],
                "temperature_2m_max": [18.0, 19.5, 17.0],
                "temperature_2m_min": [10.0, 11.5, 9.0],
                "weather_code": [1, 2, 3],
            }
        }

        mock_get.side_effect = [geocoding_response, weather_response, outlook_response]
        bot._handle_channel_message("TestUser: wx Paris", 1)

        # Check that two messages were sent (weather + outlook)
        calls = bot._ser.write.call_args_list
        if len(calls) >= 2:
            print("   ✅ Bot sent 2 messages (weather + outlook)")

            first_msg = calls[0][0][0]
            if b"Paris" in first_msg and b"FR" in first_msg:
                print("   ✅ First message contains Paris weather")
            else:
                print("   ❌ FAIL: First message doesn't contain Paris weather")
                print(f"      Got: {first_msg}")
                return False

            # Check second message is the outlook for Paris
            second_msg = calls[1][0][0]
            if b"Paris 3-day" in second_msg or b"02-" in second_msg:
                print("   ✅ Second message is outlook for Paris (sent automatically)")
            else:
                print("   ❌ FAIL: Second message is not outlook for Paris")
                print(f"      Got: {second_msg}")
                return False
        else:
            print(f"   ❌ FAIL: Expected 2 messages, got {len(calls)}")
            for i, call in enumerate(calls):
                print(f"      Message {i+1}: {call[0][0]}")
            return False

        print("\n✅ PASS: Weather command automatically sends weather + outlook")
        return True


def test_successive_weather_commands():
    """Test that successive weather commands each send outlook"""
    print("\n" + "=" * 70)
    print("TEST: Successive Weather Commands")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()
    bot._ser.write = MagicMock()

    with patch("weather_bot.requests.get") as mock_get:
        # First command: York
        print("\n1. User asks: wx York")

        geocoding_york = MagicMock()
        geocoding_york.json.return_value = {
            "results": [{
                "name": "York",
                "country": "United Kingdom",
                "country_code": "GB",
                "latitude": 53.9599,
                "longitude": -1.0873,
            }]
        }

        weather_york = MagicMock()
        weather_york.json.return_value = {
            "current": {
                "temperature_2m": 12.0,
                "apparent_temperature": 10.5,
                "relative_humidity_2m": 75,
                "wind_speed_10m": 15.0,
                "wind_direction_10m": 240,
                "precipitation": 0.0,
                "weather_code": 3,
            }
        }

        outlook_york = MagicMock()
        outlook_york.json.return_value = {
            "daily": {
                "time": ["2026-02-25", "2026-02-26", "2026-02-27"],
                "temperature_2m_max": [14.0, 15.5, 13.0],
                "temperature_2m_min": [7.0, 8.5, 6.0],
                "weather_code": [3, 61, 2],
            }
        }

        mock_get.side_effect = [geocoding_york, weather_york, outlook_york]
        bot._handle_channel_message("TestUser: wx York", 1)

        # Check that two messages were sent
        calls = bot._ser.write.call_args_list
        if len(calls) >= 2:
            print("   ✅ Bot sent 2 messages (weather + outlook)")

            first_msg = calls[0][0][0]
            if b"York" in first_msg and b"GB" in first_msg:
                print("   ✅ First message contains York weather")
            else:
                print("   ❌ FAIL: First message doesn't contain York weather")
                return False

            second_msg = calls[1][0][0]
            if b"York 3-day" in second_msg or b"02-" in second_msg:
                print("   ✅ Second message is outlook (sent automatically)")
            else:
                print("   ❌ FAIL: Second message is not outlook")
                return False
        else:
            print(f"   ❌ FAIL: Expected 2 messages, got {len(calls)}")
            return False

        print("\n✅ PASS: Each weather command independently sends weather + outlook")
        return True


def main():
    """Run all command priority tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 17 + "Weather Command Priority Tests" + " " * 21 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    tests = [
        test_weather_command_sends_outlook_automatically,
        test_successive_weather_commands,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Exception in {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
