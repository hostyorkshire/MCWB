#!/usr/bin/env python3
"""
Test script for country code conversion
"""

import sys
from weather_bot import WeatherBot


def test_country_code_conversion():
    """Test country name to code conversion"""
    print("=" * 60)
    print("TEST: Country Code Conversion")
    print("=" * 60)

    bot = WeatherBot(debug=False)

    test_cases = [
        ("United Kingdom", "UK"),
        ("Great Britain", "GB"),
        ("GB", "GB"),  # Already a code
        ("UK", "UK"),  # Already a code
        ("United States", "US"),
        ("United States of America", "US"),
        ("France", "FR"),
        ("Germany", "DE"),
        ("Spain", "ES"),
        ("Italy", "IT"),
        ("Canada", "CA"),
        ("Australia", "AU"),
        ("UnknownCountry", "UnknownCountry"),  # Not in mapping, return original
    ]

    all_passed = True
    for country_name, expected_code in test_cases:
        result = bot.get_country_code(country_name)
        status = "✓" if result == expected_code else "✗"
        if result != expected_code:
            all_passed = False
        print(f"{status} '{country_name}' -> '{result}' (expected: '{expected_code}')")

    print()
    return all_passed


def test_weather_formatting_with_country_codes():
    """Test weather response formatting with country codes"""
    print("=" * 60)
    print("TEST: Weather Response with Country Codes")
    print("=" * 60)

    bot = WeatherBot(debug=False)

    # Test with "United Kingdom"
    location_data = {
        "name": "Brighton",
        "country": "United Kingdom",
        "latitude": 50.82838,
        "longitude": -0.13947
    }

    weather_data = {
        "current": {
            "temperature_2m": 12.5,
            "apparent_temperature": 11.2,
            "relative_humidity_2m": 75,
            "wind_speed_10m": 15.3,
            "wind_direction_10m": 230,
            "precipitation": 0.0,
            "weather_code": 2
        }
    }

    response = bot.format_weather_response(location_data, weather_data)
    print("Test 1: United Kingdom -> UK")
    print(response)
    assert "Brighton, UK" in response, "Expected 'Brighton, UK' in response"
    print("✓ Correctly converted to UK\n")

    # Test with "GB" (already a code)
    location_data["country"] = "GB"
    response = bot.format_weather_response(location_data, weather_data)
    print("Test 2: GB -> GB (already a code)")
    print(response)
    assert "Brighton, GB" in response, "Expected 'Brighton, GB' in response"
    print("✓ Correctly kept as GB\n")

    # Test with "United States"
    location_data = {
        "name": "New York",
        "country": "United States",
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    response = bot.format_weather_response(location_data, weather_data)
    print("Test 3: United States -> US")
    print(response)
    assert "New York, US" in response, "Expected 'New York, US' in response"
    print("✓ Correctly converted to US\n")

    return True


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "Country Code Conversion Tests" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        passed1 = test_country_code_conversion()
        passed2 = test_weather_formatting_with_country_codes()

        print("=" * 60)
        if passed1 and passed2:
            print("✅ All country code conversion tests passed!")
        else:
            print("❌ Some tests failed!")
        print("=" * 60)
        print()

        return 0 if (passed1 and passed2) else 1

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
