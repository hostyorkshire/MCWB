#!/usr/bin/env python3
"""
Test to verify per-message country specification works correctly.
Tests that users can specify country in their weather command:
  - wx York UK
  - wx York USA
"""
from unittest.mock import MagicMock, patch
from weather_bot import WeatherBot


def test_parse_command_with_uk():
    """Test that 'wx York UK' parses correctly"""
    print("=" * 70)
    print("TEST: Parse Command with UK")
    print("=" * 70)
    
    bot = WeatherBot(debug=False)
    location, country = bot._parse_command("wx York UK")
    
    print(f"Input: 'wx York UK'")
    print(f"Parsed location: '{location}'")
    print(f"Parsed country: '{country}'")
    print()
    
    if location == "York" and country == "GB":
        print("✅ PASS: 'wx York UK' correctly parsed as location='York', country='GB'")
        return True
    else:
        print(f"❌ FAIL: Expected location='York', country='GB', got location='{location}', country='{country}'")
        return False


def test_parse_command_with_usa():
    """Test that 'wx York USA' parses correctly"""
    print("\n" + "=" * 70)
    print("TEST: Parse Command with USA")
    print("=" * 70)
    
    bot = WeatherBot(debug=False)
    location, country = bot._parse_command("wx York USA")
    
    print(f"Input: 'wx York USA'")
    print(f"Parsed location: '{location}'")
    print(f"Parsed country: '{country}'")
    print()
    
    if location == "York" and country == "US":
        print("✅ PASS: 'wx York USA' correctly parsed as location='York', country='US'")
        return True
    else:
        print(f"❌ FAIL: Expected location='York', country='US', got location='{location}', country='{country}'")
        return False


def test_parse_command_with_us():
    """Test that 'wx York US' parses correctly"""
    print("\n" + "=" * 70)
    print("TEST: Parse Command with US")
    print("=" * 70)
    
    bot = WeatherBot(debug=False)
    location, country = bot._parse_command("wx York US")
    
    print(f"Input: 'wx York US'")
    print(f"Parsed location: '{location}'")
    print(f"Parsed country: '{country}'")
    print()
    
    if location == "York" and country == "US":
        print("✅ PASS: 'wx York US' correctly parsed as location='York', country='US'")
        return True
    else:
        print(f"❌ FAIL: Expected location='York', country='US', got location='{location}', country='{country}'")
        return False


def test_parse_command_without_country():
    """Test that 'wx York' without country still works"""
    print("\n" + "=" * 70)
    print("TEST: Parse Command without Country")
    print("=" * 70)
    
    bot = WeatherBot(debug=False)
    location, country = bot._parse_command("wx York")
    
    print(f"Input: 'wx York'")
    print(f"Parsed location: '{location}'")
    print(f"Parsed country: '{country}'")
    print()
    
    if location == "York" and country is None:
        print("✅ PASS: 'wx York' correctly parsed as location='York', country=None")
        return True
    else:
        print(f"❌ FAIL: Expected location='York', country=None, got location='{location}', country='{country}'")
        return False


def test_parse_command_with_comma_format():
    """Test that 'wx York, UK' is not parsed for country (comma format preserved)"""
    print("\n" + "=" * 70)
    print("TEST: Parse Command with Comma Format")
    print("=" * 70)
    
    bot = WeatherBot(debug=False)
    location, country = bot._parse_command("wx York, UK")
    
    print(f"Input: 'wx York, UK'")
    print(f"Parsed location: '{location}'")
    print(f"Parsed country: '{country}'")
    print()
    
    # Comma format should preserve the full string and not extract country
    if location == "York, UK" and country is None:
        print("✅ PASS: 'wx York, UK' correctly preserved as location='York, UK', country=None")
        print("   (Geocoding API will handle comma-separated format)")
        return True
    else:
        print(f"❌ FAIL: Expected location='York, UK', country=None, got location='{location}', country='{country}'")
        return False


def test_weather_request_with_uk():
    """Test that weather request with UK country code works end-to-end"""
    print("\n" + "=" * 70)
    print("TEST: Weather Request with UK")
    print("=" * 70)
    
    bot = WeatherBot(debug=False, country=None)  # No default country
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response for York, UK
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "York",
                "country": "United Kingdom",
                "country_code": "GB",
                "latitude": 53.9599,
                "longitude": -1.0873
            }]
        }
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 12.5,
                "apparent_temperature": 10.8,
                "relative_humidity_2m": 75,
                "wind_speed_10m": 15.0,
                "wind_direction_10m": 220,
                "precipitation": 0.0,
                "weather_code": 2
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Simulate user command "wx York UK"
        location, country = bot._parse_command("wx York UK")
        result = bot._get_weather(location, country)
        
        print(f"User command: 'wx York UK'")
        print(f"Result:\n{result}")
        print()
        
        # Verify geocoding API was called with country=GB
        geocoding_call = mock_get.call_args_list[0]
        params = geocoding_call[1]['params']
        
        if 'country' in params and params['country'] == 'GB':
            print(f"✅ PASS: Geocoding API called with country='GB'")
        else:
            print(f"❌ FAIL: Expected country='GB' in API params, got {params}")
            return False
        
        # Verify result contains York, GB
        if "York" in result and "GB" in result:
            print("✅ PASS: Result contains York, GB")
            return True
        else:
            print("❌ FAIL: Result doesn't contain expected location")
            return False


def test_weather_request_with_usa():
    """Test that weather request with USA country code works end-to-end"""
    print("\n" + "=" * 70)
    print("TEST: Weather Request with USA")
    print("=" * 70)
    
    bot = WeatherBot(debug=False, country="GB")  # Default country is GB
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response for York, USA
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "York",
                "country": "United States",
                "country_code": "US",
                "latitude": 39.9626,
                "longitude": -76.7277
            }]
        }
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 22.5,
                "apparent_temperature": 21.2,
                "relative_humidity_2m": 60,
                "wind_speed_10m": 8.0,
                "wind_direction_10m": 180,
                "precipitation": 0.0,
                "weather_code": 0
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Simulate user command "wx York USA" (should override default country GB)
        location, country = bot._parse_command("wx York USA")
        result = bot._get_weather(location, country)
        
        print(f"Bot configured with default country='GB'")
        print(f"User command: 'wx York USA'")
        print(f"Result:\n{result}")
        print()
        
        # Verify geocoding API was called with country=US (override)
        geocoding_call = mock_get.call_args_list[0]
        params = geocoding_call[1]['params']
        
        if 'country' in params and params['country'] == 'US':
            print(f"✅ PASS: Geocoding API called with country='US' (overrode default GB)")
        else:
            print(f"❌ FAIL: Expected country='US' in API params, got {params}")
            return False
        
        # Verify result contains York, US
        if "York" in result and "US" in result:
            print("✅ PASS: Result contains York, US")
            return True
        else:
            print("❌ FAIL: Result doesn't contain expected location")
            return False


def test_case_insensitive_parsing():
    """Test that country parsing is case-insensitive"""
    print("\n" + "=" * 70)
    print("TEST: Case Insensitive Parsing")
    print("=" * 70)
    
    bot = WeatherBot(debug=False)
    
    test_cases = [
        ("wx York uk", "York", "GB"),
        ("wx York UK", "York", "GB"),
        ("wx York Uk", "York", "GB"),
        ("wx York usa", "York", "US"),
        ("wx York USA", "York", "US"),
        ("wx York UsA", "York", "US"),
    ]
    
    all_passed = True
    for input_cmd, expected_loc, expected_country in test_cases:
        location, country = bot._parse_command(input_cmd)
        if location == expected_loc and country == expected_country:
            print(f"✅ '{input_cmd}' -> location='{location}', country='{country}'")
        else:
            print(f"❌ '{input_cmd}' -> Expected location='{expected_loc}', country='{expected_country}', got location='{location}', country='{country}'")
            all_passed = False
    
    print()
    if all_passed:
        print("✅ PASS: All case variations parsed correctly")
        return True
    else:
        print("❌ FAIL: Some case variations failed")
        return False


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║       Per-Message Country Specification Tests                     ║")
    print("╚════════════════════════════════════════════════════════════════════╝\n")
    
    results = []
    results.append(("Parse UK", test_parse_command_with_uk()))
    results.append(("Parse USA", test_parse_command_with_usa()))
    results.append(("Parse US", test_parse_command_with_us()))
    results.append(("Parse without country", test_parse_command_without_country()))
    results.append(("Parse comma format", test_parse_command_with_comma_format()))
    results.append(("Weather with UK", test_weather_request_with_uk()))
    results.append(("Weather with USA override", test_weather_request_with_usa()))
    results.append(("Case insensitive", test_case_insensitive_parsing()))
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    print()
    if all_passed:
        print("✅ All tests passed!")
        exit(0)
    else:
        print("❌ Some tests failed")
        exit(1)
