#!/usr/bin/env python3
"""
Test to verify announcements are sent to the correct weather channel
Ensures announcements ONLY go to the configured weather channel, not other channels
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from pathlib import Path
from unittest.mock import patch

from weather_bot import ANNOUNCE_INTERVAL, ANNOUNCE_MESSAGE, ANNOUNCE_TIMESTAMP_FILE, WeatherBot

# Path to the active channels JSON file used by MeshCore
CHANNELS_FILE = Path(__file__).parent.parent / "logs" / "channels.json"


def test_announcement_goes_to_weather_channel():
    """Test that startup announcement is sent to the configured weather channel"""
    print("=" * 70)
    print("TEST: Announcement Sent to Weather Channel Only")
    print("=" * 70)

    # Clean up any existing timestamp file
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)

    # Simulate old announcement (past ANNOUNCE_INTERVAL) so announcement will be sent
    old_time = time.time() - (ANNOUNCE_INTERVAL + 3600)

    # Create bot with weather_channel_idx=1 (typical #weather channel)
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=1)
    bot._save_last_announce_time(old_time)

    print("  Configured weather_channel_idx: 1")
    print(f"  Internal _announce_channel_idx: {bot._announce_channel_idx}")
    print("  Simulated last announcement: past ANNOUNCE_INTERVAL")

    # Track all messages sent with their channel indices
    sent_messages = []

    def mock_send_channel_msg(msg, channel_idx):
        sent_messages.append({"msg": msg, "channel_idx": channel_idx, "time": time.time()})
        print(f"  → Message sent to channel_idx={channel_idx}: {msg[:50]}...")

    with patch.object(bot, "_connect", return_value=True), patch.object(bot, "_send_cmd"), patch.object(
        bot, "_send_channel_msg", side_effect=mock_send_channel_msg
    ):
        # Get last announce time and simulate startup announcement logic
        last_announce = bot._get_last_announce_time()
        current_time = time.time()
        time_since_last_announce = current_time - last_announce if last_announce > 0 else ANNOUNCE_INTERVAL + 1

        if bot.announce and time_since_last_announce >= ANNOUNCE_INTERVAL:
            bot._send_channel_msg(ANNOUNCE_MESSAGE, bot._announce_channel_idx)
            last_announce = current_time
            bot._save_last_announce_time(last_announce)

    # Verify announcement was sent to correct channel
    assert len(sent_messages) == 1, f"Expected 1 announcement, got {len(sent_messages)}"
    announcement = sent_messages[0]

    assert (
        announcement["channel_idx"] == 1
    ), f"Announcement should be sent to channel_idx=1, but was sent to {announcement['channel_idx']}"
    assert announcement["msg"] == ANNOUNCE_MESSAGE, "Announcement should contain correct message"

    print("  ✓ Announcement sent to correct channel (channel_idx=1)")
    print("  ✓ Announcement message is correct")

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    print()


def test_announcement_channel_not_default():
    """Test that announcements don't go to default channel (channel_idx=0) when weather channel is configured"""
    print("=" * 70)
    print("TEST: Announcement NOT Sent to Default Channel")
    print("=" * 70)

    # Clean up any existing timestamp file
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)

    # Simulate old announcement to trigger announcement on startup
    old_time = time.time() - (ANNOUNCE_INTERVAL + 3600)

    # Create bot with weather_channel_idx=2 (NOT default channel)
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=2)
    bot._save_last_announce_time(old_time)

    print("  Configured weather_channel_idx: 2")
    print("  Testing that announcement does NOT go to channel_idx=0")

    # Track all messages sent
    sent_messages = []

    def mock_send_channel_msg(msg, channel_idx):
        sent_messages.append({"msg": msg, "channel_idx": channel_idx})

    with patch.object(bot, "_connect", return_value=True), patch.object(bot, "_send_cmd"), patch.object(
        bot, "_send_channel_msg", side_effect=mock_send_channel_msg
    ):
        # Simulate startup announcement
        last_announce = bot._get_last_announce_time()
        current_time = time.time()
        time_since_last_announce = current_time - last_announce if last_announce > 0 else ANNOUNCE_INTERVAL + 1

        if bot.announce and time_since_last_announce >= ANNOUNCE_INTERVAL:
            bot._send_channel_msg(ANNOUNCE_MESSAGE, bot._announce_channel_idx)

    # Verify announcement was NOT sent to default channel
    assert len(sent_messages) == 1, f"Expected 1 announcement, got {len(sent_messages)}"
    announcement = sent_messages[0]

    assert (
        announcement["channel_idx"] == 2
    ), f"Announcement should be sent to channel_idx=2, got {announcement['channel_idx']}"
    assert announcement["channel_idx"] != 0, "Announcement should NOT be sent to default channel (idx=0)"

    print("  ✓ Announcement sent to channel_idx=2 (NOT default)")
    print("  ✓ Default channel (idx=0) correctly avoided")

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    print()


def test_announcement_channel_defaults_to_zero_when_not_configured():
    """Test that when weather_channel_idx is not configured and no channel history exists, announcements default to channel_idx=0"""
    print("=" * 70)
    print("TEST: Announcement Defaults to Channel 0 When Not Configured")
    print("=" * 70)

    # Clean up any existing timestamp and channel files
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    if CHANNELS_FILE.exists():
        os.remove(CHANNELS_FILE)

    # Simulate old announcement
    old_time = time.time() - (ANNOUNCE_INTERVAL + 3600)

    # Create bot WITHOUT weather_channel_idx configured
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)
    bot._save_last_announce_time(old_time)

    print(f"  weather_channel_idx: {bot.weather_channel_idx} (not configured)")
    print(f"  _announce_channel_idx: {bot._announce_channel_idx}")

    # Track all messages sent
    sent_messages = []

    def mock_send_channel_msg(msg, channel_idx):
        sent_messages.append({"msg": msg, "channel_idx": channel_idx})

    with patch.object(bot, "_connect", return_value=True), patch.object(bot, "_send_cmd"), patch.object(
        bot, "_send_channel_msg", side_effect=mock_send_channel_msg
    ):
        # Simulate startup announcement
        last_announce = bot._get_last_announce_time()
        current_time = time.time()
        time_since_last_announce = current_time - last_announce if last_announce > 0 else ANNOUNCE_INTERVAL + 1

        if bot.announce and time_since_last_announce >= ANNOUNCE_INTERVAL:
            bot._send_channel_msg(ANNOUNCE_MESSAGE, bot._announce_channel_idx)

    # When not configured, should default to channel_idx=0
    assert len(sent_messages) == 1, f"Expected 1 announcement, got {len(sent_messages)}"
    announcement = sent_messages[0]

    assert (
        announcement["channel_idx"] == 0
    ), f"Announcement should default to channel_idx=0, got {announcement['channel_idx']}"

    print("  ✓ Without configuration, announcement defaults to channel_idx=0")
    print("  ⚠️  WARNING: This may not be the #weather channel!")

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
    if CHANNELS_FILE.exists():
        os.remove(CHANNELS_FILE)
    print()


if __name__ == "__main__":
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 12 + "MCWB - Announcement Channel Tests" + " " * 21 + "║")
    print("╚" + "=" * 68 + "╝\n")

    try:
        test_announcement_goes_to_weather_channel()
        test_announcement_channel_not_default()
        test_announcement_channel_defaults_to_zero_when_not_configured()

        print("=" * 70)
        print("✓ All announcement channel tests passed!")
        print("=" * 70)
        print("\n⚠️  IMPORTANT: For announcements to go to #weather channel,")
        print("   the service must be configured with --weather-channel-idx flag!")
        print("   Example: --weather-channel-idx 1")
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
