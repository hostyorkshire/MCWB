#!/usr/bin/env python3
"""
Test the weather outlook feature.
Verifies that the bot:
1. Sends initial weather response
2. Prompts for outlook (y/n)
3. Handles yes/no responses correctly
4. Sends outlook when user responds with y/Y/yes/YES
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from weather_bot import WEATHER_EMOJIS
import time
from unittest.mock import MagicMock, call, patch

from weather_bot import WeatherBot


def test_outlook_prompt_after_weather():
    """Test that bot prompts for outlook after sending weather"""
    print("=" * 70)
    print("TEST: Outlook Prompt After Weather Response")
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

        mock_get.side_effect = [geocoding_response, weather_response]

        # Simulate receiving "wx London" from user on channel_idx 1
        bot._handle_channel_message("TestUser: wx London", 1)

        # Check that two messages were sent
        calls = bot._ser.write.call_args_list
        if len(calls) >= 2:
            print(f"✅ PASS: Bot sent {len(calls)} messages (weather + prompt)")

            # Verify the second message contains the outlook prompt
            second_msg = calls[1][0][0]
            if b"Would you like to see the outlook for" in second_msg:
                print("✅ PASS: Second message contains outlook prompt")
            else:
                print("❌ FAIL: Second message doesn't contain outlook prompt")
                print(f"   Got: {second_msg}")
                return False
        else:
            print(f"❌ FAIL: Expected 2 messages, got {len(calls)}")
            return False

        # Check that state was stored
        state_key = ("TestUser", 1)
        if state_key in bot._pending_outlook:
            print("✅ PASS: Pending outlook state stored")
        else:
            print("❌ FAIL: No pending outlook state")
            return False

        return True


def test_yes_response_sends_outlook():
    """Test that 'y' or 'yes' response sends the outlook"""
    print("\n" + "=" * 70)
    print("TEST: Yes Response Sends Outlook")
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

        mock_get.return_value = outlook_response

        # Test different yes variations
        for yes_response in ["y", "Y", "yes", "YES"]:
            print(f"\n  Testing response: '{yes_response}'")
            bot._pending_outlook[state_key] = {
                "location": "London",
                "country": None,
                "lat": 51.5074,
                "lon": -0.1278,
                "location_data": {"name": "London", "country_code": "GB", "latitude": 51.5074, "longitude": -0.1278},
                "timestamp": time.time(),
            }

            bot._ser.write.reset_mock()
            bot._handle_channel_message(f"TestUser: {yes_response}", 1)

            # Check that outlook was sent
            if bot._ser.write.called:
                msg = bot._ser.write.call_args[0][0]
                if b"London 3-day" in msg or b"02-" in msg:
                    print(f"    ✅ PASS: Outlook sent for '{yes_response}'")
                else:
                    print(f"    ❌ FAIL: Message doesn't look like outlook")
                    print(f"       Got: {msg}")
                    return False
            else:
                print(f"    ❌ FAIL: No message sent for '{yes_response}'")
                return False

            # Check that state was cleared
            if state_key not in bot._pending_outlook:
                print(f"    ✅ PASS: State cleared after '{yes_response}'")
            else:
                print(f"    ❌ FAIL: State not cleared")
                return False

    return True


def test_no_response_clears_state():
    """Test that 'n' or other responses clear the pending state and send OK message"""
    print("\n" + "=" * 70)
    print("TEST: No Response Clears State and Sends OK")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()
    bot._ser.write = MagicMock()

    # Set up pending outlook state
    state_key = ("TestUser", 1)
    bot._pending_outlook[state_key] = {
        "location": "London",
        "country": None,
        "lat": 51.5074,
        "lon": -0.1278,
        "location_data": {"name": "London", "country_code": "GB"},
        "timestamp": time.time(),
    }

    # Test 'n' response - should send OK message
    bot._ser.write.reset_mock()
    bot._handle_channel_message("TestUser: n", 1)

    if state_key not in bot._pending_outlook:
        print("✅ PASS: State cleared after 'n' response")
    else:
        print("❌ FAIL: State not cleared after 'n'")
        return False

    if bot._ser.write.called:
        msg = bot._ser.write.call_args[0][0]
        if b"Find out more about me and my commands at https://mcwb.netlify.app" in msg:
            print("✅ PASS: Response message sent after 'n' response")
        else:
            print("❌ FAIL: Response message not found in response")
            print(f"   Got: {msg}")
            return False
        msg_str = msg.decode("utf-8", errors="replace")
        if any(emoji in msg_str for emoji in WEATHER_EMOJIS):
            print("✅ PASS: Weather emoji included in response message")
        else:
            print("❌ FAIL: No weather emoji found in response message")
            print(f"   Got: {msg_str}")
            return False
    else:
        print("❌ FAIL: No message sent after 'n' response")
        return False

    # Test random text
    bot._pending_outlook[state_key] = {
        "location": "London",
        "country": None,
        "lat": 51.5074,
        "lon": -0.1278,
        "location_data": {"name": "London", "country_code": "GB"},
        "timestamp": time.time(),
    }

    bot._handle_channel_message("TestUser: maybe later", 1)

    if state_key not in bot._pending_outlook:
        print("✅ PASS: State cleared after other response")
    else:
        print("❌ FAIL: State not cleared after other text")
        return False

    return True


def test_timeout_cleanup():
    """Test that old outlook requests are cleaned up"""
    print("\n" + "=" * 70)
    print("TEST: Timeout Cleanup")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    bot._outlook_timeout = 2  # 2 second timeout for testing

    # Add a pending outlook request
    state_key = ("TestUser", 1)
    bot._pending_outlook[state_key] = {
        "location": "London",
        "country": None,
        "lat": 51.5074,
        "lon": -0.1278,
        "location_data": {"name": "London", "country_code": "GB"},
        "timestamp": time.time() - 3,  # 3 seconds ago (expired)
    }

    print(f"  Added expired outlook request (3 seconds old, timeout={bot._outlook_timeout}s)")

    # Trigger cleanup
    bot._cleanup_expired_outlook_requests()

    if state_key not in bot._pending_outlook:
        print("✅ PASS: Expired request cleaned up")
    else:
        print("❌ FAIL: Expired request not cleaned up")
        return False

    # Add a fresh request
    bot._pending_outlook[state_key] = {
        "location": "London",
        "country": None,
        "lat": 51.5074,
        "lon": -0.1278,
        "location_data": {"name": "London", "country_code": "GB"},
        "timestamp": time.time(),  # Fresh
    }

    print(f"  Added fresh outlook request")

    # Trigger cleanup
    bot._cleanup_expired_outlook_requests()

    if state_key in bot._pending_outlook:
        print("✅ PASS: Fresh request not cleaned up")
    else:
        print("❌ FAIL: Fresh request was incorrectly cleaned up")
        return False

    return True


def test_outlook_format():
    """Test the outlook response format is concise"""
    print("\n" + "=" * 70)
    print("TEST: Outlook Format is Concise")
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
    if len(response) < 150:
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

    return True


def main():
    """Run all outlook tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "Weather Outlook Tests" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    tests = [
        test_outlook_prompt_after_weather,
        test_yes_response_sends_outlook,
        test_no_response_clears_state,
        test_timeout_cleanup,
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
