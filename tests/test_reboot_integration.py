#!/usr/bin/env python3
"""
Integration test for reboot notification functionality
Tests the complete flow of detecting and sending reboot notifications
"""

import os
import sys
import time
from unittest.mock import MagicMock, Mock, patch

from weather_bot import REBOOT_NOTIFY_MESSAGE, STATE_FILE, WeatherBot


def test_integration_first_run():
    """Test first run scenario - no notification should be sent"""
    print("\n" + "=" * 60)
    print("Integration Test 1: First Run (No Reboot)")
    print("=" * 60)

    # Clean up state file
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

    # Create bot with reboot notifications enabled
    bot = WeatherBot(debug=True, reboot_notify=True, weather_channel_idx=1)

    # Mock serial connection to avoid hardware dependency
    with patch.object(bot, "_connect") as mock_connect:
        mock_connect.return_value = True
        bot._ser = Mock()
        bot._ser.is_open = False  # Prevent listener thread from running

        # Mock the channel message send method
        with patch.object(bot, "_send_channel_msg") as mock_send:
            # Simulate the initialization sequence from run()
            bot._send_reboot_notification()
            bot._mark_running()

            # Verify no notification was sent on first run
            mock_send.assert_not_called()
            print("✓ First run: No reboot notification sent")

    # Verify state file was created
    assert os.path.exists(STATE_FILE), "State file should be created"
    print("✓ State file created successfully")

    print("\n✓ Integration Test 1 PASSED\n")


def test_integration_restart():
    """Test restart scenario - notification should be sent"""
    print("=" * 60)
    print("Integration Test 2: Restart (After First Run)")
    print("=" * 60)

    # Ensure state file exists (from previous run)
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            f.write(f"{int(time.time())}\n")

    # Create bot with reboot notifications enabled
    bot = WeatherBot(debug=True, reboot_notify=True, weather_channel_idx=1)

    # Mock serial connection
    with patch.object(bot, "_connect") as mock_connect:
        mock_connect.return_value = True
        bot._ser = Mock()
        bot._ser.is_open = False  # Prevent listener thread from running

        # Mock the channel message send method
        with patch.object(bot, "_send_channel_msg") as mock_send:
            # Simulate the initialization sequence from run()
            bot._send_reboot_notification()
            bot._mark_running()

            # Verify notification was sent on restart
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == REBOOT_NOTIFY_MESSAGE, "Should send reboot message"
            assert call_args[0][1] == 1, "Should send on channel 1"
            print(f"✓ Restart: Reboot notification sent: '{REBOOT_NOTIFY_MESSAGE}'")
            print("✓ Notification sent on channel_idx=1")

    print("\n✓ Integration Test 2 PASSED\n")


def test_integration_disabled():
    """Test that notifications are not sent when disabled"""
    print("=" * 60)
    print("Integration Test 3: Restart with Notifications Disabled")
    print("=" * 60)

    # Ensure state file exists (simulating a restart)
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            f.write(f"{int(time.time())}\n")

    # Create bot WITHOUT reboot notifications enabled
    bot = WeatherBot(debug=True, reboot_notify=False, weather_channel_idx=1)

    # Mock serial connection
    with patch.object(bot, "_connect") as mock_connect:
        mock_connect.return_value = True
        bot._ser = Mock()
        bot._ser.is_open = False

        # Mock the channel message send method
        with patch.object(bot, "_send_channel_msg") as mock_send:
            # Simulate the initialization sequence from run()
            bot._send_reboot_notification()
            bot._mark_running()

            # Verify no notification was sent when feature is disabled
            mock_send.assert_not_called()
            print("✓ Notifications disabled: No message sent")

    print("\n✓ Integration Test 3 PASSED\n")


def test_integration_multiple_restarts():
    """Test multiple restart cycles"""
    print("=" * 60)
    print("Integration Test 4: Multiple Restart Cycles")
    print("=" * 60)

    # Clean up
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

    restart_count = 0

    for i in range(3):
        print(f"\n--- Cycle {i+1} ---")

        bot = WeatherBot(debug=False, reboot_notify=True, weather_channel_idx=1)

        with patch.object(bot, "_connect") as mock_connect:
            mock_connect.return_value = True
            bot._ser = Mock()
            bot._ser.is_open = False

            with patch.object(bot, "_send_channel_msg") as mock_send:
                is_reboot = bot._is_reboot()
                bot._send_reboot_notification()
                bot._mark_running()

                if is_reboot:
                    restart_count += 1
                    mock_send.assert_called_once()
                    print(f"✓ Cycle {i+1}: Restart detected, notification sent")
                else:
                    mock_send.assert_not_called()
                    print(f"✓ Cycle {i+1}: First run, no notification")

    # We should have detected 2 restarts (cycles 2 and 3)
    assert restart_count == 2, f"Expected 2 restarts, got {restart_count}"
    print(f"\n✓ Correctly detected {restart_count} restarts out of 3 cycles")
    print("\n✓ Integration Test 4 PASSED\n")


def main():
    """Run integration tests"""
    print("╔" + "=" * 60 + "╗")
    print("║  REBOOT NOTIFICATION - INTEGRATION TESTS              ║")
    print("╚" + "=" * 60 + "╝")

    try:
        test_integration_first_run()
        test_integration_restart()
        test_integration_disabled()
        test_integration_multiple_restarts()

        # Clean up
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        print("=" * 60)
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
