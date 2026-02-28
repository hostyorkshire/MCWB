#!/usr/bin/env python3
"""
Test validation and error reporting functionality for MCWB.

This test validates:
1. Channel index validation (channel-idx parameter)
2. Weather channel index validation (weather-channel-idx parameter)
3. Channel name validation (channel parameter)
4. Error messages are informative and helpful
"""

import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, "..")

from weather_bot import WeatherBot, _MAX_VALID_CHANNEL_IDX


class TestChannelValidation(unittest.TestCase):
    """Test channel parameter validation."""

    def test_valid_channel_idx_zero(self):
        """Test that channel_idx=0 is valid (boundary case)."""
        try:
            with patch("weather_bot.MeshCore"):
                bot = WeatherBot(allowed_channel_idx=0)
                self.assertEqual(bot.allowed_channel_idx, 0)
        except ValueError:
            self.fail("channel_idx=0 should be valid")

    def test_valid_channel_idx_max(self):
        """Test that channel_idx=7 is valid (boundary case)."""
        try:
            with patch("weather_bot.MeshCore"):
                bot = WeatherBot(allowed_channel_idx=_MAX_VALID_CHANNEL_IDX)
                self.assertEqual(bot.allowed_channel_idx, _MAX_VALID_CHANNEL_IDX)
        except ValueError:
            self.fail(f"channel_idx={_MAX_VALID_CHANNEL_IDX} should be valid")

    def test_invalid_channel_idx_negative(self):
        """Test that negative channel_idx raises ValueError."""
        with self.assertRaises(ValueError) as context:
            with patch("weather_bot.MeshCore"):
                WeatherBot(allowed_channel_idx=-1)
        
        error_msg = str(context.exception)
        self.assertIn("Invalid channel index: -1", error_msg)
        self.assertIn("must be between 0 and", error_msg)

    def test_invalid_channel_idx_too_high(self):
        """Test that channel_idx > 7 raises ValueError."""
        with self.assertRaises(ValueError) as context:
            with patch("weather_bot.MeshCore"):
                WeatherBot(allowed_channel_idx=8)
        
        error_msg = str(context.exception)
        self.assertIn("Invalid channel index: 8", error_msg)
        self.assertIn("must be between 0 and 7", error_msg)

    def test_invalid_channel_idx_way_too_high(self):
        """Test that very large channel_idx raises ValueError."""
        with self.assertRaises(ValueError) as context:
            with patch("weather_bot.MeshCore"):
                WeatherBot(allowed_channel_idx=100)
        
        error_msg = str(context.exception)
        self.assertIn("Invalid channel index: 100", error_msg)
        self.assertIn("must be between 0 and 7", error_msg)

    def test_valid_weather_channel_idx_zero(self):
        """Test that weather_channel_idx=0 is valid."""
        try:
            with patch("weather_bot.MeshCore"):
                bot = WeatherBot(weather_channel_idx=0)
                self.assertEqual(bot.weather_channel_idx, 0)
        except ValueError:
            self.fail("weather_channel_idx=0 should be valid")

    def test_valid_weather_channel_idx_max(self):
        """Test that weather_channel_idx=7 is valid."""
        try:
            with patch("weather_bot.MeshCore"):
                bot = WeatherBot(weather_channel_idx=_MAX_VALID_CHANNEL_IDX)
                self.assertEqual(bot.weather_channel_idx, _MAX_VALID_CHANNEL_IDX)
        except ValueError:
            self.fail(f"weather_channel_idx={_MAX_VALID_CHANNEL_IDX} should be valid")

    def test_invalid_weather_channel_idx_negative(self):
        """Test that negative weather_channel_idx raises ValueError."""
        with self.assertRaises(ValueError) as context:
            with patch("weather_bot.MeshCore"):
                WeatherBot(weather_channel_idx=-1)
        
        error_msg = str(context.exception)
        self.assertIn("Invalid weather channel index: -1", error_msg)
        self.assertIn("must be between 0 and 7", error_msg)

    def test_invalid_weather_channel_idx_too_high(self):
        """Test that weather_channel_idx > 7 raises ValueError."""
        with self.assertRaises(ValueError) as context:
            with patch("weather_bot.MeshCore"):
                WeatherBot(weather_channel_idx=10)
        
        error_msg = str(context.exception)
        self.assertIn("Invalid weather channel index: 10", error_msg)
        self.assertIn("must be between 0 and 7", error_msg)


class TestChannelNameValidation(unittest.TestCase):
    """Test channel name validation."""

    def test_valid_channel_name_single(self):
        """Test that a single channel name is accepted."""
        with patch("weather_bot.MeshCore"):
            bot = WeatherBot(channel="weather")
            self.assertEqual(bot.channels, ["weather"])

    def test_valid_channel_name_multiple(self):
        """Test that multiple channel names are accepted."""
        with patch("weather_bot.MeshCore"):
            bot = WeatherBot(channel="weather,alerts,forecast")
            self.assertEqual(bot.channels, ["weather", "alerts", "forecast"])

    def test_channel_name_with_spaces(self):
        """Test that spaces around channel names are trimmed."""
        with patch("weather_bot.MeshCore"):
            bot = WeatherBot(channel="weather , alerts , forecast")
            self.assertEqual(bot.channels, ["weather", "alerts", "forecast"])

    def test_empty_channel_name(self):
        """Test that empty channel string results in empty list."""
        with patch("weather_bot.MeshCore"):
            bot = WeatherBot(channel="")
            self.assertEqual(bot.channels, [])

    def test_channel_name_only_spaces(self):
        """Test that whitespace-only channel string results in empty list."""
        with patch("weather_bot.MeshCore"):
            bot = WeatherBot(channel="   ")
            self.assertEqual(bot.channels, [])

    def test_channel_name_with_hash_prefix_warning(self):
        """Test that channel name with # prefix generates warning (but still works)."""
        # Capture stdout to check for warning
        captured_output = StringIO()
        
        with patch("weather_bot.MeshCore"):
            with patch('sys.stdout', captured_output):
                bot = WeatherBot(channel="#weather")
        
        # Channel should still be set (with the # included)
        self.assertEqual(bot.channels, ["#weather"])
        
        # Check that warning was printed
        output = captured_output.getvalue()
        self.assertIn("WARNING", output)
        self.assertIn("starts with '#'", output)


class TestErrorMessages(unittest.TestCase):
    """Test that error messages are informative and helpful."""

    def test_channel_idx_error_includes_valid_range(self):
        """Test that channel_idx error includes valid range."""
        with self.assertRaises(ValueError) as context:
            with patch("weather_bot.MeshCore"):
                WeatherBot(allowed_channel_idx=10)
        
        error_msg = str(context.exception)
        self.assertIn("0, 1, 2, 3, 4, 5, 6, 7", error_msg)

    def test_channel_idx_error_includes_tip(self):
        """Test that channel_idx error includes helpful tip."""
        with self.assertRaises(ValueError) as context:
            with patch("weather_bot.MeshCore"):
                WeatherBot(allowed_channel_idx=10)
        
        error_msg = str(context.exception)
        self.assertIn("Tip:", error_msg)
        self.assertIn("--channel-idx", error_msg)

    def test_weather_channel_idx_error_includes_tip(self):
        """Test that weather_channel_idx error includes helpful tip."""
        with self.assertRaises(ValueError) as context:
            with patch("weather_bot.MeshCore"):
                WeatherBot(weather_channel_idx=10)
        
        error_msg = str(context.exception)
        self.assertIn("Tip:", error_msg)
        self.assertIn("--weather-channel-idx", error_msg)

    def test_error_includes_actual_value(self):
        """Test that error message includes the actual invalid value provided."""
        with self.assertRaises(ValueError) as context:
            with patch("weather_bot.MeshCore"):
                WeatherBot(allowed_channel_idx=42)
        
        error_msg = str(context.exception)
        self.assertIn("42", error_msg)
        self.assertIn("Your value:", error_msg)


class TestValidationLogging(unittest.TestCase):
    """Test that validation results are logged appropriately."""

    def test_successful_validation_logged(self):
        """Test that successful validation is logged."""
        with patch("weather_bot.MeshCore"):
            bot = WeatherBot(allowed_channel_idx=1, weather_channel_idx=2)
            
            # Check that logger methods were called (indirectly through initialization)
            self.assertIsNotNone(bot.logger)


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("MCWB - Validation and Error Reporting Tests")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestChannelValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestChannelNameValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorMessages))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationLogging))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ ALL VALIDATION TESTS PASSED")
        print(f"   Ran {result.testsRun} tests successfully")
    else:
        print("❌ SOME TESTS FAILED")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
