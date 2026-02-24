#!/usr/bin/env python3
"""
Test network error handling in weather bot.
Verifies that network errors return user-friendly messages.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch, MagicMock
import requests
from weather_bot import WeatherBot


def test_connection_error_handling():
    """Test that connection errors return user-friendly message"""
    print("=" * 60)
    print("TEST: Connection Error Handling")
    print("=" * 60)

    bot = WeatherBot(debug=False)

    # Test ConnectionError in geocode_location
    with patch('weather_bot.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError(
            "HTTPSConnectionPool(host='api.open-meteo.com', port=443): Max retries exceeded"
        )

        result = bot._get_weather("London")
        expected_msg = "Sorry, I didn't get that due to network problems. But don't worry hit me with it again!"

        assert result == expected_msg, f"Expected: {expected_msg}, Got: {result}"
        print(f"✓ ConnectionError returns user-friendly message")

    # Test Timeout in geocode_location
    with patch('weather_bot.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = bot._get_weather("Manchester")

        assert result == expected_msg, f"Expected: {expected_msg}, Got: {result}"
        print(f"✓ Timeout returns user-friendly message")

    # Test RequestException (general network error)
    with patch('weather_bot.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = bot._get_weather("Birmingham")

        assert result == expected_msg, f"Expected: {expected_msg}, Got: {result}"
        print(f"✓ RequestException returns user-friendly message")

    # Test that other exceptions still get logged properly
    with patch('weather_bot.requests.get') as mock_get:
        mock_get.side_effect = ValueError("Some other error")

        result = bot._get_weather("Leeds")

        # Other exceptions should still be caught and logged (not the network message)
        assert "Sorry, I didn't get that due to network problems" not in result
        assert "Weather error" in result or "error" in result.lower()
        print(f"✓ Non-network errors still get caught and logged")

    print()


def test_network_error_after_geocoding():
    """Test network error in weather fetch after successful geocoding"""
    print("=" * 60)
    print("TEST: Network Error After Geocoding")
    print("=" * 60)

    bot = WeatherBot(debug=False)

    # Mock successful geocoding but failed weather fetch
    with patch('weather_bot.requests.get') as mock_get:
        # First call (geocoding) succeeds
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{"name": "York", "country": "UK", "latitude": 53.9, "longitude": -1.1}]
        }

        # Second call (weather) fails
        mock_get.side_effect = [
            geocoding_response,
            requests.exceptions.ConnectionError("Network error")
        ]

        result = bot._get_weather("York")
        expected_msg = "Sorry, I didn't get that due to network problems. But don't worry hit me with it again!"

        assert result == expected_msg, f"Expected: {expected_msg}, Got: {result}"
        print(f"✓ Network error during weather fetch returns user-friendly message")

    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 8 + "Network Error Handling Tests" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_connection_error_handling()
        test_network_error_after_geocoding()

        print("=" * 60)
        print("All network error handling tests passed!")
        print("=" * 60)
        print()

        return 0

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
