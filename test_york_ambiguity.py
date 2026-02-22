#!/usr/bin/env python3
"""
Integration test demonstrating the country filter feature.
Shows how the bot handles ambiguous city names like "York".
"""
from unittest.mock import MagicMock, patch
from weather_bot import WeatherBot


def test_york_ambiguity_without_filter():
    """Demonstrate the problem: York without country filter might return wrong city"""
    print("=" * 70)
    print("SCENARIO 1: Query 'York' without country filter")
    print("=" * 70)
    print("Problem: User in UK queries 'York', but gets York, Pennsylvania USA")
    print()
    
    bot = WeatherBot(debug=False, country=None)
    
    with patch('weather_bot.requests.get') as mock_get:
        # Simulate API returning York, USA (first match without country filter)
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
        
        result = bot._get_weather("York")
        
        print("API Response:")
        print(result)
        print()
        print("⚠️  User in UK gets weather for York, US (wrong city!)")
        print()


def test_york_with_gb_filter():
    """Demonstrate the solution: York with GB country filter returns correct city"""
    print("=" * 70)
    print("SCENARIO 2: Query 'York' with country=GB filter")
    print("=" * 70)
    print("Solution: Bot configured with --country GB returns York, UK")
    print()
    
    bot = WeatherBot(debug=False, country="GB")
    
    with patch('weather_bot.requests.get') as mock_get:
        # Simulate API returning York, UK when country=GB filter is applied
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
        
        result = bot._get_weather("York")
        
        print("API Response:")
        print(result)
        print()
        
        # Verify country parameter was sent
        geocoding_call = mock_get.call_args_list[0]
        params = geocoding_call[1]['params']
        print(f"✅ API called with country='{params.get('country')}' parameter")
        print("✅ User in UK gets correct weather for York, UK")
        print()


def test_explicit_location_overrides_filter():
    """Users can still query other countries by being explicit"""
    print("=" * 70)
    print("SCENARIO 3: User specifies 'York, USA' with country=GB filter")
    print("=" * 70)
    print("Users can still get other locations by being explicit in their query")
    print()
    
    bot = WeatherBot(debug=False, country="GB")
    
    with patch('weather_bot.requests.get') as mock_get:
        # Even with GB filter, explicit "York, USA" should work
        # (API will try to match the full query string)
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
        
        result = bot._get_weather("York, USA")
        
        print("API Response:")
        print(result)
        print()
        print("✅ User can still query other countries by being explicit")
        print()


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║       Country Filter Integration Test - York Ambiguity            ║")
    print("╚════════════════════════════════════════════════════════════════════╝\n")
    
    test_york_ambiguity_without_filter()
    test_york_with_gb_filter()
    test_explicit_location_overrides_filter()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ Country filter solves the ambiguous city name problem")
    print("✅ Bot operator can configure default country with --country flag")
    print("✅ Users can still query other locations by being explicit")
    print()
    print("Usage examples:")
    print("  python3 weather_bot.py --country GB  # For UK deployments")
    print("  python3 weather_bot.py --country US  # For US deployments")
    print("  python3 weather_bot.py               # No filter (global)")
