#!/usr/bin/env python3
"""
Diagnostic tool to verify weather command parsing.
Use this to check if "wx york USA" and "wx York UK" commands are recognized.

Usage:
    python3 diagnose_command_parsing.py
    python3 diagnose_command_parsing.py "wx york USA"
    python3 diagnose_command_parsing.py "wx York UK" "weather Leeds UK"
"""
import sys
from weather_bot import WeatherBot


def diagnose_command(command: str):
    """Parse and display how a command is interpreted."""
    bot = WeatherBot(debug=False, country=None)

    print("\nCommand: \"{command}\"")
    print("-" * 60)

    location, country = bot._parse_command(command)

    if location is None:
        print("❌ NOT RECOGNIZED as a weather command")
        print("   Expected format: 'wx [location]' or 'weather [location]'")
        return False

    print("✅ RECOGNIZED as weather command")
    print("   Location: \"{location}\"")
    print(f"   Country:  {country if country else '(not specified)'}")

    # Show what would be sent to the API
    if country:
        print("\n   API will search for: \"{location}\" in country \"{country}\"")
        print("   URL: https://geocoding-api.open-meteo.com/v1/search")
        print(f"        ?name={location}&country={country}")
    else:
        print("\n   API will search for: \"{location}\" (global search)")
        print("   URL: https://geocoding-api.open-meteo.com/v1/search")
        print(f"        ?name={location}")

    return True


def main():
    """Run diagnostics on provided commands or use default test cases."""
    print("=" * 60)
    print("Weather Command Parsing Diagnostic Tool")
    print("=" * 60)

    if len(sys.argv) > 1:
        # Test commands provided as arguments
        commands = sys.argv[1:]
    else:
        # Default test cases
        print("\nNo commands provided. Testing default cases...")
        commands = [
            "wx york USA",
            "wx York UK",
            "wx york usa",
            "WX YORK UK",
            "weather York USA",
            "wx Paris FR",
            "wx York",
            "wx York, UK",
            "random text",
            "wx",
        ]

    results = []
    for cmd in commands:
        success = diagnose_command(cmd)
        results.append((cmd, success))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    recognized = sum(1 for _, success in results if success)
    total = len(results)

    for cmd, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {cmd}")

    print(f"\nRecognized: {recognized}/{total} commands")

    if recognized == total:
        print("\n✅ All commands recognized correctly!")
    elif recognized > 0:
        print(f"\n⚠️  {total - recognized} command(s) not recognized")
    else:
        print("\n❌ No commands recognized")

    print("\n" + "=" * 60)
    print("HELP")
    print("=" * 60)
    print("Valid command formats:")
    print("  wx [location]              - e.g., 'wx London'")
    print("  wx [location] [country]    - e.g., 'wx York UK'")
    print("  weather [location]         - e.g., 'weather Paris FR'")
    print("\nSupported country codes:")
    print("  UK, USA, US, GB, or any 2-letter ISO code (FR, DE, CA, etc.)")
    print("\nCase insensitive:")
    print("  'wx', 'WX', 'Wx' all work")
    print("  'UK', 'uk', 'Uk' all work")


if __name__ == "__main__":
    main()
