#!/usr/bin/env python3
"""
Test script for shortened field labels (Step 2)
Validates that labels are shortened correctly to save characters
"""

import sys
from weather_bot import WeatherBot


def test_label_shortening():
    """Test that labels are shortened correctly"""
    print("=" * 60)
    print("TEST: Label Shortening")
    print("=" * 60)

    bot = WeatherBot(debug=False)

    # Mock location and weather data
    location_data = {
        "name": "Manchester",
        "country": "United Kingdom",
        "latitude": 53.48,
        "longitude": -2.24
    }

    weather_data = {
        "current": {
            "temperature_2m": 15.8,
            "apparent_temperature": 14.3,
            "relative_humidity_2m": 68,
            "wind_speed_10m": 18.2,
            "wind_direction_10m": 270,
            "precipitation": 1.5,
            "weather_code": 61
        }
    }

    response = bot.format_weather_response(location_data, weather_data)
    
    print("\nGenerated response:")
    print("-" * 60)
    print(response)
    print("-" * 60)
    print()
    
    # Verify shortened labels are present
    required_labels = ["Cond:", "Temp:", "feels ", "Humid:", "Wind:", "Precip:"]
    old_labels = ["Conditions:", "feels like", "Humidity:", "Precipitation:"]
    
    all_passed = True
    
    print("Checking for shortened labels:")
    for label in required_labels:
        if label in response:
            print(f"  ✓ '{label}' found")
        else:
            print(f"  ✗ '{label}' NOT found")
            all_passed = False
    
    print()
    print("Checking old labels are NOT present:")
    for label in old_labels:
        if label not in response:
            print(f"  ✓ '{label}' correctly replaced")
        else:
            print(f"  ✗ '{label}' still present (should be shortened)")
            all_passed = False
    
    print()
    return all_passed


def test_character_savings():
    """Test and demonstrate character savings from label shortening"""
    print("=" * 60)
    print("TEST: Character Savings Calculation")
    print("=" * 60)

    bot = WeatherBot(debug=False)

    location_data = {
        "name": "London",
        "country": "GB",
        "latitude": 51.5074,
        "longitude": -0.1278
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

    # Current format (with shortened labels)
    response = bot.format_weather_response(location_data, weather_data)
    
    # Calculate what the old format would have been
    # Old format had: "Conditions:", "feels like", "Humidity:", "Precipitation:"
    # New format has: "Cond:", "feels", "Humid:", "Precip:"
    
    label_savings = {
        "Conditions -> Cond": 6,
        "feels like -> feels": 5,
        "Humidity -> Humid": 3,
        "Precipitation -> Precip": 7,
    }
    
    print()
    print("Character savings per label:")
    print("-" * 60)
    
    total_saved = 0
    for change, saved in label_savings.items():
        print(f"  {change}: {saved} chars")
        total_saved += saved
    
    print("-" * 60)
    print(f"  TOTAL SAVED: {total_saved} characters per report")
    print()
    
    print(f"Current response length: {len(response)} characters")
    estimated_old_length = len(response) + total_saved
    print(f"Old response length would be: {estimated_old_length} characters")
    print(f"Savings: {total_saved} characters ({(total_saved/estimated_old_length)*100:.1f}% reduction)")
    print()
    
    return True


def test_multiple_scenarios():
    """Test label shortening with various weather conditions"""
    print("=" * 60)
    print("TEST: Multiple Weather Scenarios")
    print("=" * 60)
    print()

    bot = WeatherBot(debug=False)

    scenarios = [
        {
            "name": "Brighton, UK - Rainy",
            "location": {"name": "Brighton", "country": "UK"},
            "weather": {
                "current": {
                    "temperature_2m": 9.5,
                    "apparent_temperature": 7.2,
                    "relative_humidity_2m": 82,
                    "wind_speed_10m": 12.4,
                    "wind_direction_10m": 245,
                    "precipitation": 3.2,
                    "weather_code": 63
                }
            }
        },
        {
            "name": "York, UK - Clear",
            "location": {"name": "York", "country": "UK"},
            "weather": {
                "current": {
                    "temperature_2m": 18.0,
                    "apparent_temperature": 17.5,
                    "relative_humidity_2m": 55,
                    "wind_speed_10m": 8.1,
                    "wind_direction_10m": 90,
                    "precipitation": 0.0,
                    "weather_code": 0
                }
            }
        },
    ]

    all_passed = True
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print("-" * 60)
        response = bot.format_weather_response(scenario['location'], scenario['weather'])
        print(response)
        
        # Verify shortened labels
        if "Cond:" in response and "Humid:" in response and "Precip:" in response and "feels " in response:
            print("✓ All shortened labels present")
        else:
            print("✗ Some labels missing or not shortened")
            all_passed = False
        
        print()
    
    return all_passed


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "Label Shortening Tests" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        passed1 = test_label_shortening()
        passed2 = test_character_savings()
        passed3 = test_multiple_scenarios()

        print("=" * 60)
        if passed1 and passed2 and passed3:
            print("✅ All label shortening tests passed!")
        else:
            print("❌ Some tests failed!")
        print("=" * 60)
        print()

        return 0 if (passed1 and passed2 and passed3) else 1

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
