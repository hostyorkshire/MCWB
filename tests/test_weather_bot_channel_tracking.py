#!/usr/bin/env python3
"""
Test that weather bot tracks channels when sending messages via _send_channel_msg
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from weather_bot import WeatherBot


def test_announcement_tracks_channel():
    """Test that sending announcements tracks the channel"""
    with tempfile.TemporaryDirectory() as tmpdir:
        channels_file = os.path.join(tmpdir, "channels.json")

        # Create weather bot with announcements on channel 1
        bot = WeatherBot(port=None, announce=True, weather_channel_idx=1, debug=False)
        bot.mesh.start()

        # Verify no channels initially
        channels = bot.mesh.get_active_channels()
        assert len(channels) == 0, "Should have no channels initially"

        # Simulate sending announcement (what happens in bot.run())
        try:
            bot._send_channel_msg("Test announcement", bot._announce_channel_idx)
        except AttributeError:
            # Expected - no serial port, but channel should still be tracked
            pass

        # Verify channel is tracked
        channels = bot.mesh.get_active_channels()
        assert len(channels) == 1, f"Should have 1 channel after announcement, got {len(channels)}"
        assert channels[0]["channel_idx"] == 1, f"Channel should be idx 1, got {channels[0]['channel_idx']}"

        # Verify channels.json is saved
        bot.mesh.save_active_channels(channels_file)

        assert os.path.exists(channels_file), "channels.json should exist"

        with open(channels_file) as f:
            data = json.load(f)

        assert len(data["channels"]) == 1, "channels.json should have 1 channel"
        assert data["channels"][0]["channel_idx"] == 1, "Channel idx should be 1"

        bot.mesh.stop()
        print("✓ Test passed: Announcements track channels")


def test_reboot_notification_tracks_channel():
    """Test that sending reboot notifications tracks the channel"""
    with tempfile.TemporaryDirectory() as tmpdir:
        channels_file = os.path.join(tmpdir, "channels.json")

        # Create weather bot with reboot notifications on channel 2
        bot = WeatherBot(port=None, reboot_notify=True, weather_channel_idx=2, debug=False)
        bot.mesh.start()

        # Verify no channels initially
        channels = bot.mesh.get_active_channels()
        assert len(channels) == 0, "Should have no channels initially"

        # Simulate sending reboot notification
        try:
            bot._send_channel_msg("Reboot notification", 2)
        except AttributeError:
            # Expected - no serial port, but channel should still be tracked
            pass

        # Verify channel is tracked
        channels = bot.mesh.get_active_channels()
        assert len(channels) == 1, f"Should have 1 channel after reboot notify, got {len(channels)}"
        assert channels[0]["channel_idx"] == 2, f"Channel should be idx 2, got {channels[0]['channel_idx']}"

        # Verify channels.json is saved
        bot.mesh.save_active_channels(channels_file)

        assert os.path.exists(channels_file), "channels.json should exist"

        with open(channels_file) as f:
            data = json.load(f)

        assert len(data["channels"]) == 1, "channels.json should have 1 channel"
        assert data["channels"][0]["channel_idx"] == 2, "Channel idx should be 2"

        bot.mesh.stop()
        print("✓ Test passed: Reboot notifications track channels")


def test_weather_response_tracks_channel():
    """Test that sending weather responses tracks the channel"""
    with tempfile.TemporaryDirectory() as tmpdir:
        channels_file = os.path.join(tmpdir, "channels.json")

        # Create weather bot
        bot = WeatherBot(port=None, debug=False)
        bot.mesh.start()

        # Verify no channels initially
        channels = bot.mesh.get_active_channels()
        assert len(channels) == 0, "Should have no channels initially"

        # Simulate sending weather response on channel 3
        try:
            bot._send_channel_msg("Weather: 15°C", 3)
        except AttributeError:
            # Expected - no serial port, but channel should still be tracked
            pass

        # Verify channel is tracked
        channels = bot.mesh.get_active_channels()
        assert len(channels) == 1, f"Should have 1 channel after response, got {len(channels)}"
        assert channels[0]["channel_idx"] == 3, f"Channel should be idx 3, got {channels[0]['channel_idx']}"

        # Verify channels.json is saved
        bot.mesh.save_active_channels(channels_file)

        assert os.path.exists(channels_file), "channels.json should exist"

        with open(channels_file) as f:
            data = json.load(f)

        assert len(data["channels"]) == 1, "channels.json should have 1 channel"
        assert data["channels"][0]["channel_idx"] == 3, "Channel idx should be 3"

        bot.mesh.stop()
        print("✓ Test passed: Weather responses track channels")


def test_multiple_channels_tracked():
    """Test that multiple channels are tracked correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        channels_file = os.path.join(tmpdir, "channels.json")

        # Create weather bot
        bot = WeatherBot(port=None, debug=False)
        bot.mesh.start()

        # Send messages on different channels
        for channel_idx in [0, 1, 2]:
            try:
                bot._send_channel_msg(f"Test on channel {channel_idx}", channel_idx)
            except AttributeError:
                pass

        # Verify all channels are tracked
        channels = bot.mesh.get_active_channels()
        assert len(channels) == 3, f"Should have 3 channels, got {len(channels)}"

        tracked_indices = [ch["channel_idx"] for ch in channels]
        assert 0 in tracked_indices, "Channel 0 should be tracked"
        assert 1 in tracked_indices, "Channel 1 should be tracked"
        assert 2 in tracked_indices, "Channel 2 should be tracked"

        # Verify channels.json
        bot.mesh.save_active_channels(channels_file)

        with open(channels_file) as f:
            data = json.load(f)

        assert len(data["channels"]) == 3, "channels.json should have 3 channels"

        bot.mesh.stop()
        print("✓ Test passed: Multiple channels tracked correctly")


if __name__ == "__main__":
    test_announcement_tracks_channel()
    test_reboot_notification_tracks_channel()
    test_weather_response_tracks_channel()
    test_multiple_channels_tracked()
    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)
