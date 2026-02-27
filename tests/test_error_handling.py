#!/usr/bin/env python3
"""
Test improved error handling for network issues.
Demonstrates better user-facing error messages when the weather service is unreachable.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import Mock, patch
import requests
from weather_bot import WeatherBot


def test_timeout_error():
    """Test that timeout errors provide helpful user messages."""
    print("=" * 70)
    print("TEST: Timeout Error Handling")
    print("=" * 70)
    print("Scenario: Geocoding service is slow and times out")
    print()

    bot = WeatherBot(debug=False, country=None)

    with patch('weather_bot.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout()
        result = bot._get_weather('York', 'UK')

    print(f"User sees: {result}")
    print()

    passed = True
    if "timeout" in result.lower() and "try again" in result.lower():
        print("✅ PASS: Clear timeout message with actionable advice")
    else:
        print("❌ FAIL: Message doesn't clearly indicate timeout")
        passed = False
    print()
    return passed


def test_connection_error():
    """Test that connection errors provide helpful user messages."""
    print("=" * 70)
    print("TEST: Connection Error Handling")
    print("=" * 70)
    print("Scenario: Cannot reach geocoding service (network down)")
    print()

    bot = WeatherBot(debug=False, country=None)

    with patch('weather_bot.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError()
        result = bot._get_weather('York', 'USA')

    print(f"User sees: {result}")
    print()

    passed = True
    if "connection" in result.lower() and "network" in result.lower():
        print("✅ PASS: Clear connection error message")
    else:
        print("❌ FAIL: Message doesn't clearly indicate connection issue")
        passed = False
    print()
    return passed


def test_http_error():
    """Test that HTTP errors (4xx, 5xx) provide helpful messages."""
    print("=" * 70)
    print("TEST: HTTP Error Handling")
    print("=" * 70)
    print("Scenario: Weather service returns HTTP 503 (Service Unavailable)")
    print()

    bot = WeatherBot(debug=False, country=None)

    with patch('weather_bot.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_response.status_code = 503
        mock_get.return_value = mock_response
        result = bot._get_weather('Paris', 'FR')

    print(f"User sees: {result}")
    print()

    passed = True
    if "error" in result.lower() or "service" in result.lower():
        print("✅ PASS: HTTP error communicated to user")
    else:
        print("❌ FAIL: HTTP error not clearly communicated")
        passed = False
    print()
    return passed


def test_location_not_found_with_country():
    """Test helpful message when location isn't found with country filter."""
    print("=" * 70)
    print("TEST: Location Not Found (with country)")
    print("=" * 70)
    print("Scenario: User searches for non-existent city in UK")
    print()

    bot = WeatherBot(debug=False, country=None)

    with patch('weather_bot.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {'results': []}
        mock_get.return_value = mock_response
        result = bot._get_weather('Fakeville', 'UK')

    print(f"User sees: {result}")
    print()

    passed = True
    if "not found" in result.lower() and "UK" in result:
        print("✅ PASS: Clear 'not found' message mentions the country")
    else:
        print("❌ FAIL: Message doesn't clearly indicate location wasn't found")
        passed = False

    if "try without" in result.lower() or "check spelling" in result.lower():
        print("✅ PASS: Message suggests helpful actions")
    else:
        print("❌ FAIL: Message doesn't suggest next steps")
        passed = False
    print()
    return passed


def test_location_not_found_without_country():
    """Test helpful message when location isn't found without country filter."""
    print("=" * 70)
    print("TEST: Location Not Found (without country)")
    print("=" * 70)
    print("Scenario: User searches for non-existent city globally")
    print()

    bot = WeatherBot(debug=False, country=None)

    with patch('weather_bot.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {'results': []}
        mock_get.return_value = mock_response
        result = bot._get_weather('Fakeville')

    print(f"User sees: {result}")
    print()

    passed = True
    if "not found" in result.lower():
        print("✅ PASS: Clear 'not found' message")
    else:
        print("❌ FAIL: Message doesn't clearly indicate location wasn't found")
        passed = False

    if "[country]" in result or "UK" in result or "USA" in result:
        print("✅ PASS: Message suggests trying with country code")
    else:
        print("❌ FAIL: Message doesn't suggest adding country code")
        passed = False
    print()
    return passed


def test_success_case_unchanged():
    """Verify successful weather lookups still work correctly."""
    print("=" * 70)
    print("TEST: Success Case (Regression Test)")
    print("=" * 70)
    print("Scenario: Normal successful weather lookup")
    print()

    bot = WeatherBot(debug=False, country=None)

    with patch('weather_bot.requests.get') as mock_get:
        geo_response = Mock()
        geo_response.raise_for_status = Mock()
        geo_response.json.return_value = {
            'results': [{
                'name': 'York',
                'country': 'United Kingdom',
                'country_code': 'GB',
                'latitude': 53.9599,
                'longitude': -1.0873
            }]
        }

        weather_response = Mock()
        weather_response.raise_for_status = Mock()
        weather_response.json.return_value = {
            'current': {
                'temperature_2m': 12.5,
                'apparent_temperature': 10.8,
                'relative_humidity_2m': 75,
                'wind_speed_10m': 15.0,
                'wind_direction_10m': 220,
                'precipitation': 0.0,
                'weather_code': 2
            }
        }

        mock_get.side_effect = [geo_response, weather_response]
        result = bot._get_weather('York', 'UK')

    print("User sees:")
    print(result)
    print()

    passed = True
    if "York, GB" in result and "Temp:" in result and "Wind:" in result:
        print("✅ PASS: Normal weather lookup still works correctly")
    else:
        print("❌ FAIL: Weather response format changed unexpectedly")
        passed = False
    print()
    return passed


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║       Improved Error Handling Tests                               ║")
    print("╚════════════════════════════════════════════════════════════════════╝\n")

    # Run all tests and track results
    results = []
    results.append(("Timeout Error", test_timeout_error()))
    results.append(("Connection Error", test_connection_error()))
    results.append(("HTTP Error", test_http_error()))
    results.append(("Location Not Found (with country)", test_location_not_found_with_country()))
    results.append(("Location Not Found (without country)", test_location_not_found_without_country()))
    results.append(("Success Case", test_success_case_unchanged()))

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    # Count passes and failures
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{len(results)} tests passed")

    if failed == 0:
        print("\n✅ All error handling tests passed successfully")
        print()
        print("Key improvements:")
        print("  • Timeout errors now show friendly '⏱️ Request timeout' message")
        print("  • Connection errors show '🌐 Connection error' with advice")
        print("  • Location not found messages suggest helpful next steps")
        print("  • HTTP errors are caught and handled gracefully")
        print("  • Success cases continue to work unchanged")
        sys.exit(0)
    else:
        print(f"\n❌ {failed} test(s) failed")
        sys.exit(1)
