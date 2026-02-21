#!/usr/bin/env python3
"""
Manual verification script to demonstrate the country code conversion feature.
Shows before/after comparison of bot output with country codes.
"""

import sys
from weather_bot import WeatherBot


def demonstrate_country_code_conversion():
    """Demonstrate the country code conversion in action"""
    print("=" * 70)
    print("DEMONSTRATION: Country Code Conversion for Shortened Bot Output")
    print("=" * 70)
    print()
    print("Goal: Shorten bot reply output by converting country names to codes")
    print("      (e.g., 'United Kingdom' -> 'UK', 'Great Britain' -> 'GB')")
    print()

    bot = WeatherBot(debug=False)

    # Example weather data
    weather_data = {
        "current": {
            "temperature_2m": 9.5,
            "apparent_temperature": 7.2,
            "relative_humidity_2m": 82,
            "wind_speed_10m": 12.4,
            "wind_direction_10m": 245,
            "precipitation": 0.1,
            "weather_code": 3
        }
    }

    test_locations = [
        {"name": "Brighton", "country": "United Kingdom"},
        {"name": "London", "country": "Great Britain"},
        {"name": "Manchester", "country": "GB"},
        {"name": "Paris", "country": "France"},
        {"name": "New York", "country": "United States"},
    ]

    print("BEFORE (with full country names):")
    print("-" * 70)
    for loc in test_locations:
        # Show what the old format would look like
        old_format = f"{loc['name']}, {loc['country']}"
        print(f"  {old_format}")
    print()

    print("AFTER (with country codes - SPACE SAVED!):")
    print("-" * 70)
    for loc in test_locations:
        # Show the new format with country codes
        location_data = {"name": loc["name"], "country": loc["country"]}
        response = bot.format_weather_response(location_data, weather_data)
        # Just print the first line (location + country code)
        first_line = response.split('\n')[0]
        print(f"  {first_line}")
    print()

    print("=" * 70)
    print("CHARACTER COUNT COMPARISON:")
    print("=" * 70)
    
    total_old = 0
    total_new = 0
    
    for loc in test_locations:
        old = f"{loc['name']}, {loc['country']}"
        new = f"{loc['name']}, {bot.get_country_code(loc['country'])}"
        saved = len(old) - len(new)
        total_old += len(old)
        total_new += len(new)
        
        print(f"{loc['name']:15} | Old: {len(old):2} chars | New: {len(new):2} chars | Saved: {saved:2} chars")
    
    print("-" * 70)
    print(f"{'TOTAL':15} | Old: {total_old:2} chars | New: {total_new:2} chars | Saved: {total_old - total_new:2} chars")
    print()
    
    print("=" * 70)
    print("FULL EXAMPLE OUTPUT:")
    print("=" * 70)
    location_data = {"name": "Brighton", "country": "United Kingdom"}
    response = bot.format_weather_response(location_data, weather_data)
    print(response)
    print()
    
    print("✅ SUCCESS: Country names converted to codes, saving characters!")
    print()


def main():
    """Run the demonstration"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Country Code Conversion Demo" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    try:
        demonstrate_country_code_conversion()
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
