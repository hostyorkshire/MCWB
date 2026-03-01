#!/usr/bin/env python3
"""
Integration test: Verify bot announces on correct channel after restart
This simulates the real-world scenario described in the issue
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock, patch

from weather_bot import ANNOUNCE_MESSAGE, WEATHER_CHANNEL_FILE, WeatherBot


def test_complete_restart_scenario():
    """
    Simulates the complete scenario:
    1. Bot starts for first time (announces on channel 0)
    2. User sends message on #weather channel (channel_idx=1)
    3. Bot detects and persists channel
    4. Bot restarts (simulating reboot)
    5. Bot announces on channel 1 (#weather) on startup
    """
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: Bot Announcement on Startup/Reboot")
    print("=" * 80)

    # Clean up
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)

    # PHASE 1: First startup
    print("\n[PHASE 1: First Startup]")
    print("  Creating bot for the first time...")
    sent_messages = []

    def track_messages(msg, channel_idx):
        sent_messages.append({"msg": msg, "channel": channel_idx})
        print(f"  📤 Message sent to channel_idx={channel_idx}: {msg[:50]}...")

    bot1 = WeatherBot(node_id="test_bot", debug=False, announce=True)

    with patch.object(bot1, "_send_channel_msg", side_effect=track_messages):
        # Simulate startup announcement
        if bot1.announce:
            bot1._send_channel_msg(ANNOUNCE_MESSAGE, bot1._announce_channel_idx)

    assert len(sent_messages) == 1, "Should send one startup announcement"
    assert sent_messages[0]["channel"] == 0, "First startup should announce on channel 0 (default)"
    print("  ✓ First startup announcement sent to channel_idx=0 (default)")

    # PHASE 2: User interaction - weather request on #weather channel
    print("\n[PHASE 2: User Activity]")
    print("  User sends 'WX London' on #weather channel (channel_idx=1)...")

    # Simulate receiving a message with #weather hashtag
    bot1._detect_channel_name("Message from #weather channel", 1)

    assert bot1._announce_channel_idx == 1, "Bot should update announce channel to 1"
    assert bot1._weather_channel_detected, "Bot should mark channel as detected"
    assert WEATHER_CHANNEL_FILE.exists(), "Channel should be persisted"
    print("  ✓ Bot detected #weather on channel_idx=1")
    print(f"  ✓ Channel persisted to {WEATHER_CHANNEL_FILE}")

    # PHASE 3: Bot restart (simulating reboot)
    print("\n[PHASE 3: Bot Restart (Reboot)]")
    print("  Simulating system reboot - creating new bot instance...")

    sent_messages.clear()
    bot2 = WeatherBot(node_id="test_bot", debug=False, announce=True)

    with patch.object(bot2, "_send_channel_msg", side_effect=track_messages):
        # Simulate startup announcement
        if bot2.announce:
            bot2._send_channel_msg(ANNOUNCE_MESSAGE, bot2._announce_channel_idx)

    assert len(sent_messages) == 1, "Should send one startup announcement"
    assert sent_messages[0]["channel"] == 1, "Restart should announce on channel 1 (#weather)"
    print("  ✓ Bot loaded persisted channel: channel_idx=1")
    print("  ✓ Startup announcement sent to channel_idx=1 (#weather)")

    # Clean up
    if WEATHER_CHANNEL_FILE.exists():
        os.remove(WEATHER_CHANNEL_FILE)

    print("\n" + "=" * 80)
    print("✅ SUCCESS: Bot now announces on #weather channel after restart!")
    print("=" * 80)
    print("\nThis solves the issue:")
    print("  'the bot is still not announcing on startup or reboot in the #weather channel'")
    print("\nHow it works:")
    print("  1. Bot auto-detects #weather channel from user messages")
    print("  2. Detected channel is persisted to logs/.weather_channel")
    print("  3. On restart, bot loads persisted channel")
    print("  4. Startup announcement goes to correct #weather channel")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        test_complete_restart_scenario()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)
