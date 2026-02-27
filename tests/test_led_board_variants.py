#!/usr/bin/env python3
"""
Test LED board variant configuration
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from weather_bot import WeatherBot, LEDController


class TestLEDVariants(unittest.TestCase):
    """Test LED board variant configuration"""

    def test_default_configuration(self):
        """Test default LED configuration (no LEDs enabled)"""
        bot = WeatherBot()
        self.assertFalse(bot.led_controller.enabled)
        self.assertEqual(bot.led_controller.blue_pin, 25)
        self.assertIsNone(bot.led_controller.green_pin)
        self.assertIsNone(bot.led_controller.red_pin)

    def test_dollatek_variant(self):
        """Test DollaTek board variant (single LED on GPIO25)"""
        bot = WeatherBot(enable_leds=True, led_board_variant="dollatek")
        self.assertTrue(bot.led_controller.enabled)
        self.assertEqual(bot.led_controller.blue_pin, 25)
        self.assertIsNone(bot.led_controller.green_pin)
        self.assertIsNone(bot.led_controller.red_pin)

    def test_heltec_v2_variant(self):
        """Test Heltec V2 board variant (single LED on GPIO25)"""
        bot = WeatherBot(enable_leds=True, led_board_variant="heltec-v2")
        self.assertTrue(bot.led_controller.enabled)
        self.assertEqual(bot.led_controller.blue_pin, 25)
        self.assertIsNone(bot.led_controller.green_pin)
        self.assertIsNone(bot.led_controller.red_pin)

    def test_custom_pins(self):
        """Test custom GPIO pin configuration"""
        bot = WeatherBot(
            enable_leds=True,
            led_blue_pin=2,
            led_green_pin=4,
            led_red_pin=5
        )
        self.assertTrue(bot.led_controller.enabled)
        self.assertEqual(bot.led_controller.blue_pin, 2)
        self.assertEqual(bot.led_controller.green_pin, 4)
        self.assertEqual(bot.led_controller.red_pin, 5)

    def test_custom_pins_override_variant(self):
        """Test that custom pins override board variant settings"""
        bot = WeatherBot(
            enable_leds=True,
            led_board_variant="dollatek",
            led_blue_pin=2,
            led_green_pin=4
        )
        self.assertTrue(bot.led_controller.enabled)
        self.assertEqual(bot.led_controller.blue_pin, 2)  # Overridden
        self.assertEqual(bot.led_controller.green_pin, 4)  # Overridden
        self.assertIsNone(bot.led_controller.red_pin)  # Variant default

    def test_invalid_variant(self):
        """Test that invalid board variant uses defaults"""
        bot = WeatherBot(enable_leds=True, led_board_variant="invalid")
        self.assertTrue(bot.led_controller.enabled)
        # Should fall back to defaults
        self.assertEqual(bot.led_controller.blue_pin, 25)
        self.assertIsNone(bot.led_controller.green_pin)
        self.assertIsNone(bot.led_controller.red_pin)

    def test_led_flash_with_none_pin(self):
        """Test that LED flash operations handle None pins gracefully"""
        bot = WeatherBot(enable_leds=True, led_board_variant="dollatek")

        # These should not raise exceptions even though green/red are None
        bot.led_controller.rx_flash()
        bot.led_controller.tx_flash()

        # Blue LED should work
        bot.led_controller.start_heartbeat()
        bot.led_controller.stop_heartbeat()

    def test_board_variants_exist(self):
        """Test that board variant presets are defined"""
        self.assertIn("dollatek", LEDController.BOARD_VARIANTS)
        self.assertIn("heltec-v2", LEDController.BOARD_VARIANTS)

        # Verify DollaTek configuration
        dollatek = LEDController.BOARD_VARIANTS["dollatek"]
        self.assertEqual(dollatek["blue"], 25)
        self.assertIsNone(dollatek["green"])
        self.assertIsNone(dollatek["red"])

        # Verify Heltec V2 configuration
        heltec = LEDController.BOARD_VARIANTS["heltec-v2"]
        self.assertEqual(heltec["blue"], 25)
        self.assertIsNone(heltec["green"])
        self.assertIsNone(heltec["red"])


def main():
    """Run the test suite"""
    print("=" * 70)
    print("Testing LED Board Variant Configuration")
    print("=" * 70)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestLEDVariants)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✓ All LED configuration tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 70)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
