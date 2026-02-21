#!/usr/bin/env python3
"""
Simple test to verify country code shortening works correctly
"""
from unittest.mock import MagicMock, patch
from weather_bot import WeatherBot


def test_country_code_shortening():
    """Test that country codes are used instead of full country names"""
    print("=" * 70)
    print("TEST: Country Code Shortening")
    print("=" * 70)
    
    bot = WeatherBot(debug=False)
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response with both country and country_code
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "London",
                "country": "United Kingdom",
                "country_code": "GB",
                "latitude": 51.5074,
                "longitude": -0.1278
            }]
        }
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 14.2,
                "apparent_temperature": 12.8,
                "relative_humidity_2m": 72,
                "wind_speed_10m": 18.0,
                "wind_direction_10m": 230,
                "precipitation": 0.0,
                "weather_code": 2
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Get weather
        result = bot._get_weather("London")
        
        print("\nResult:")
        print(result)
        print()
        
        # Check that result uses country code (GB) not full name (United Kingdom)
        if "GB" in result:
            print("✅ PASS: Country code 'GB' found in output")
        else:
            print("❌ FAIL: Country code 'GB' not found in output")
            return False
            
        if "United Kingdom" in result:
            print("❌ FAIL: Full country name 'United Kingdom' found in output (should be code)")
            return False
        else:
            print("✅ PASS: Full country name not in output")
            
        # Check format
        if result.startswith("London, GB"):
            print("✅ PASS: Correct format 'London, GB'")
        else:
            print("❌ FAIL: Expected 'London, GB' at start of output")
            return False
            
        return True


def test_fallback_to_full_name():
    """Test fallback when country_code is not available"""
    print("\n" + "=" * 70)
    print("TEST: Fallback to Full Country Name")
    print("=" * 70)
    
    bot = WeatherBot(debug=False)
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response WITHOUT country_code
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "Paris",
                "country": "France",
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
                "weather_code": 1
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Get weather
        result = bot._get_weather("Paris")
        
        print("\nResult:")
        print(result)
        print()
        
        # Should fallback to full country name
        if "France" in result:
            print("✅ PASS: Falls back to full country name 'France' when code not available")
        else:
            print("❌ FAIL: Should use full country name when code not available")
            return False
            
        return True


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║          Country Code Shortening Tests                            ║")
    print("╚════════════════════════════════════════════════════════════════════╝\n")
    
    test1_passed = test_country_code_shortening()
    test2_passed = test_fallback_to_full_name()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if test1_passed and test2_passed:
        print("✅ All tests passed!")
        exit(0)
    else:
        print("❌ Some tests failed")
        exit(1)
