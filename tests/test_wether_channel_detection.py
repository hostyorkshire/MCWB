#!/usr/bin/env python3
"""
Test that weather bot detects the #wether channel (typo variant of #weather)
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from weather_bot import WeatherBot


def test_wether_channel_detection_from_hashtag():
    """Test that bot detects #wether hashtag in messages"""
    # Clean up any persisted channel from previous tests
    if os.path.exists("logs/.last_weather_channel"):
        os.remove("logs/.last_weather_channel")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create weather bot without explicit channel configuration
        bot = WeatherBot(port=None, announce=True, debug=False)
        bot.mesh.start()
        
        # Verify no weather channel detected initially
        assert not bot._weather_channel_detected, "Weather channel should not be detected initially"
        
        # Simulate receiving a message with #wether hashtag on channel 2
        test_message = "Message on #wether channel"
        bot._detect_channel_name(test_message, 2)
        
        # Verify #wether channel is detected
        assert bot._weather_channel_detected, "Should detect #wether as weather channel"
        assert bot._announce_channel_idx == 2, f"Announce channel should be 2, got {bot._announce_channel_idx}"
        assert 2 in bot._channel_idx_to_name, "Channel 2 should be mapped"
        assert bot._channel_idx_to_name[2] == "weather", "Channel 2 should be named 'weather'"
        
        bot.mesh.stop()
        print("✓ Test passed: #wether hashtag detected")


def test_wether_case_insensitive():
    """Test that #wether detection is case-insensitive"""
    # Clean up any persisted channel from previous tests
    if os.path.exists("logs/.last_weather_channel"):
        os.remove("logs/.last_weather_channel")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bot = WeatherBot(port=None, announce=True, debug=False)
        bot.mesh.start()
        
        # Test with uppercase
        test_message = "Message on #WETHER channel"
        bot._detect_channel_name(test_message, 3)
        
        assert bot._weather_channel_detected, "Should detect #WETHER (uppercase)"
        assert bot._announce_channel_idx == 3, "Should use channel 3"
        
        bot.mesh.stop()
        print("✓ Test passed: #wether detection is case-insensitive")


def test_wether_in_wx_command():
    """Test that 'wx' command works when #wether is mentioned"""
    # Clean up any persisted channel from previous tests
    if os.path.exists("logs/.last_weather_channel"):
        os.remove("logs/.last_weather_channel")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bot = WeatherBot(port=None, announce=True, debug=False)
        bot.mesh.start()
        
        # Simulate a weather command on #wether channel
        test_message = "User: on #wether wx London"
        
        # Detect the channel name
        bot._detect_channel_name(test_message, 1)
        
        # Parse the command - should strip out "#wether" and parse "wx London"
        location, country = bot._parse_command("on #wether wx London")
        
        assert location == "London", f"Should extract location 'London', got '{location}'"
        assert bot._weather_channel_detected, "Should detect #wether channel"
        
        bot.mesh.stop()
        print("✓ Test passed: wx command works with #wether reference")


def test_wether_pattern_in_parse_command():
    """Test that #wether is properly stripped from commands"""
    bot = WeatherBot(port=None, debug=False)
    
    # Test various formats including edge cases
    test_cases = [
        ("wx #wether London", "London"),
        ("wx on #wether London", "London"),
        ("weather #wether York", "York"),
        ("#wether wx Manchester", "Manchester"),
        ("on#wether wx London", "London"),  # No space after 'on'
        ("weather channel wx York", "York"),  # 'weather channel' at start
        ("on weather channel wx Leeds", "Leeds"),  # 'on weather channel' pattern
    ]
    
    for input_text, expected_location in test_cases:
        location, country = bot._parse_command(input_text)
        assert location == expected_location, f"For '{input_text}', expected '{expected_location}' but got '{location}'"
    
    print("✓ Test passed: #wether pattern properly stripped from commands")


def test_wether_coexists_with_weather():
    """Test that #wether detection doesn't break #weather detection"""
    # Clean up any persisted channel from previous tests
    if os.path.exists("logs/.last_weather_channel"):
        os.remove("logs/.last_weather_channel")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bot1 = WeatherBot(port=None, announce=True, debug=False)
        bot1.mesh.start()
        
        # Detect #weather on channel 1
        bot1._detect_channel_name("Message on #weather", 1)
        assert bot1._weather_channel_detected, "Should detect #weather"
        assert bot1._announce_channel_idx == 1, "Should use channel 1"
        
        bot1.mesh.stop()
        
        # Clean up persisted channel before next test
        if os.path.exists("logs/.last_weather_channel"):
            os.remove("logs/.last_weather_channel")
        
        # Create a new bot and detect #wether on channel 2
        bot2 = WeatherBot(port=None, announce=True, debug=False)
        bot2.mesh.start()
        
        bot2._detect_channel_name("Message on #wether", 2)
        assert bot2._weather_channel_detected, "Should detect #wether"
        assert bot2._announce_channel_idx == 2, "Should use channel 2"
        
        bot2.mesh.stop()
        print("✓ Test passed: #wether and #weather detection coexist")


if __name__ == "__main__":
    test_wether_channel_detection_from_hashtag()
    test_wether_case_insensitive()
    test_wether_in_wx_command()
    test_wether_pattern_in_parse_command()
    test_wether_coexists_with_weather()
    print("\n" + "=" * 50)
    print("✅ All #wether channel detection tests passed!")
    print("=" * 50)
