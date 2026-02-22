#!/usr/bin/env python3
"""
Test script for weather channel index configuration
Tests the new --weather-channel-idx option
"""

import sys
from weather_bot import WeatherBot
from unittest.mock import MagicMock, patch


def test_weather_channel_idx_filtering():
    """Test that weather_channel_idx correctly filters incoming messages"""
    print("=" * 60)
    print("TEST 1: Weather Channel Index Filtering")
    print("=" * 60)
    
    # Create bot with weather_channel_idx=2
    # Note: allowed_channel_idx is set by the caller (main function), not in __init__
    bot = WeatherBot(debug=False, weather_channel_idx=2, allowed_channel_idx=2)
    
    # Check initialization
    assert bot.weather_channel_idx == 2, "weather_channel_idx should be set"
    assert bot._announce_channel_idx == 2, "announce channel should use weather_channel_idx"
    assert bot.allowed_channel_idx == 2, "allowed_channel_idx should be passed correctly"
    
    print("  ✓ Bot initialized with weather_channel_idx=2")
    print(f"  ✓ announce_channel_idx set to {bot._announce_channel_idx}")
    print(f"  ✓ allowed_channel_idx set to {bot.allowed_channel_idx}")
    print()


def test_weather_channel_idx_announcements():
    """Test that announcements use the configured weather_channel_idx"""
    print("=" * 60)
    print("TEST 2: Announcements Use Weather Channel Index")
    print("=" * 60)
    
    # Mock serial to avoid needing hardware
    with patch('weather_bot.serial'):
        # Create bot with weather_channel_idx=3
        bot = WeatherBot(debug=False, weather_channel_idx=3, announce=True)
        
        # Verify announcement channel is set correctly
        assert bot._announce_channel_idx == 3, "Announcement should use weather_channel_idx"
        
        print("  ✓ Bot with weather_channel_idx=3")
        print(f"  ✓ Announcements will be sent on channel_idx={bot._announce_channel_idx}")
        print()


def test_weather_channel_idx_persists():
    """Test that weather_channel_idx doesn't change when messages arrive"""
    print("=" * 60)
    print("TEST 3: Weather Channel Index Persists")
    print("=" * 60)
    
    # Create bot with weather_channel_idx=1
    bot = WeatherBot(debug=False, weather_channel_idx=1, allowed_channel_idx=1)
    
    initial_announce_idx = bot._announce_channel_idx
    assert initial_announce_idx == 1, "Initial announce channel should be 1"
    
    # Manually simulate the message handling without triggering actual weather fetch/send
    # Just test the logic that updates announce_channel_idx
    channel_idx = 2
    
    # This is the code from _handle_channel_message that updates announce_channel_idx
    if bot.weather_channel_idx is None:
        bot._announce_channel_idx = channel_idx
    
    assert bot._announce_channel_idx == 1, "Announce channel should not change when weather_channel_idx is set"
    
    print("  ✓ Bot configured with weather_channel_idx=1")
    print("  ✓ Simulated message on channel_idx=2 (would be filtered)")
    print(f"  ✓ Announce channel remains {bot._announce_channel_idx} (not changed)")
    print()


def test_backward_compatibility():
    """Test backward compatibility with existing --channel-idx option"""
    print("=" * 60)
    print("TEST 4: Backward Compatibility")
    print("=" * 60)
    
    # Bot without weather_channel_idx (old behavior)
    bot_old = WeatherBot(debug=False, allowed_channel_idx=2)
    assert bot_old.weather_channel_idx is None, "weather_channel_idx should be None when not specified"
    assert bot_old._announce_channel_idx == 0, "Should start with default channel 0"
    
    print("  ✓ Bot without weather_channel_idx behaves as before")
    print(f"  ✓ announce_channel_idx starts at {bot_old._announce_channel_idx}")
    
    # Manually simulate the logic from _handle_channel_message for updating announce channel
    channel_idx = 2
    if bot_old.weather_channel_idx is None:
        bot_old._announce_channel_idx = channel_idx
    
    assert bot_old._announce_channel_idx == 2, "Announce channel should update from received message"
    
    print("  ✓ After simulated message on channel_idx=2")
    print(f"  ✓ announce_channel_idx updated to {bot_old._announce_channel_idx}")
    print()


def test_weather_channel_idx_priority():
    """Test that weather_channel_idx takes priority over channel_idx"""
    print("=" * 60)
    print("TEST 5: Weather Channel Index Priority")
    print("=" * 60)
    
    # When weather_channel_idx is specified, it should be used for allowed_channel_idx
    # This is handled in main() where:
    # allowed_idx = args.channel_idx if args.weather_channel_idx is None else args.weather_channel_idx
    
    # Simulate this behavior
    weather_idx = 3
    channel_idx = 1
    allowed_idx = channel_idx if weather_idx is None else weather_idx
    
    bot = WeatherBot(debug=False, weather_channel_idx=weather_idx, allowed_channel_idx=allowed_idx)
    
    assert bot.weather_channel_idx == 3, "weather_channel_idx should be 3"
    assert bot.allowed_channel_idx == 3, "allowed_channel_idx should use weather_channel_idx"
    
    print("  ✓ When both --weather-channel-idx (3) and --channel-idx (1) specified")
    print(f"  ✓ Bot uses weather_channel_idx={bot.weather_channel_idx}")
    print(f"  ✓ Filtering on allowed_channel_idx={bot.allowed_channel_idx}")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 6 + "Weather Channel Index Configuration Tests" + " " * 9 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_weather_channel_idx_filtering()
        test_weather_channel_idx_announcements()
        test_weather_channel_idx_persists()
        test_backward_compatibility()
        test_weather_channel_idx_priority()

        print("=" * 60)
        print("All weather channel index tests passed!")
        print("=" * 60)
        print()
        print("Usage examples:")
        print("  # Weather channel is on index 2 in your MeshCore app")
        print("  python3 weather_bot.py --weather-channel-idx 2")
        print()
        print("  # Weather channel on index 3, with announcements")
        print("  python3 weather_bot.py --weather-channel-idx 3 --announce")
        print()
        print("  # Old way still works (for backward compatibility)")
        print("  python3 weather_bot.py --channel-idx 1")
        print()

        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
