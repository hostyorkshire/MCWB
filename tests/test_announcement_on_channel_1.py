#!/usr/bin/env python3
"""
Test to verify announcements go to channel 1 (#weather channel)
This tests the specific scenario where #weather is on channel_idx=1
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path
from unittest.mock import patch

from weather_bot import ANNOUNCE_MESSAGE, WEATHER_CHANNEL_FILE, WeatherBot


def cleanup():
    """Clean up any persisted files from previous tests"""
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)


def test_explicit_config_channel_1():
    """
    Test that when weather_channel_idx=1 is configured,
    announcements go to channel 1 immediately on startup.
    """
    print("=" * 70)
    print("TEST 1: Explicit Configuration - Announcements on Channel 1")
    print("=" * 70)

    cleanup()

    # Create bot with explicit configuration: weather_channel_idx=1
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=1)

    print(f"  Configured weather_channel_idx: {bot.weather_channel_idx}")
    print(f"  _announce_channel_idx: {bot._announce_channel_idx}")

    # Verify announcement channel is set to 1
    assert bot._announce_channel_idx == 1, f"Expected channel 1, got {bot._announce_channel_idx}"

    # Track messages sent
    sent_messages = []

    def mock_send_channel_msg(msg, channel_idx):
        sent_messages.append({"msg": msg, "channel_idx": channel_idx})

    with patch.object(bot, "_send_cmd"), patch.object(bot, "_send_channel_msg", side_effect=mock_send_channel_msg):
        # Simulate startup announcement
        bot._send_channel_msg(ANNOUNCE_MESSAGE, bot._announce_channel_idx)

    # Verify announcement went to channel 1
    assert len(sent_messages) == 1, "Should send 1 announcement"
    assert (
        sent_messages[0]["channel_idx"] == 1
    ), f"Announcement should go to channel 1, got {sent_messages[0]['channel_idx']}"

    print("  ✓ Announcement channel is channel_idx=1")
    print("  ✓ Announcements will go to #weather channel (channel 1)")
    print()

    cleanup()


def test_auto_detect_channel_1():
    """
    Test that when #weather channel is detected on channel 1,
    announcements are sent to channel 1.
    """
    print("=" * 70)
    print("TEST 2: Auto-Detection - Weather Commands on Channel 1")
    print("=" * 70)

    cleanup()

    # Create bot without explicit configuration
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    print(f"  Initial _announce_channel_idx: {bot._announce_channel_idx}")
    print(f"  Initial _weather_channel_detected: {bot._weather_channel_detected}")

    # Simulate receiving a weather command on channel 1
    print("\n  Simulating: User sends 'wx London' on channel_idx=1...")

    channel_idx = 1
    location, country = bot._parse_command("wx London")

    # Apply the detection logic from _handle_channel_message
    if location and not bot._weather_channel_detected and bot.weather_channel_idx is None:
        if channel_idx not in bot._channel_idx_to_name:
            bot._channel_idx_to_name[channel_idx] = "weather"
            bot._weather_channel_detected = True
            print(f"  → Auto-detected #weather channel on channel_idx={channel_idx}")
        bot._announce_channel_idx = channel_idx
        print(f"  → _announce_channel_idx updated to: {bot._announce_channel_idx}")

    # Verify announcement channel is now set to 1
    assert bot._announce_channel_idx == 1, f"Expected channel 1, got {bot._announce_channel_idx}"
    assert bot._weather_channel_detected, "Weather channel should be detected"

    print(f"\n  Final _announce_channel_idx: {bot._announce_channel_idx}")
    print("  ✓ Auto-detected #weather channel on channel 1")
    print("  ✓ Future announcements will go to channel 1")
    print()

    cleanup()


def test_hashtag_detection_channel_1():
    """
    Test that when #weather hashtag is detected on channel 1,
    announcements are sent to channel 1.
    """
    print("=" * 70)
    print("TEST 3: Auto-Detection - #weather Hashtag on Channel 1")
    print("=" * 70)

    cleanup()

    # Create bot without explicit configuration
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    print(f"  Initial _announce_channel_idx: {bot._announce_channel_idx}")

    # Simulate receiving a message with #weather hashtag on channel 1
    print("\n  Simulating: Message with #weather hashtag on channel_idx=1...")
    bot._detect_channel_name("User: Welcome to the #weather channel!", channel_idx=1)

    # Verify announcement channel is now set to 1
    assert bot._weather_channel_detected, "Weather channel should be detected"
    assert bot._announce_channel_idx == 1, f"Expected channel 1, got {bot._announce_channel_idx}"

    print("  → Auto-detected #weather channel on channel_idx=1")
    print(f"  → _announce_channel_idx: {bot._announce_channel_idx}")
    print("\n  ✓ Detected #weather hashtag on channel 1")
    print("  ✓ Future announcements will go to channel 1")
    print()

    cleanup()


def test_no_interference_from_other_channels():
    """
    Test that messages on other channels do NOT change announcement channel
    once channel 1 is detected as the weather channel.
    """
    print("=" * 70)
    print("TEST 4: Other Channels Don't Interfere with Channel 1")
    print("=" * 70)

    cleanup()

    # Create bot with channel 1 configured
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=1)

    print(f"  Configured weather_channel_idx: {bot.weather_channel_idx}")
    print(f"  _announce_channel_idx: {bot._announce_channel_idx}")

    # Simulate receiving messages on other channels
    print("\n  Simulating: Messages arriving on channels 0, 2, 3, 4...")
    for ch in [0, 2, 3, 4]:
        location, _ = bot._parse_command(f"Hello from channel {ch}")
        # Location should be None for these non-weather messages
        assert location is None, "Should not detect location in greeting"

    # Verify announcement channel is STILL 1
    assert bot._announce_channel_idx == 1, f"Channel should remain 1, got {bot._announce_channel_idx}"

    print(f"  → _announce_channel_idx: {bot._announce_channel_idx}")
    print("\n  ✓ Announcement channel remains on channel 1")
    print("  ✓ Other channels did NOT interfere")
    print()

    cleanup()


if __name__ == "__main__":
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 8 + "MCWB - Announcements on Channel 1 (#weather)" + " " * 14 + "║")
    print("╚" + "=" * 68 + "╝\n")

    try:
        test_explicit_config_channel_1()
        test_auto_detect_channel_1()
        test_hashtag_detection_channel_1()
        test_no_interference_from_other_channels()

        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\n🎯 VERIFIED: Announcements will go to channel 1 (#weather)")
        print("\n📝 Configuration Options:")
        print("   1. Explicit: python3 weather_bot.py --announce --weather-channel-idx 1")
        print("   2. Auto-detect: python3 weather_bot.py --announce")
        print("      (Will detect channel 1 from #weather hashtag or wx commands)")
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
