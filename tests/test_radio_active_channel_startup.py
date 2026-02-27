#!/usr/bin/env python3
"""
Test that the bot uses the radio's most recently active channel on startup.
Verifies the new priority order:
1. Manual --weather-channel-idx
2. Radio's most recently active channel (from channels.json via mesh._active_channels)
3. Persisted channel from previous session (.last_weather_channel)
4. Default channel 0
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from weather_bot import WEATHER_CHANNEL_FILE, WeatherBot

# Path to the active channels JSON file used by MeshCore
CHANNELS_FILE = Path(__file__).parent.parent / "logs" / "channels.json"


def _write_channels_json(channels):
    """Helper to write a channels.json file with given channel data."""
    CHANNELS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "channels": channels,
        "last_updated": "2024-01-01T00:00:00",
    }
    with open(CHANNELS_FILE, "w") as f:
        json.dump(data, f)


def _cleanup():
    """Remove persistence files between tests."""
    if CHANNELS_FILE.exists():
        CHANNELS_FILE.unlink()
    if WEATHER_CHANNEL_FILE.exists():
        WEATHER_CHANNEL_FILE.unlink()


def test_uses_radio_active_channel_when_available():
    """Bot uses the most recently active non-default channel from channels.json on startup."""
    print("=" * 70)
    print("TEST: Use radio's most recently active channel on startup")
    print("=" * 70)

    _cleanup()

    # Simulate channels.json with activity on channel 1
    _write_channels_json([
        {"channel_idx": 0, "channel_name": None, "last_used": time.time() - 100},
        {"channel_idx": 1, "channel_name": "weather", "last_used": time.time()},
    ])

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    assert bot._announce_channel_idx == 1, (
        f"Expected channel_idx=1 from channels.json, got {bot._announce_channel_idx}"
    )
    assert bot._weather_channel_detected is True, "Should mark channel as detected"
    print(f"  ✓ Bot uses radio active channel_idx=1 from channels.json")

    _cleanup()
    print()


def test_most_recently_active_channel_preferred():
    """Bot selects the MOST RECENTLY used channel when multiple non-default channels exist."""
    print("=" * 70)
    print("TEST: Most recently active channel is preferred")
    print("=" * 70)

    _cleanup()

    now = time.time()
    _write_channels_json([
        {"channel_idx": 0, "channel_name": None, "last_used": now - 10},
        {"channel_idx": 2, "channel_name": None, "last_used": now - 50},
        {"channel_idx": 3, "channel_name": None, "last_used": now - 5},   # most recent
    ])

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    assert bot._announce_channel_idx == 3, (
        f"Expected most recently active channel_idx=3, got {bot._announce_channel_idx}"
    )
    print(f"  ✓ Bot selected most recently active channel_idx=3")

    _cleanup()
    print()


def test_explicit_config_overrides_radio_active_channel():
    """Manual --weather-channel-idx takes precedence over radio active channels."""
    print("=" * 70)
    print("TEST: Explicit config overrides radio active channel")
    print("=" * 70)

    _cleanup()

    # channels.json has channel 1
    _write_channels_json([
        {"channel_idx": 1, "channel_name": "weather", "last_used": time.time()},
    ])

    # Explicit config set to 5
    bot = WeatherBot(node_id="test_bot", debug=False, announce=True, weather_channel_idx=5)

    assert bot._announce_channel_idx == 5, (
        f"Explicit config should override channels.json, expected 5, got {bot._announce_channel_idx}"
    )
    print(f"  ✓ Explicit weather_channel_idx=5 takes precedence over channels.json channel 1")

    _cleanup()
    print()


def test_falls_back_to_persisted_when_no_non_default_radio_channels():
    """Falls back to persisted channel when channels.json only has channel 0."""
    print("=" * 70)
    print("TEST: Falls back to persisted channel when radio only has default channel")
    print("=" * 70)

    _cleanup()

    # channels.json has only channel 0 (default)
    _write_channels_json([
        {"channel_idx": 0, "channel_name": None, "last_used": time.time()},
    ])
    # Persisted channel from previous session
    WEATHER_CHANNEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    WEATHER_CHANNEL_FILE.write_text("4")

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    assert bot._announce_channel_idx == 4, (
        f"Should fall back to persisted channel 4, got {bot._announce_channel_idx}"
    )
    print(f"  ✓ Falls back to persisted channel_idx=4 (channels.json only has default channel)")

    _cleanup()
    print()


def test_falls_back_to_zero_when_no_channels_anywhere():
    """Defaults to channel 0 when neither channels.json nor persisted file exist."""
    print("=" * 70)
    print("TEST: Defaults to channel 0 when no channels configured or detected")
    print("=" * 70)

    _cleanup()

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    assert bot._announce_channel_idx == 0, (
        f"Should default to channel_idx=0, got {bot._announce_channel_idx}"
    )
    print(f"  ✓ Defaults to channel_idx=0 when no channel history exists")

    _cleanup()
    print()


def test_corrupt_channels_json_handled_gracefully():
    """Corrupt channels.json does not crash the bot; falls through to persisted file."""
    print("=" * 70)
    print("TEST: Corrupt channels.json handled gracefully")
    print("=" * 70)

    _cleanup()

    # Write corrupt channels.json
    CHANNELS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHANNELS_FILE.write_text("this is not valid JSON!!!")
    # Persisted channel as fallback
    WEATHER_CHANNEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    WEATHER_CHANNEL_FILE.write_text("2")

    bot = WeatherBot(node_id="test_bot", debug=False, announce=True)

    assert bot._announce_channel_idx == 2, (
        f"Corrupt channels.json should fall back to persisted channel 2, got {bot._announce_channel_idx}"
    )
    print(f"  ✓ Corrupt channels.json handled gracefully, using persisted channel_idx=2")

    _cleanup()
    print()


if __name__ == "__main__":
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "MCWB - Radio Active Channel Startup Tests" + " " * 17 + "║")
    print("╚" + "=" * 68 + "╝\n")

    try:
        test_uses_radio_active_channel_when_available()
        test_most_recently_active_channel_preferred()
        test_explicit_config_overrides_radio_active_channel()
        test_falls_back_to_persisted_when_no_non_default_radio_channels()
        test_falls_back_to_zero_when_no_channels_anywhere()
        test_corrupt_channels_json_handled_gracefully()

        print("=" * 70)
        print("✓ All radio active channel startup tests passed!")
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
