#!/usr/bin/env python3
"""
Test that weather bot detects plain 'weather' and 'wx' words (without requiring hashtag)
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from weather_bot import WeatherBot


def test_plain_weather_word_detection():
    """Test that bot detects plain 'weather' word in messages"""
    # Clean up any persisted channel from previous tests
    if os.path.exists("logs/.last_weather_channel"):
        os.remove("logs/.last_weather_channel")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bot = WeatherBot(port=None, announce=True, debug=False)
        bot.mesh.start()
        
        # Verify no weather channel detected initially
        assert not bot._weather_channel_detected, "Weather channel should not be detected initially"
        
        # Simulate receiving a message with plain 'weather' word on channel 2
        test_message = "Message on weather"
        bot._detect_channel_name(test_message, 2)
        
        # Verify weather channel is detected
        assert bot._weather_channel_detected, "Should detect plain 'weather' as weather channel"
        assert bot._announce_channel_idx == 2, f"Announce channel should be 2, got {bot._announce_channel_idx}"
        assert 2 in bot._channel_idx_to_name, "Channel 2 should be mapped"
        assert bot._channel_idx_to_name[2] == "weather", "Channel 2 should be named 'weather'"
        
        bot.mesh.stop()
        print("✓ Test passed: plain 'weather' word detected")


def test_plain_wx_word_detection():
    """Test that bot detects plain 'wx' word in messages"""
    # Clean up any persisted channel from previous tests
    if os.path.exists("logs/.last_weather_channel"):
        os.remove("logs/.last_weather_channel")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bot = WeatherBot(port=None, announce=True, debug=False)
        bot.mesh.start()
        
        # Simulate receiving a message with plain 'wx' word on channel 3
        test_message = "Join the wx channel"
        bot._detect_channel_name(test_message, 3)
        
        # Verify weather channel is detected
        assert bot._weather_channel_detected, "Should detect plain 'wx' as weather channel"
        assert bot._announce_channel_idx == 3, f"Announce channel should be 3, got {bot._announce_channel_idx}"
        
        bot.mesh.stop()
        print("✓ Test passed: plain 'wx' word detected")


def test_hashtag_weather_still_works():
    """Test that #weather hashtag detection still works"""
    # Clean up any persisted channel from previous tests
    if os.path.exists("logs/.last_weather_channel"):
        os.remove("logs/.last_weather_channel")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bot = WeatherBot(port=None, announce=True, debug=False)
        bot.mesh.start()
        
        # Test with hashtag
        test_message = "Message on #weather channel"
        bot._detect_channel_name(test_message, 1)
        
        assert bot._weather_channel_detected, "Should detect #weather (with hashtag)"
        assert bot._announce_channel_idx == 1, "Should use channel 1"
        
        bot.mesh.stop()
        print("✓ Test passed: #weather hashtag detection still works")


def test_wether_not_detected():
    """Test that 'wether' (typo) is NOT detected"""
    # Clean up any persisted channel from previous tests
    if os.path.exists("logs/.last_weather_channel"):
        os.remove("logs/.last_weather_channel")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bot = WeatherBot(port=None, announce=True, debug=False)
        bot.mesh.start()
        
        # Test with 'wether' - should NOT be detected
        test_message = "Message on #wether channel"
        bot._detect_channel_name(test_message, 4)
        
        assert not bot._weather_channel_detected, "Should NOT detect #wether"
        assert 4 not in bot._channel_idx_to_name, "Channel 4 should NOT be mapped"
        
        bot.mesh.stop()
        print("✓ Test passed: #wether is correctly NOT detected")


def test_case_insensitive():
    """Test that detection is case-insensitive"""
    # Clean up any persisted channel from previous tests
    if os.path.exists("logs/.last_weather_channel"):
        os.remove("logs/.last_weather_channel")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bot = WeatherBot(port=None, announce=True, debug=False)
        bot.mesh.start()
        
        # Test with uppercase
        test_message = "Message on WEATHER channel"
        bot._detect_channel_name(test_message, 5)
        
        assert bot._weather_channel_detected, "Should detect WEATHER (uppercase)"
        assert bot._announce_channel_idx == 5, "Should use channel 5"
        
        bot.mesh.stop()
        print("✓ Test passed: detection is case-insensitive")


def test_word_boundaries():
    """Test that word boundaries are respected"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # These should all detect 'weather' or 'wx' due to word boundaries
        test_cases_should_match = [
            "Posted to weather",
            "Join wx discussion",
            "The weather is here",
            "Use wx command",
        ]
        
        for test_msg in test_cases_should_match:
            bot = WeatherBot(port=None, debug=False)
            bot.mesh.start()
            bot._detect_channel_name(test_msg, 1)
            assert bot._weather_channel_detected, f"Should detect weather in: {test_msg}"
            bot.mesh.stop()
        
        print("✓ Test passed: word boundaries work correctly")


if __name__ == "__main__":
    test_plain_weather_word_detection()
    test_plain_wx_word_detection()
    test_hashtag_weather_still_works()
    test_wether_not_detected()
    test_case_insensitive()
    test_word_boundaries()
    print("\n" + "=" * 50)
    print("✅ All plain 'weather' and 'wx' detection tests passed!")
    print("=" * 50)
