#!/usr/bin/env python3
"""
Test to verify country code filtering works correctly for geocoding.
Tests that the bot can filter location searches by country to avoid
returning cities from the wrong country.
"""
from unittest.mock import MagicMock, patch, call
from weather_bot import WeatherBot


def test_country_filter_applied():
    """Test that country code is passed to geocoding API when configured"""
    print("=" * 70)
    print("TEST: Country Filter Applied to API")
    print("=" * 70)
    
    bot = WeatherBot(debug=False, country="GB")
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response
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
                "weather_code": 1
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Get weather
        result = bot._get_weather("York")
        
        print("\nResult:")
        print(result)
        print()
        
        # Check that geocoding API was called with country parameter
        geocoding_call = mock_get.call_args_list[0]
        params = geocoding_call[1]['params']
        
        if 'country' in params and params['country'] == 'GB':
            print(f"✅ PASS: Country parameter 'GB' passed to geocoding API")
            print(f"   Full params: {params}")
        else:
            print(f"❌ FAIL: Country parameter not passed correctly")
            print(f"   Expected: country='GB' in params")
            print(f"   Got: {params}")
            return False
            
        # Verify result contains UK York
        if "York" in result and "GB" in result:
            print("✅ PASS: Result contains York, GB")
        else:
            print("❌ FAIL: Result doesn't contain expected location")
            return False
            
        return True


def test_no_country_filter_when_not_configured():
    """Test that country filter is not applied when not configured"""
    print("\n" + "=" * 70)
    print("TEST: No Country Filter When Not Configured")
    print("=" * 70)
    
    bot = WeatherBot(debug=False, country=None)
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "Paris",
                "country": "France",
                "country_code": "FR",
                "latitude": 48.8566,
                "longitude": 2.3522
            }]
        }
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 16.5,
                "apparent_temperature": 15.2,
                "relative_humidity_2m": 68,
                "wind_speed_10m": 12.0,
                "wind_direction_10m": 180,
                "precipitation": 0.0,
                "weather_code": 2
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Get weather
        result = bot._get_weather("Paris")
        
        print("\nResult:")
        print(result)
        print()
        
        # Check that geocoding API was called WITHOUT country parameter
        geocoding_call = mock_get.call_args_list[0]
        params = geocoding_call[1]['params']
        
        if 'country' not in params:
            print(f"✅ PASS: Country parameter not included when not configured")
            print(f"   Full params: {params}")
        else:
            print(f"❌ FAIL: Country parameter included when it shouldn't be")
            print(f"   Got: {params}")
            return False
            
        return True


def test_country_filter_with_us():
    """Test that US country filter works correctly"""
    print("\n" + "=" * 70)
    print("TEST: US Country Filter")
    print("=" * 70)
    
    bot = WeatherBot(debug=False, country="US")
    
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
                "temperature_2m": 18.3,
                "apparent_temperature": 17.1,
                "relative_humidity_2m": 65,
                "wind_speed_10m": 10.0,
                "wind_direction_10m": 180,
                "precipitation": 0.0,
                "weather_code": 0
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Get weather
        result = bot._get_weather("York")
        
        print("\nResult:")
        print(result)
        print()
        
        # Check that geocoding API was called with US country parameter
        geocoding_call = mock_get.call_args_list[0]
        params = geocoding_call[1]['params']
        
        if 'country' in params and params['country'] == 'US':
            print(f"✅ PASS: Country parameter 'US' passed to geocoding API")
            print(f"   Full params: {params}")
        else:
            print(f"❌ FAIL: Country parameter not passed correctly")
            return False
            
        # Verify result contains US York
        if "York" in result and "US" in result:
            print("✅ PASS: Result contains York, US")
        else:
            print("❌ FAIL: Result doesn't contain expected location")
            return False
            
        return True


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║          Country Code Filtering Tests                             ║")
    print("╚════════════════════════════════════════════════════════════════════╝\n")
    
    test1_passed = test_country_filter_applied()
    test2_passed = test_no_country_filter_when_not_configured()
    test3_passed = test_country_filter_with_us()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if test1_passed and test2_passed and test3_passed:
        print("✅ All tests passed!")
        exit(0)
    else:
        print("❌ Some tests failed")
        exit(1)
