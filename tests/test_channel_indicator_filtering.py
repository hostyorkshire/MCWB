#!/usr/bin/env python3
"""
Test that channel indicators are properly filtered from weather commands
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from weather_bot import WeatherBot


def test_filter_channel_indicators():
    """Test that channel indicators are removed from location strings"""
    print("=" * 70)
    print("TEST: Filter channel indicators from WX commands")
    print("=" * 70)

    test_cases = [
        ("WX London on #weather", "London", None),
        ("wx York #weather", "York", None),
        ("WX Seattle #wx", "Seattle", None),
        ("weather Paris weather channel", "Paris", None),
        ("WX New York on #weather", "New York", None),
        ("wx London UK on #weather", "London", "GB"),
        ("WX York, UK", "York, UK", None),  # Comma format preserved
        ("wx Sheffield", "Sheffield", None),  # No channel indicator
    ]

    for command, expected_location, expected_country in test_cases:
        location, country = WeatherBot._parse_command(command)
        
        assert location == expected_location, (
            f"Command '{command}' should extract location '{expected_location}', "
            f"but got '{location}'"
        )
        assert country == expected_country, (
            f"Command '{command}' should extract country '{expected_country}', "
            f"but got '{country}'"
        )
        
        print(f"  ✓ '{command}' -> location='{location}', country={country}")

    print()


if __name__ == "__main__":
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "MCWB - Channel Indicator Filtering Tests" + " " * 13 + "║")
    print("╚" + "=" * 68 + "╝\n")

    try:
        test_filter_channel_indicators()

        print("=" * 70)
        print("✓ All channel indicator filtering tests passed!")
        print("=" * 70)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
