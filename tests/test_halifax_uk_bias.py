#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

"""
Test to verify Halifax returns UK location by default (issue fix).
Tests that the bot biases to UK locations unless user explicitly specifies
a different country (e.g., "wx Halifax CA").
"""
from unittest.mock import MagicMock, patch

from weather_bot import WeatherBot


def test_halifax_defaults_to_uk():
    """Test that 'wx Halifax' returns Halifax, GB (UK) by default"""
    print("=" * 70)
    print("TEST: Halifax defaults to UK location")
    print("=" * 70)
    print("Issue: Bot should return Halifax, GB by default for UK users")
    print()

    # Bot with default country (should be GB)
    bot = WeatherBot(debug=False)
    
    # Verify the default
    assert bot.country == "GB", f"Expected default country GB, got {bot.country}"
    print(f"✅ Bot defaults to country=GB")
    print()

    with patch("weather_bot.requests.get") as mock_get:
        # Simulate API returning multiple Halifax locations
        # Halifax, CA might come first, but client-side filtering should select GB
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [
                {
                    "name": "Halifax",
                    "country": "Canada",
                    "country_code": "CA",
                    "latitude": 44.6488,
                    "longitude": -63.5752,
                },
                {
                    "name": "Halifax",
                    "country": "United Kingdom",
                    "country_code": "GB",
                    "latitude": 53.7252,
                    "longitude": -1.8579,
                },
            ]
        }

        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 8.5,
                "apparent_temperature": 6.2,
                "relative_humidity_2m": 82,
                "wind_speed_10m": 18.0,
                "wind_direction_10m": 270,
                "precipitation": 0.5,
                "weather_code": 61,
            }
        }

        mock_get.side_effect = [geocoding_response, weather_response]

        # Simple command without country specification
        result = bot._get_weather("Halifax")

        print("User command: 'wx Halifax'")
        print(f"Result:\n{result}")
        print()

        # Verify result contains Halifax, GB (not CA)
        if "Halifax" in result and "GB" in result:
            print("✅ PASS: Halifax defaults to UK location (Halifax, GB)")
            print("   User gets correct UK location without specifying country")
            return True
        else:
            print("❌ FAIL: Halifax didn't return GB location")
            print(f"   Expected 'Halifax, GB' in result")
            return False


def test_halifax_ca_explicit():
    """Test that 'wx Halifax CA' explicitly returns Halifax, Canada"""
    print("\n" + "=" * 70)
    print("TEST: Halifax CA explicit override")
    print("=" * 70)
    print("Users can still get Halifax, CA by being explicit")
    print()

    bot = WeatherBot(debug=False)

    with patch("weather_bot.requests.get") as mock_get:
        # Simulate API returning multiple Halifax locations
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [
                {
                    "name": "Halifax",
                    "country": "United Kingdom",
                    "country_code": "GB",
                    "latitude": 53.7252,
                    "longitude": -1.8579,
                },
                {
                    "name": "Halifax",
                    "country": "Canada",
                    "country_code": "CA",
                    "latitude": 44.6488,
                    "longitude": -63.5752,
                },
            ]
        }

        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": -5.2,
                "apparent_temperature": -12.5,
                "relative_humidity_2m": 78,
                "wind_speed_10m": 25.0,
                "wind_direction_10m": 320,
                "precipitation": 2.0,
                "weather_code": 71,
            }
        }

        mock_get.side_effect = [geocoding_response, weather_response]

        # Parse command with explicit CA
        location, country = bot._parse_command("wx Halifax CA")
        result = bot._get_weather(location, country)

        print("User command: 'wx Halifax CA'")
        print(f"Result:\n{result}")
        print()

        # Verify result contains Halifax, CA (overriding default GB)
        if "Halifax" in result and "CA" in result:
            print("✅ PASS: User can explicitly get Halifax, Canada")
            print("   Per-message country override works correctly")
            return True
        else:
            print("❌ FAIL: Halifax CA didn't return CA location")
            return False


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║          Halifax UK Bias Test (Issue Fix)                         ║")
    print("╚════════════════════════════════════════════════════════════════════╝\n")

    test1_passed = test_halifax_defaults_to_uk()
    test2_passed = test_halifax_ca_explicit()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("Issue: Bot returned Halifax, CA when UK users typed 'wx Halifax'")
    print("Solution: Bot now defaults to country=GB, returning Halifax, GB")
    print()
    if test1_passed and test2_passed:
        print("✅ All tests passed!")
        print("✅ Halifax now defaults to UK location")
        print("✅ Users can still get Halifax, CA with 'wx Halifax CA'")
        exit(0)
    else:
        print("❌ Some tests failed")
        exit(1)
