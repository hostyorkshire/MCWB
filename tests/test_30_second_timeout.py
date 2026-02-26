#!/usr/bin/env python3
"""
Test the 30-second outlook timeout feature.
Verifies that:
1. Outlook requests expire after 30 seconds
2. Expired requests are automatically cleaned up
3. Other users can use the bot without interference from expired outlooks
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from unittest.mock import MagicMock, patch

from weather_bot import WeatherBot


def test_30_second_timeout():
    """Test that outlook requests expire after 30 seconds"""
    print("=" * 70)
    print("TEST: 30-Second Outlook Timeout")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    
    # Verify the timeout is set to 30 seconds
    if bot._outlook_timeout == 30:
        print(f"✅ PASS: Outlook timeout is set to 30 seconds")
    else:
        print(f"❌ FAIL: Outlook timeout is {bot._outlook_timeout}s, expected 30s")
        return False

    # Add a pending outlook request that's 31 seconds old (expired)
    state_key = ("TestUser", 1)
    bot._pending_outlook[state_key] = {
        "location": "London",
        "country": None,
        "lat": 51.5074,
        "lon": -0.1278,
        "location_data": {"name": "London", "country_code": "GB"},
        "timestamp": time.time() - 31,  # 31 seconds ago (expired)
    }

    print(f"  Added expired outlook request (31 seconds old)")

    # Trigger cleanup
    bot._cleanup_expired_outlook_requests()

    if state_key not in bot._pending_outlook:
        print("✅ PASS: Expired request (31s old) was cleaned up")
    else:
        print("❌ FAIL: Expired request was not cleaned up")
        return False

    # Add a fresh request (29 seconds old, not expired)
    bot._pending_outlook[state_key] = {
        "location": "London",
        "country": None,
        "lat": 51.5074,
        "lon": -0.1278,
        "location_data": {"name": "London", "country_code": "GB"},
        "timestamp": time.time() - 29,  # 29 seconds ago (still valid)
    }

    print(f"  Added fresh outlook request (29 seconds old)")

    # Trigger cleanup
    bot._cleanup_expired_outlook_requests()

    if state_key in bot._pending_outlook:
        print("✅ PASS: Fresh request (29s old) was not cleaned up")
    else:
        print("❌ FAIL: Fresh request was incorrectly cleaned up")
        return False

    return True


def test_cleanup_called_on_every_message():
    """Test that cleanup is called when processing any message"""
    print("\n" + "=" * 70)
    print("TEST: Cleanup Called On Every Message")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()
    bot._ser.write = MagicMock()

    # Add an expired outlook for UserA
    state_key_a = ("UserA", 1)
    bot._pending_outlook[state_key_a] = {
        "location": "London",
        "country": None,
        "lat": 51.5074,
        "lon": -0.1278,
        "location_data": {"name": "London", "country_code": "GB"},
        "timestamp": time.time() - 31,  # 31 seconds ago (expired)
    }

    print("  UserA has an expired outlook request (31s old)")

    # UserB sends a weather request
    print("  UserB sends: wx Paris")
    
    with patch("weather_bot.requests.get") as mock_get:
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
                "temperature_2m": 16.3,
                "apparent_temperature": 15.1,
                "relative_humidity_2m": 68,
                "wind_speed_10m": 12.0,
                "wind_direction_10m": 180,
                "precipitation": 0.0,
                "weather_code": 1,
            }
        }

        mock_get.side_effect = [geocoding_response, weather_response]
        bot._handle_channel_message("UserB: wx Paris", 1)

    # Verify UserA's expired outlook was cleaned up
    if state_key_a not in bot._pending_outlook:
        print("✅ PASS: UserA's expired outlook was cleaned up when UserB sent a message")
    else:
        print("❌ FAIL: UserA's expired outlook was not cleaned up")
        return False

    # Verify UserB got a new outlook prompt
    state_key_b = ("UserB", 1)
    if state_key_b in bot._pending_outlook:
        print("✅ PASS: UserB has a new pending outlook")
    else:
        print("❌ FAIL: UserB doesn't have a pending outlook")
        return False

    return True


def test_expired_outlook_doesnt_interfere():
    """Test that expired outlooks don't interfere with new users"""
    print("\n" + "=" * 70)
    print("TEST: Expired Outlook Doesn't Interfere With New Users")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()
    bot._ser.write = MagicMock()

    # UserA asks for weather but never responds
    print("  1. UserA asks: wx London")
    
    with patch("weather_bot.requests.get") as mock_get:
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

        mock_get.side_effect = [geocoding_response, weather_response]
        bot._handle_channel_message("UserA: wx London", 1)

    state_key_a = ("UserA", 1)
    if state_key_a in bot._pending_outlook:
        print("     UserA has pending outlook")
    
    # Manually expire UserA's request
    bot._pending_outlook[state_key_a]["timestamp"] = time.time() - 31

    # UserB asks for weather after 30+ seconds
    print("  2. After 30+ seconds, UserB asks: wx Paris")
    
    with patch("weather_bot.requests.get") as mock_get:
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
                "temperature_2m": 16.3,
                "apparent_temperature": 15.1,
                "relative_humidity_2m": 68,
                "wind_speed_10m": 12.0,
                "wind_direction_10m": 180,
                "precipitation": 0.0,
                "weather_code": 1,
            }
        }

        mock_get.side_effect = [geocoding_response, weather_response]
        bot._ser.write.reset_mock()
        bot._handle_channel_message("UserB: wx Paris", 1)

    # Verify UserB got Paris weather
    calls = bot._ser.write.call_args_list
    if len(calls) >= 2:
        first_msg = calls[0][0][0]
        if b"Paris" in first_msg and b"FR" in first_msg:
            print("✅ PASS: UserB received Paris weather")
        else:
            print("❌ FAIL: UserB didn't receive Paris weather")
            return False
    else:
        print("❌ FAIL: Expected 2 messages for UserB")
        return False

    # Verify UserA's expired outlook was cleaned up
    if state_key_a not in bot._pending_outlook:
        print("✅ PASS: UserA's expired outlook was automatically cleaned up")
    else:
        print("❌ FAIL: UserA's expired outlook still exists")
        return False

    return True


def test_timeout_boundary_cases():
    """Test timeout boundary cases (exactly 30 seconds)"""
    print("\n" + "=" * 70)
    print("TEST: Timeout Boundary Cases")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    
    # Test at exactly 30 seconds (should be expired)
    state_key = ("TestUser", 1)
    bot._pending_outlook[state_key] = {
        "location": "London",
        "country": None,
        "lat": 51.5074,
        "lon": -0.1278,
        "location_data": {"name": "London", "country_code": "GB"},
        "timestamp": time.time() - 30,  # Exactly 30 seconds ago
    }

    print("  Testing request at exactly 30 seconds old")
    bot._cleanup_expired_outlook_requests()

    if state_key not in bot._pending_outlook:
        print("✅ PASS: Request at exactly 30s is treated as expired")
    else:
        print("❌ FAIL: Request at exactly 30s should be expired")
        return False

    # Test at 29.9 seconds (should NOT be expired)
    bot._pending_outlook[state_key] = {
        "location": "London",
        "country": None,
        "lat": 51.5074,
        "lon": -0.1278,
        "location_data": {"name": "London", "country_code": "GB"},
        "timestamp": time.time() - 29.9,  # 29.9 seconds ago
    }

    print("  Testing request at 29.9 seconds old")
    bot._cleanup_expired_outlook_requests()

    if state_key in bot._pending_outlook:
        print("✅ PASS: Request at 29.9s is still valid")
    else:
        print("❌ FAIL: Request at 29.9s should still be valid")
        return False

    return True


def main():
    """Run all 30-second timeout tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "30-Second Timeout Tests" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    tests = [
        test_30_second_timeout,
        test_cleanup_called_on_every_message,
        test_expired_outlook_doesnt_interfere,
        test_timeout_boundary_cases,
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
