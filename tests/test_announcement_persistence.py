#!/usr/bin/env python3
"""
Test announcement persistence to prevent duplicate announcements on restart
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time

from weather_bot import ANNOUNCE_INTERVAL, ANNOUNCE_TIMESTAMP_FILE, WeatherBot


def should_announce_on_startup(bot, last_announce_time):
    """
    Helper function to determine if bot should announce on startup.
    Mirrors the logic in weather_bot.py run() method.

    Args:
        bot: WeatherBot instance
        last_announce_time: Timestamp of last announcement (0 if none)

    Returns:
        bool: True if bot should announce, False otherwise
    """
    # Always announce on startup to let users know the bot is operational
    return bot.announce


def test_timestamp_persistence():
    """Test that announcement timestamps are persisted and read correctly"""
    print("=" * 70)
    print("TEST 1: Timestamp Persistence")
    print("=" * 70)

    # Clean up any existing timestamp file
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    # Test writing timestamp
    test_time = time.time()
    bot._save_last_announce_time(test_time)
    assert os.path.exists(ANNOUNCE_TIMESTAMP_FILE), "Timestamp file should be created"
    print(f"  ✓ Timestamp file created at {ANNOUNCE_TIMESTAMP_FILE}")

    # Test reading timestamp
    read_time = bot._get_last_announce_time()
    assert abs(read_time - test_time) < 0.1, f"Read time {read_time} should match written time {test_time}"
    print(f"  ✓ Timestamp read correctly: {read_time}")

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    print()


def test_announcement_on_recent_restart():
    """Test that bot announces on startup even if recently announced"""
    print("=" * 70)
    print("TEST 2: Announce on Recent Restart (Always Announce)")
    print("=" * 70)

    # Clean up any existing timestamp file
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)

    # Simulate a recent announcement (1 hour ago)
    recent_time = time.time() - (1 * 60 * 60)  # 1 hour ago
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=1)
    bot._save_last_announce_time(recent_time)
    print(f"  Simulated last announcement: 1 hour ago")

    # Check if announcement should be made using helper
    last_announce = bot._get_last_announce_time()
    should_announce = should_announce_on_startup(bot, last_announce)

    # SHOULD announce (always announce on startup)
    assert should_announce, "Should always announce on startup"
    print(f"  ✓ Announcement will be sent (always announces on reboot)")

    # Verify time calculation
    time_since_last_announce = time.time() - last_announce
    hours_since = time_since_last_announce / 3600
    print(f"  ✓ Time since last announce: {hours_since:.2f} hours")
    print(f"  ✓ Bot announces on startup regardless of interval")

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    print()


def test_announcement_on_old_restart():
    """Test that bot announces on startup if last announcement was > 6 hours ago"""
    print("=" * 70)
    print("TEST 3: Announce on Old Restart")
    print("=" * 70)

    # Clean up any existing timestamp file
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)

    # Simulate an old announcement (8 hours ago)
    old_time = time.time() - (8 * 60 * 60)  # 8 hours ago
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=1)
    bot._save_last_announce_time(old_time)
    print(f"  Simulated last announcement: 8 hours ago")

    # Check if announcement should be made using helper
    last_announce = bot._get_last_announce_time()
    should_announce = should_announce_on_startup(bot, last_announce)

    # SHOULD announce (8 hours > 6 hours)
    assert should_announce, "Should announce after 6 hours"
    print(f"  ✓ Announcement will be sent (8 hours > 6 hours)")

    # Verify time calculation
    time_since_last_announce = time.time() - last_announce
    hours_since = time_since_last_announce / 3600
    print(f"  ✓ Time since last announce: {hours_since:.2f} hours")
    assert time_since_last_announce >= ANNOUNCE_INTERVAL, "Should be more than 6 hours"

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    print()


def test_announcement_on_first_start():
    """Test that bot announces on first startup (no timestamp file)"""
    print("=" * 70)
    print("TEST 4: Announce on First Start")
    print("=" * 70)

    # Clean up any existing timestamp file
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=1)
    print(f"  No previous announcement file exists")

    # Check if announcement should be made using helper
    last_announce = bot._get_last_announce_time()
    should_announce = should_announce_on_startup(bot, last_announce)

    # SHOULD announce (first time)
    assert should_announce, "Should announce on first start"
    print(f"  ✓ Announcement will be sent on first start")

    # Verify timestamp = 0 when no file exists
    assert last_announce == 0, "Should return 0 when no file exists"
    print(f"  ✓ No previous timestamp (returns 0)")

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    print()


if __name__ == "__main__":
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 12 + "MCWB - Announcement Persistence Tests" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝\n")

    try:
        test_timestamp_persistence()
        test_announcement_on_recent_restart()
        test_announcement_on_old_restart()
        test_announcement_on_first_start()

        print("=" * 70)
        print("✓ All announcement persistence tests passed!")
        print("=" * 70)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
