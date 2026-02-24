#!/usr/bin/env python3
"""
Test announcement persistence to prevent duplicate announcements on restart
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from weather_bot import WeatherBot, ANNOUNCE_INTERVAL, ANNOUNCE_TIMESTAMP_FILE


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


def test_no_announcement_on_recent_restart():
    """Test that bot skips announcement on startup if recently announced"""
    print("=" * 70)
    print("TEST 2: Skip Announcement on Recent Restart")
    print("=" * 70)
    
    # Clean up any existing timestamp file
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    
    # Simulate a recent announcement (1 hour ago)
    recent_time = time.time() - (1 * 60 * 60)  # 1 hour ago
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, 
                     weather_channel_idx=1)
    bot._save_last_announce_time(recent_time)
    print(f"  Simulated last announcement: 1 hour ago")
    
    # Simulate the startup announcement logic
    last_announce = bot._get_last_announce_time()
    current_time = time.time()
    time_since_last_announce = current_time - last_announce if last_announce > 0 else ANNOUNCE_INTERVAL + 1
    
    # Check if announcement should be skipped
    should_announce = time_since_last_announce >= ANNOUNCE_INTERVAL
    
    # Should NOT announce (1 hour < 3 hours)
    assert not should_announce, "Should not announce within 3 hours"
    print(f"  ✓ Announcement will be skipped (1 hour < 3 hours)")
    
    # Verify time calculation
    hours_since = time_since_last_announce / 3600
    print(f"  ✓ Time since last announce: {hours_since:.2f} hours")
    assert time_since_last_announce < ANNOUNCE_INTERVAL, "Should be less than 3 hours"
    
    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    print()


def test_announcement_on_old_restart():
    """Test that bot announces on startup if last announcement was > 3 hours ago"""
    print("=" * 70)
    print("TEST 3: Announce on Old Restart")
    print("=" * 70)
    
    # Clean up any existing timestamp file
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    
    # Simulate an old announcement (4 hours ago)
    old_time = time.time() - (4 * 60 * 60)  # 4 hours ago
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True,
                     weather_channel_idx=1)
    bot._save_last_announce_time(old_time)
    print(f"  Simulated last announcement: 4 hours ago")
    
    # Simulate the startup announcement logic
    last_announce = bot._get_last_announce_time()
    current_time = time.time()
    time_since_last_announce = current_time - last_announce if last_announce > 0 else ANNOUNCE_INTERVAL + 1
    
    # Check if announcement should be made
    should_announce = time_since_last_announce >= ANNOUNCE_INTERVAL
    
    # SHOULD announce (4 hours > 3 hours)
    assert should_announce, "Should announce after 3 hours"
    print(f"  ✓ Announcement will be sent (4 hours > 3 hours)")
    
    # Verify time calculation
    hours_since = time_since_last_announce / 3600
    print(f"  ✓ Time since last announce: {hours_since:.2f} hours")
    assert time_since_last_announce >= ANNOUNCE_INTERVAL, "Should be more than 3 hours"
    
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
    
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True,
                     weather_channel_idx=1)
    print(f"  No previous announcement file exists")
    
    # Simulate the startup announcement logic
    last_announce = bot._get_last_announce_time()
    current_time = time.time()
    time_since_last_announce = current_time - last_announce if last_announce > 0 else ANNOUNCE_INTERVAL + 1
    
    # Check if announcement should be made
    should_announce = time_since_last_announce >= ANNOUNCE_INTERVAL
    
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
        test_no_announcement_on_recent_restart()
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
