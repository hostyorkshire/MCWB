#!/usr/bin/env python3
"""
Test script for reboot notification functionality
"""

import os
import sys
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from weather_bot import WeatherBot, STATE_FILE, REBOOT_NOTIFY_MESSAGE


class TestRebootNotification(unittest.TestCase):
    """Test reboot notification functionality"""

    def setUp(self):
        """Set up test environment"""
        # Remove state file if it exists
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

    def tearDown(self):
        """Clean up test environment"""
        # Remove state file if it exists
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

    def test_first_run_no_reboot_detection(self):
        """Test that first run does not detect a reboot"""
        bot = WeatherBot(debug=False, reboot_notify=True)
        self.assertFalse(bot._is_reboot())

    def test_mark_running_creates_state_file(self):
        """Test that marking as running creates state file"""
        bot = WeatherBot(debug=False, reboot_notify=True)
        self.assertFalse(os.path.exists(STATE_FILE))
        bot._mark_running()
        self.assertTrue(os.path.exists(STATE_FILE))

    def test_subsequent_run_detects_reboot(self):
        """Test that subsequent run detects a reboot"""
        # First run - create state file
        bot1 = WeatherBot(debug=False, reboot_notify=True)
        bot1._mark_running()

        # Second run - should detect reboot
        bot2 = WeatherBot(debug=False, reboot_notify=True)
        self.assertTrue(bot2._is_reboot())

    def test_reboot_notification_not_sent_on_first_run(self):
        """Test that reboot notification is not sent on first run"""
        bot = WeatherBot(debug=False, reboot_notify=True)

        # Mock the send method
        with patch.object(bot, '_send_channel_msg') as mock_send:
            bot._send_reboot_notification()
            # Should not send notification on first run
            mock_send.assert_not_called()

    def test_reboot_notification_sent_on_restart(self):
        """Test that reboot notification is sent on restart"""
        # First run - create state file
        bot1 = WeatherBot(debug=False, reboot_notify=True)
        bot1._mark_running()

        # Second run - should send notification
        bot2 = WeatherBot(debug=False, reboot_notify=True, weather_channel_idx=1)

        with patch.object(bot2, '_send_channel_msg') as mock_send:
            bot2._send_reboot_notification()
            # Should send notification on restart
            mock_send.assert_called_once_with(REBOOT_NOTIFY_MESSAGE, 1)

    def test_reboot_notification_disabled_by_default(self):
        """Test that reboot notification is disabled by default"""
        # Create state file to simulate restart
        bot1 = WeatherBot(debug=False)
        bot1._mark_running()

        # Second run without reboot_notify flag
        bot2 = WeatherBot(debug=False, reboot_notify=False)

        with patch.object(bot2, '_send_channel_msg') as mock_send:
            bot2._send_reboot_notification()
            # Should not send notification when disabled
            mock_send.assert_not_called()

    def test_state_file_contains_timestamp(self):
        """Test that state file contains a timestamp"""
        bot = WeatherBot(debug=False, reboot_notify=True)
        bot._mark_running()

        # Read state file
        with open(STATE_FILE, 'r') as f:
            content = f.read().strip()

        # Should be a valid timestamp
        try:
            timestamp = int(content)
            # Should be a recent timestamp (within last minute)
            self.assertLess(abs(time.time() - timestamp), 60)
        except ValueError:
            self.fail("State file should contain a valid timestamp")

    def test_reboot_notification_uses_correct_channel(self):
        """Test that reboot notification uses the correct channel"""
        # Create state file to simulate restart
        bot1 = WeatherBot(debug=False)
        bot1._mark_running()

        # Test with weather_channel_idx
        bot2 = WeatherBot(debug=False, reboot_notify=True, weather_channel_idx=5)
        with patch.object(bot2, '_send_channel_msg') as mock_send:
            bot2._send_reboot_notification()
            mock_send.assert_called_once_with(REBOOT_NOTIFY_MESSAGE, 5)


def main():
    """Run tests"""
    print("=" * 60)
    print("Testing Reboot Notification Functionality")
    print("=" * 60)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRebootNotification)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✓ All reboot notification tests passed!")
    else:
        print("✗ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
