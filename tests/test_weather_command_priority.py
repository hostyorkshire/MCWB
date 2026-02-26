#!/usr/bin/env python3
"""
Test that weather commands have priority over outlook responses.
This ensures that when a user asks for a new weather report while having
a pending outlook request, they get the weather report first (not treated
as a response to the outlook question).
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from unittest.mock import MagicMock, patch

from weather_bot import WeatherBot


def test_weather_command_overrides_pending_outlook():
    """Test that a new weather command gets priority over pending outlook"""
    print("=" * 70)
    print("TEST: Weather Command Overrides Pending Outlook")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()
    bot._ser.write = MagicMock()

    with patch("weather_bot.requests.get") as mock_get:
        # Step 1: User asks for London weather
        print("\n1. User asks: wx London")
        
        geocoding_response_london = MagicMock()
        geocoding_response_london.json.return_value = {
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

        weather_response_london = MagicMock()
        weather_response_london.json.return_value = {
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

        mock_get.side_effect = [geocoding_response_london, weather_response_london]
        bot._handle_channel_message("TestUser: wx London", 1)

        # Check that state was stored
        state_key = ("TestUser", 1)
        if state_key in bot._pending_outlook:
            print("   ✅ Pending outlook state stored for London")
        else:
            print("   ❌ FAIL: No pending outlook state")
            return False

        # Step 2: Before responding to outlook, user asks for Paris weather
        print("\n2. User asks: wx Paris (before responding to outlook prompt)")
        
        geocoding_response_paris = MagicMock()
        geocoding_response_paris.json.return_value = {
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

        weather_response_paris = MagicMock()
        weather_response_paris.json.return_value = {
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

        mock_get.side_effect = [geocoding_response_paris, weather_response_paris]
        bot._ser.write.reset_mock()
        bot._handle_channel_message("TestUser: wx Paris", 1)

        # Verify Paris weather was sent (not an "OK" message)
        calls = bot._ser.write.call_args_list
        if len(calls) >= 2:
            print("   ✅ Bot sent 2 messages (weather + prompt)")
            
            # Check first message contains Paris weather
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

        # Verify the pending outlook is now for Paris, not London
        if state_key in bot._pending_outlook:
            outlook_location = bot._pending_outlook[state_key]["location"]
            if outlook_location == "Paris":
                print("   ✅ Pending outlook updated to Paris")
            else:
                print(f"   ❌ FAIL: Pending outlook is for '{outlook_location}', expected 'Paris'")
                return False
        else:
            print("   ❌ FAIL: No pending outlook state")
            return False

        return True


def test_weather_command_with_no_pending_outlook():
    """Test that weather commands work normally when there's no pending outlook"""
    print("\n" + "=" * 70)
    print("TEST: Weather Command Works Without Pending Outlook")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()
    bot._ser.write = MagicMock()

    with patch("weather_bot.requests.get") as mock_get:
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

        mock_get.side_effect = [geocoding_response, weather_response]
        bot._handle_channel_message("TestUser: wx York", 1)

        calls = bot._ser.write.call_args_list
        if len(calls) >= 2:
            print("✅ PASS: Bot sent 2 messages (weather + outlook)")
            
            first_msg = calls[0][0][0]
            if b"York" in first_msg and b"GB" in first_msg:
                print("✅ PASS: First message contains York weather")
            else:
                print("❌ FAIL: First message doesn't contain York weather")
                return False
                
            second_msg = calls[1][0][0]
            if b"York 3-day" in second_msg or b"02-" in second_msg:
                print("✅ PASS: Second message is outlook (sent automatically)")
            else:
                print("❌ FAIL: Second message is not outlook")
                return False
        else:
            print(f"❌ FAIL: Expected 2 messages, got {len(calls)}")
            return False

        return True

def test_yes_response_still_works():
    """Test that 'yes' responses still trigger outlook after the fix"""
    print("\n" + "=" * 70)
    print("TEST: Yes Response Still Works After Fix")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()
    bot._ser.write = MagicMock()

    # Manually set up pending outlook state
    state_key = ("TestUser", 1)
    bot._pending_outlook[state_key] = {
        "location": "London",
        "country": None,
        "lat": 51.5074,
        "lon": -0.1278,
        "location_data": {"name": "London", "country_code": "GB", "latitude": 51.5074, "longitude": -0.1278},
        "timestamp": time.time(),
    }

    with patch("weather_bot.requests.get") as mock_get:
        outlook_response = MagicMock()
        outlook_response.json.return_value = {
            "daily": {
                "time": ["2026-02-25", "2026-02-26", "2026-02-27"],
                "temperature_2m_max": [15.0, 16.5, 14.0],
                "temperature_2m_min": [8.0, 9.5, 7.0],
                "weather_code": [2, 61, 3],
            }
        }

        mock_get.return_value = outlook_response
        bot._handle_channel_message("TestUser: y", 1)

        if bot._ser.write.called:
            msg = bot._ser.write.call_args[0][0]
            if b"London 3-day" in msg:
                print("✅ PASS: Outlook sent after 'y' response")
            else:
                print("❌ FAIL: Message doesn't look like outlook")
                print(f"   Got: {msg}")
                return False
        else:
            print("❌ FAIL: No message sent")
            return False

        if state_key not in bot._pending_outlook:
            print("✅ PASS: State cleared after outlook sent")
        else:
            print("❌ FAIL: State not cleared")
            return False

        return True


def main():
    """Run all priority tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 16 + "Weather Command Priority Tests" + " " * 22 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    tests = [
        test_weather_command_overrides_pending_outlook,
        test_weather_command_with_no_pending_outlook,
        test_yes_response_still_works,
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
