#!/usr/bin/env python3
"""
Combined demonstration of Steps 1 and 2: Complete output shortening
Shows the total character savings from both country codes and label shortening
"""

import sys
from weather_bot import WeatherBot


def show_progressive_improvements():
    """Show the progressive improvements from original to final format"""
    
    print("=" * 70)
    print("COMBINED IMPROVEMENTS: Steps 1 & 2")
    print("=" * 70)
    print()
    
    bot = WeatherBot(debug=False)
    
    # Test locations with various countries
    test_cases = [
        {
            "name": "Brighton",
            "country_before": "United Kingdom",
            "country_after": "UK",
            "weather": {
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
        },
        {
            "name": "New York",
            "country_before": "United States",
            "country_after": "US",
            "weather": {
                "current": {
                    "temperature_2m": 22.3,
                    "apparent_temperature": 21.8,
                    "relative_humidity_2m": 65,
                    "wind_speed_10m": 10.5,
                    "wind_direction_10m": 180,
                    "precipitation": 0.0,
                    "weather_code": 1
                }
            }
        },
    ]
    
    total_original = 0
    total_step1 = 0
    total_final = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"Example {i}: {case['name']}, {case['country_before']}")
        print("=" * 70)
        print()
        
        # Original format (with full labels and full country name)
        original = f"""{case['name']}, {case['country_before']}
Conditions: {bot.get_weather_description(case['weather']['current']['weather_code'])}
Temp: {case['weather']['current']['temperature_2m']}°C (feels like {case['weather']['current']['apparent_temperature']}°C)
Humidity: {case['weather']['current']['relative_humidity_2m']}%
Wind: {case['weather']['current']['wind_speed_10m']} km/h at {case['weather']['current']['wind_direction_10m']}°
Precipitation: {case['weather']['current']['precipitation']} mm"""
        
        # Step 1: Country code only
        step1 = f"""{case['name']}, {case['country_after']}
Conditions: {bot.get_weather_description(case['weather']['current']['weather_code'])}
Temp: {case['weather']['current']['temperature_2m']}°C (feels like {case['weather']['current']['apparent_temperature']}°C)
Humidity: {case['weather']['current']['relative_humidity_2m']}%
Wind: {case['weather']['current']['wind_speed_10m']} km/h at {case['weather']['current']['wind_direction_10m']}°
Precipitation: {case['weather']['current']['precipitation']} mm"""
        
        # Final: Both country code and shortened labels (current implementation)
        location_data = {"name": case['name'], "country": case['country_before']}
        final = bot.format_weather_response(location_data, case['weather'])
        
        print("ORIGINAL (no optimizations):")
        print("-" * 70)
        print(original)
        print(f"Characters: {len(original)}")
        print()
        
        print("After STEP 1 (country codes only):")
        print("-" * 70)
        print(step1)
        step1_saved = len(original) - len(step1)
        print(f"Characters: {len(step1)} (saved {step1_saved} chars)")
        print()
        
        print("After STEP 2 (country codes + shortened labels):")
        print("-" * 70)
        print(final)
        final_saved = len(original) - len(final)
        print(f"Characters: {len(final)} (saved {final_saved} chars)")
        print()
        
        print("SUMMARY:")
        print("-" * 70)
        print(f"  Original: {len(original)} chars")
        print(f"  Step 1:   {len(step1)} chars (saved {step1_saved})")
        print(f"  Step 2:   {len(final)} chars (saved {final_saved} total)")
        print(f"  Reduction: {(final_saved/len(original)*100):.1f}%")
        print()
        print("=" * 70)
        print()
        
        total_original += len(original)
        total_step1 += len(step1)
        total_final += len(final)
    
    # Overall summary
    print("OVERALL RESULTS ACROSS ALL EXAMPLES:")
    print("=" * 70)
    print(f"Total characters (original):  {total_original} chars")
    print(f"Total characters (Step 1):    {total_step1} chars")
    print(f"Total characters (Step 2):    {total_final} chars")
    print()
    print(f"Step 1 savings: {total_original - total_step1} chars")
    print(f"Step 2 savings: {total_step1 - total_final} chars")
    print(f"TOTAL SAVED:    {total_original - total_final} chars ({(total_original - total_final)/total_original*100:.1f}% reduction)")
    print("=" * 70)
    print()


def show_breakdown():
    """Show detailed breakdown of savings"""
    
    print("=" * 70)
    print("DETAILED BREAKDOWN OF CHARACTER SAVINGS")
    print("=" * 70)
    print()
    
    print("STEP 1: Country Name to Code Conversion")
    print("-" * 70)
    country_savings = [
        ("United Kingdom → UK", 14, 2, 12),
        ("United States → US", 13, 2, 11),
        ("Great Britain → GB", 13, 2, 11),
    ]
    
    for change, before, after, saved in country_savings:
        print(f"  {change:30} {saved} chars")
    
    print()
    print("STEP 2: Label Shortening")
    print("-" * 70)
    label_savings = [
        ("Conditions: → Cond:", 12, 6, 6),
        ("feels like → feels", 10, 5, 5),
        ("Humidity: → Humid:", 10, 7, 3),
        ("Precipitation: → Precip:", 15, 8, 7),
    ]
    
    for change, before, after, saved in label_savings:
        print(f"  {change:35} {saved} chars")
    
    total_label_saved = sum(s[3] for s in label_savings)
    
    print()
    print("=" * 70)
    print(f"Typical savings per weather report:")
    print(f"  Country code:    ~12 chars")
    print(f"  Label shortening: {total_label_saved} chars")
    print(f"  TOTAL:           ~{12 + total_label_saved} chars per report")
    print("=" * 70)
    print()


def main():
    """Run the combined demonstration"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 12 + "Combined Output Shortening Demo" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    try:
        show_breakdown()
        show_progressive_improvements()
        
        print("✅ SUCCESS: Output significantly shortened!")
        print("   Both country codes and label shortening are now active.")
        print()
        
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
