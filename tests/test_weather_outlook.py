#!/usr/bin/env python3
"""
Test the weather outlook feature.
Verifies that the bot:
1. Sends initial weather response
2. Automatically sends outlook after weather response
3. Includes link at bottom of outlook message
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from unittest.mock import MagicMock, call, patch

from weather_bot import WeatherBot


def test_outlook_sent_automatically_after_weather():
    """Test that bot automatically sends outlook after weather response"""
    print("=" * 70)
    print("TEST: Outlook Automatically Sent After Weather Response")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()
    bot._ser.write = MagicMock()

    with patch("weather_bot.requests.get") as mock_get:
        # Mock geocoding response
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [
                {
                    "name": "London",
                    "country": "United Kingdom",
                    "country_code": "GB",
                    "latitude": 51.5074,
                    "longitude": -0.1278,
                }
            ]
        }

        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 14.5,
                "apparent_temperature": 12.8,
                "relative_humidity_2m": 75,
                "wind_speed_10m": 18.0,
                "wind_direction_10m": 230,
                "precipitation": 0.0,
                "weather_code": 2,
            }
        }

        # Mock outlook response
        outlook_response = MagicMock()
        outlook_response.json.return_value = {
            "daily": {
                "time": ["2026-02-25", "2026-02-26", "2026-02-27"],
                "temperature_2m_max": [15.0, 16.5, 14.0],
                "temperature_2m_min": [8.0, 9.5, 7.0],
                "weather_code": [2, 61, 3],
            }
        }

        mock_get.side_effect = [geocoding_response, weather_response, outlook_response]

        # Simulate receiving "wx London" from user on channel_idx 1
        bot._handle_channel_message("TestUser: wx London", 1)

        # Check that two messages were sent (weather + outlook)
        calls = bot._ser.write.call_args_list
        if len(calls) >= 2:
            print(f"✅ PASS: Bot sent {len(calls)} messages (weather + outlook)")

            # Verify the first message is weather
            first_msg = calls[0][0][0]
            if b"London" in first_msg and b"Temp:" in first_msg:
                print("✅ PASS: First message is weather response")
            else:
                print("❌ FAIL: First message doesn't look like weather")
                print(f"   Got: {first_msg}")
                return False

            # Verify the second message is outlook (not a prompt)
            second_msg = calls[1][0][0]
            if b"3-day" in second_msg and b"02-" in second_msg:
                print("✅ PASS: Second message is outlook (not prompt)")
            else:
                print("❌ FAIL: Second message doesn't look like outlook")
                print(f"   Got: {second_msg}")
                return False

            # Verify outlook contains link
            if b"https://mcwb.netlify.app" in second_msg:
                print("✅ PASS: Outlook includes link at bottom")
            else:
                print("❌ FAIL: Outlook missing link")
                print(f"   Got: {second_msg}")
                return False
        else:
            print(f"❌ FAIL: Expected 2 messages, got {len(calls)}")
            return False

        return True


def test_outlook_format():
    """Test the outlook response format is concise and includes link"""
    print("\n" + "=" * 70)
    print("TEST: Outlook Format is Concise with Link")
    print("=" * 70)

    bot = WeatherBot(debug=False)

    location_data = {"name": "York", "country_code": "GB", "latitude": 53.9599, "longitude": -1.0873}

    outlook_data = {
        "daily": {
            "time": ["2026-02-25", "2026-02-26", "2026-02-27"],
            "temperature_2m_max": [15.0, 16.5, 14.0],
            "temperature_2m_min": [8.0, 9.5, 7.0],
            "weather_code": [2, 61, 3],
        }
    }

    response = bot.format_outlook_response(location_data, outlook_data)
    print("\nOutlook response:")
    print(response)
    print()

    # Check that response is reasonably short
    if len(response) < 200:
        print(f"✅ PASS: Response is concise ({len(response)} characters)")
    else:
        print(f"⚠ WARNING: Response is long ({len(response)} characters)")
        print("   Consider making it shorter for MeshCore limits")

    # Check that it contains expected elements
    if "York" in response and "3-day" in response:
        print("✅ PASS: Response contains location and '3-day'")
    else:
        print("❌ FAIL: Response missing expected elements")
        return False

    # Check that dates are shortened
    if "02-25" in response or "02-26" in response:
        print("✅ PASS: Dates are shortened (MM-DD format)")
    else:
        print("❌ FAIL: Dates not in expected short format")
        return False

    # Check that link is included at bottom
    if "https://mcwb.netlify.app" in response:
        print("✅ PASS: Link included at bottom of outlook")
        # Verify it's at the end
        if response.strip().endswith("https://mcwb.netlify.app"):
            print("✅ PASS: Link is at the end of the message")
        else:
            print("⚠ WARNING: Link is not at the very end")
    else:
        print("❌ FAIL: Link not found in outlook")
        return False

    return True


def main():
    """Run all outlook tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "Weather Outlook Tests" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    tests = [
        test_outlook_sent_automatically_after_weather,
        test_outlook_format,
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
