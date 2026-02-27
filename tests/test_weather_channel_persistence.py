#!/usr/bin/env python3
"""
Test weather channel persistence to ensure bot announces on correct channel after restart
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from weather_bot import ANNOUNCE_MESSAGE, WEATHER_CHANNEL_FILE, WeatherBot

# Path to the active channels JSON file used by MeshCore
CHANNELS_FILE = Path(__file__).parent.parent / "logs" / "channels.json"


def test_weather_channel_persistence():
    """Test that detected weather channel is persisted and loaded on restart"""
    print("=" * 70)
    print("TEST 1: Weather Channel Persistence")
    print("=" * 70)

    # Clean up any existing files
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)

    # Create bot and simulate channel detection
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    # Simulate detection of #weather on channel_idx=2
    test_channel_idx = 2
    bot._save_weather_channel(test_channel_idx)
    assert WEATHER_CHANNEL_FILE.exists(), "Weather channel file should be created"
    print(f"  ✓ Weather channel file created at {WEATHER_CHANNEL_FILE}")

    # Read it back
    loaded_channel = bot._get_persisted_weather_channel()
    assert loaded_channel == test_channel_idx, f"Loaded channel {loaded_channel} should match saved {test_channel_idx}"
    print(f"  ✓ Weather channel read correctly: {loaded_channel}")

    # Clean up
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)
    print()


def test_startup_with_persisted_channel():
    """Test that bot uses persisted channel on startup when no radio active channels exist"""
    print("=" * 70)
    print("TEST 2: Startup with Persisted Channel")
    print("=" * 70)

    # Clean up both persistence files so radio active channels don't interfere
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)
    if CHANNELS_FILE.exists():
        os.remove(CHANNELS_FILE)

    # First session: detect weather channel on channel_idx=3
    bot1 = WeatherBot(node_id="test_bot", debug=False, announce=True)
    detected_channel = 3
    bot1._save_weather_channel(detected_channel)
    print(f"  Session 1: Detected weather channel on channel_idx={detected_channel}")

    # Second session: create new bot instance (simulating restart)
    bot2 = WeatherBot(node_id="test_bot", debug=False, announce=True)

    # Verify that bot2 loaded the persisted channel
    assert bot2._announce_channel_idx == detected_channel, \
        f"Bot should load persisted channel {detected_channel}, but got {bot2._announce_channel_idx}"
    assert bot2._weather_channel_detected is True, "Bot should mark channel as detected"
    print(f"  Session 2: Loaded persisted channel_idx={bot2._announce_channel_idx}")
    print("  ✓ Bot will announce on correct channel after restart")

    # Clean up
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)
    if CHANNELS_FILE.exists():
        os.remove(CHANNELS_FILE)
    print()


def test_startup_announcement_uses_persisted_channel():
    """Test that startup announcement goes to persisted weather channel when no radio active channels exist"""
    print("=" * 70)
    print("TEST 3: Startup Announcement Uses Persisted Channel")
    print("=" * 70)

    # Clean up both persistence files so radio active channels don't interfere
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)
    if CHANNELS_FILE.exists():
        os.remove(CHANNELS_FILE)

    # Simulate persisted channel from previous session
    persisted_channel = 2
    bot_temp = WeatherBot(node_id="test_bot", debug=False, announce=True)
    bot_temp._save_weather_channel(persisted_channel)
    print(f"  Previous session: Weather channel was channel_idx={persisted_channel}")

    # Create new bot instance (simulating restart with announcement)
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    # Mock serial connection and _send_channel_msg to track announcements
    sent_announcements = []

    def mock_send_channel_msg(msg, channel_idx):
        if msg == ANNOUNCE_MESSAGE:
            sent_announcements.append({"msg": msg, "channel_idx": channel_idx})

    with patch.object(bot, "_connect", return_value=True), \
         patch.object(bot, "_send_cmd"), \
         patch.object(bot, "_send_channel_msg", side_effect=mock_send_channel_msg):

        # Simulate startup announcement (from run() method)
        bot._running = True
        if bot.announce:
            bot._send_channel_msg(ANNOUNCE_MESSAGE, bot._announce_channel_idx)
        bot._running = False

    # Verify announcement went to persisted channel
    assert len(sent_announcements) == 1, f"Should send one announcement, got {len(sent_announcements)}"
    assert sent_announcements[0]["channel_idx"] == persisted_channel, \
        f"Announcement should go to channel {persisted_channel}, got {sent_announcements[0]['channel_idx']}"
    print(f"  ✓ Startup announcement sent to persisted channel_idx={persisted_channel}")

    # Clean up
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)
    if CHANNELS_FILE.exists():
        os.remove(CHANNELS_FILE)
    print()


def test_explicit_config_overrides_persisted():
    """Test that explicit --weather-channel-idx overrides persisted channel"""
    print("=" * 70)
    print("TEST 4: Explicit Config Overrides Persisted Channel")
    print("=" * 70)

    # Clean up
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)

    # Simulate persisted channel
    persisted_channel = 2
    bot_temp = WeatherBot(node_id="test_bot", debug=False, announce=True)
    bot_temp._save_weather_channel(persisted_channel)
    print(f"  Persisted channel: channel_idx={persisted_channel}")

    # Create bot with explicit weather_channel_idx
    explicit_channel = 5
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=explicit_channel)

    # Verify explicit config takes precedence
    assert bot._announce_channel_idx == explicit_channel, \
        f"Explicit config should override persisted channel, expected {explicit_channel}, got {bot._announce_channel_idx}"
    print(f"  Explicit config: channel_idx={explicit_channel}")
    print("  ✓ Explicit config takes precedence over persisted channel")

    # Clean up
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)
    print()


def test_no_persistence_file_defaults_to_zero():
    """Test that bot defaults to channel 0 when no persistence files exist"""
    print("=" * 70)
    print("TEST 5: No Persistence File - Default to Channel 0")
    print("=" * 70)

    # Clean up both persistence files
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)
    if CHANNELS_FILE.exists():
        os.remove(CHANNELS_FILE)

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    # Verify defaults to channel 0
    assert bot._announce_channel_idx == 0, \
        f"Should default to channel 0, got {bot._announce_channel_idx}"
    print("  ✓ Bot defaults to channel_idx=0 (first startup)")

    # Clean up
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)
    if CHANNELS_FILE.exists():
        os.remove(CHANNELS_FILE)
    print()


def test_auto_detection_persists_channel():
    """Test that auto-detection persists the detected channel"""
    print("=" * 70)
    print("TEST 6: Auto-Detection Persists Channel")
    print("=" * 70)

    # Clean up
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    # Simulate receiving a message with #weather hashtag on channel 4
    detected_channel = 4
    bot._detect_channel_name("#weather channel announcement", detected_channel)

    # Verify channel was persisted
    assert WEATHER_CHANNEL_FILE.exists(), "Weather channel should be persisted after detection"
    loaded = bot._get_persisted_weather_channel()
    assert loaded == detected_channel, \
        f"Persisted channel should be {detected_channel}, got {loaded}"
    print(f"  ✓ Auto-detected channel_idx={detected_channel} was persisted")

    # Clean up
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)
    print()


if __name__ == "__main__":
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "MCWB - Weather Channel Persistence Tests" + " " * 17 + "║")
    print("╚" + "=" * 68 + "╝\n")

    try:
        test_weather_channel_persistence()
        test_startup_with_persisted_channel()
        test_startup_announcement_uses_persisted_channel()
        test_explicit_config_overrides_persisted()
        test_no_persistence_file_defaults_to_zero()
        test_auto_detection_persists_channel()

        print("=" * 70)
        print("✓ All weather channel persistence tests passed!")
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
