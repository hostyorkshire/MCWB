#!/usr/bin/env python3
"""
Test that channels.json save failures are logged instead of silently failing.

This test ensures that administrators can diagnose dashboard issues where
active channels aren't showing up due to file I/O problems.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to import meshcore
sys.path.insert(0, str(Path(__file__).parent.parent))

from meshcore import MeshCore


def test_channels_save_success():
    """Test that channels are successfully saved and logged in debug mode"""
    print("\n" + "=" * 60)
    print("TEST: Successful channels save with debug logging")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        channels_file = os.path.join(tmpdir, "channels.json")

        # Create MeshCore with debug enabled
        mesh = MeshCore("test", debug=True, serial_port=None)
        mesh.start()

        # Send messages to populate channels
        mesh.send_message("Test message", channel="weather")

        # Save to temp location
        mesh.save_active_channels(channels_file)

        # Verify file exists
        assert os.path.exists(channels_file), "channels.json should exist"

        # Verify content
        import json

        with open(channels_file) as f:
            data = json.load(f)

        assert "channels" in data, "Data should have channels key"
        assert len(data["channels"]) > 0, "Should have at least one channel"

        mesh.stop()

    print("✓ Channels saved successfully with debug logging")
    return True


def test_channels_save_error_logging():
    """Test that save errors are logged to meshcore_error.log"""
    print("\n" + "=" * 60)
    print("TEST: Error logging for failed saves")
    print("=" * 60)

    # Create MeshCore
    mesh = MeshCore("test", debug=False, serial_port=None)
    mesh.start()

    # Try to save to an impossible path
    impossible_path = "/dev/null/impossible/channels.json"
    mesh.save_active_channels(impossible_path)

    # Check that error was logged
    error_log = Path(__file__).parent.parent / "logs" / "meshcore_error.log"
    if error_log.exists():
        with open(error_log) as f:
            log_content = f.read()

        # Verify error message contains the failed path
        assert "Failed to save active channels" in log_content, "Error log should contain failure message"
        assert impossible_path in log_content, "Error log should contain the failed path"

        print(f"✓ Error correctly logged to {error_log}")
    else:
        print(f"⚠ Error log not found at {error_log}")

    mesh.stop()
    return True


def test_channels_json_format():
    """Test that channels.json has correct format for dashboard"""
    print("\n" + "=" * 60)
    print("TEST: channels.json format for dashboard")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        channels_file = os.path.join(tmpdir, "channels.json")

        # Create and populate channels
        mesh = MeshCore("test", debug=False, serial_port=None)
        mesh.start()
        mesh.send_message("Weather", channel="weather")
        mesh.send_message("Alerts", channel="alerts")
        mesh.send_message("Public", channel=None)

        mesh.save_active_channels(channels_file)
        mesh.stop()

        # Verify format matches what dashboard expects
        import json

        with open(channels_file) as f:
            data = json.load(f)

        assert "channels" in data, "Must have 'channels' key"
        assert "last_updated" in data, "Must have 'last_updated' key"
        assert isinstance(data["channels"], list), "channels must be a list"

        # Verify channel structure
        for ch in data["channels"]:
            assert "channel_idx" in ch, "Each channel must have channel_idx"
            assert "channel_name" in ch, "Each channel must have channel_name"
            assert isinstance(ch["channel_idx"], int), "channel_idx must be int"

        # Verify we have the expected channels
        channel_names = [ch.get("channel_name") for ch in data["channels"]]
        assert "weather" in channel_names, "Should have weather channel"
        assert "alerts" in channel_names, "Should have alerts channel"
        assert None in channel_names, "Should have default/public channel (None)"

    print("✓ channels.json format is correct")
    print(f"  - Found {len(data['channels'])} channels: {channel_names}")
    return True


def test_empty_channels_on_start():
    """Test that channels.json is created even when empty"""
    print("\n" + "=" * 60)
    print("TEST: Empty channels.json created on start")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        channels_file = os.path.join(tmpdir, "channels.json")

        # Start meshcore without sending any messages
        mesh = MeshCore("test", debug=False, serial_port=None)
        mesh.start()

        # Save immediately (should have empty channels)
        mesh.save_active_channels(channels_file)
        mesh.stop()

        # Verify file exists and is valid JSON
        assert os.path.exists(channels_file), "channels.json should be created on start"

        import json

        with open(channels_file) as f:
            data = json.load(f)

        assert data["channels"] == [], "Should have empty channels array"
        assert "last_updated" in data, "Should have last_updated timestamp"

    print("✓ Empty channels.json created successfully")
    print("  - This allows dashboard to show 'No active channels detected yet'")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CHANNELS ERROR LOGGING TESTS")
    print("=" * 60)
    print("\nThese tests verify that save_active_channels() properly logs")
    print("errors instead of failing silently, helping admins diagnose")
    print("dashboard issues where channels aren't showing up.")

    all_passed = True

    try:
        if not test_channels_save_success():
            all_passed = False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        all_passed = False

    try:
        if not test_channels_save_error_logging():
            all_passed = False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        all_passed = False

    try:
        if not test_channels_json_format():
            all_passed = False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        all_passed = False

    try:
        if not test_empty_channels_on_start():
            all_passed = False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
    print("=" * 60)
