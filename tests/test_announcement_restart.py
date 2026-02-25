#!/usr/bin/env python3
"""
Integration test for announcement persistence during bot restart
Tests the full startup sequence with and without recent announcements
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import threading
import time
from unittest.mock import MagicMock, patch

from weather_bot import ANNOUNCE_INTERVAL, ANNOUNCE_MESSAGE, ANNOUNCE_TIMESTAMP_FILE, WeatherBot


def simulate_startup_announcement_logic(bot):
    """
    Helper to simulate the startup announcement logic from run() method.

    Args:
        bot: WeatherBot instance with mocked _send_channel_msg

    Returns:
        bool: True if announcement was sent, False otherwise
    """
    last_announce = bot._get_last_announce_time()
    current_time = time.time()
    # Add 1 to ensure first startup always announces (when last_announce == 0)
    time_since_last_announce = current_time - last_announce if last_announce > 0 else ANNOUNCE_INTERVAL + 1

    if bot.announce and time_since_last_announce >= ANNOUNCE_INTERVAL:
        bot._send_channel_msg(ANNOUNCE_MESSAGE, bot._announce_channel_idx)
        last_announce = current_time
        bot._save_last_announce_time(last_announce)
        return True
    elif bot.announce:
        remaining = ANNOUNCE_INTERVAL - time_since_last_announce
        msg = f"Skipping startup announcement (last announced {int(time_since_last_announce/60)} minutes ago, {int(remaining/60)} minutes until next)"
        print(f"  {msg}")
        return False
    return False


def test_startup_with_recent_announcement():
    """Test full startup sequence when announcement was made recently (< 3 hours)"""
    print("=" * 70)
    print("TEST: Full Startup with Recent Announcement")
    print("=" * 70)

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)

    # Simulate recent announcement (30 minutes ago)
    recent_time = time.time() - (30 * 60)  # 30 minutes ago

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=1)
    bot._save_last_announce_time(recent_time)

    print(f"  Simulated last announcement: 30 minutes ago")
    print(f"  Starting bot with announcements enabled...")

    # Mock serial connection and _send_channel_msg to avoid hardware dependency
    sent_announcements = []

    def mock_send_channel_msg(msg, channel_idx):
        if msg == ANNOUNCE_MESSAGE:
            sent_announcements.append({"msg": msg, "channel_idx": channel_idx, "time": time.time()})

    with patch.object(bot, "_connect", return_value=True), patch.object(bot, "_send_cmd"), patch.object(
        bot, "_send_channel_msg", side_effect=mock_send_channel_msg
    ):

        # Simulate the startup code from run() method using helper
        bot._running = True
        announced = simulate_startup_announcement_logic(bot)
        bot._running = False

    # Should NOT have sent announcement
    assert not announced, "Should not announce on startup"
    assert len(sent_announcements) == 0, f"Should not announce on startup (sent {len(sent_announcements)})"
    print(f"  ✓ No announcement sent on startup (30 min < 3 hours)")

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    print()


def test_startup_with_old_announcement():
    """Test full startup sequence when announcement was made long ago (> 3 hours)"""
    print("=" * 70)
    print("TEST: Full Startup with Old Announcement")
    print("=" * 70)

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)

    # Simulate old announcement (5 hours ago)
    old_time = time.time() - (5 * 60 * 60)  # 5 hours ago

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=1)
    bot._save_last_announce_time(old_time)

    print(f"  Simulated last announcement: 5 hours ago")
    print(f"  Starting bot with announcements enabled...")

    # Mock serial connection and _send_channel_msg to avoid hardware dependency
    sent_announcements = []

    def mock_send_channel_msg(msg, channel_idx):
        if msg == ANNOUNCE_MESSAGE:
            sent_announcements.append({"msg": msg, "channel_idx": channel_idx, "time": time.time()})

    with patch.object(bot, "_connect", return_value=True), patch.object(bot, "_send_cmd"), patch.object(
        bot, "_send_channel_msg", side_effect=mock_send_channel_msg
    ):

        # Simulate the startup code from run() method using helper
        bot._running = True
        announced = simulate_startup_announcement_logic(bot)
        bot._running = False

    # SHOULD have sent announcement
    assert announced, "Should announce on startup"
    assert len(sent_announcements) == 1, f"Should announce on startup (sent {len(sent_announcements)})"
    print(f"  ✓ Announcement sent on startup (5 hours > 3 hours)")

    # Verify timestamp was saved
    new_timestamp = bot._get_last_announce_time()
    assert new_timestamp > old_time, "New timestamp should be saved"
    print(f"  ✓ Timestamp updated after announcement")

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    print()


def test_startup_no_previous_announcement():
    """Test full startup sequence with no previous announcement file"""
    print("=" * 70)
    print("TEST: First Startup (No Previous Announcement)")
    print("=" * 70)

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=1)

    print(f"  No previous announcement file")
    print(f"  Starting bot with announcements enabled...")

    # Mock serial connection and _send_channel_msg to avoid hardware dependency
    sent_announcements = []

    def mock_send_channel_msg(msg, channel_idx):
        if msg == ANNOUNCE_MESSAGE:
            sent_announcements.append({"msg": msg, "channel_idx": channel_idx, "time": time.time()})

    with patch.object(bot, "_connect", return_value=True), patch.object(bot, "_send_cmd"), patch.object(
        bot, "_send_channel_msg", side_effect=mock_send_channel_msg
    ):

        # Simulate the startup code from run() method using helper
        bot._running = True
        announced = simulate_startup_announcement_logic(bot)
        bot._running = False

    # SHOULD have sent announcement (first time)
    assert announced, "Should announce on first startup"
    assert len(sent_announcements) == 1, f"Should announce on first startup (sent {len(sent_announcements)})"
    print(f"  ✓ Announcement sent on first startup")

    # Verify timestamp was saved
    new_timestamp = bot._get_last_announce_time()
    assert new_timestamp > 0, "Timestamp should be saved"
    print(f"  ✓ Timestamp saved after announcement")

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    print()


if __name__ == "__main__":
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "MCWB - Announcement Restart Integration Tests" + " " * 12 + "║")
    print("╚" + "=" * 68 + "╝\n")

    try:
        test_startup_with_recent_announcement()
        test_startup_with_old_announcement()
        test_startup_no_previous_announcement()

        print("=" * 70)
        print("✓ All integration tests passed!")
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
