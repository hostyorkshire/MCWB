#!/usr/bin/env python3
"""
Test that channels are tracked when messages are sent
This ensures the dashboard shows active channels even when only sending
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meshcore import MeshCore


def test_channels_tracked_on_send():
    """Test that channels are tracked when messages are sent"""
    print("=" * 60)
    print("TEST: Channels Tracked on Send")
    print("=" * 60)

    mesh = MeshCore("test_node", debug=False)
    mesh.start()

    # Initially no active channels
    channels = mesh.get_active_channels()
    assert len(channels) == 0
    print("✓ Initially no active channels")

    # Send a message to channel 'weather' - should track the channel
    mesh.send_message("Test weather message", "text", channel="weather")

    channels = mesh.get_active_channels()
    assert len(channels) == 1, f"Expected 1 channel, got {len(channels)}"
    assert channels[0]["channel_name"] == "weather"
    print("✓ Channel 'weather' tracked after sending message")

    # Send a message to channel 'alerts'
    mesh.send_message("Test alert message", "text", channel="alerts")

    channels = mesh.get_active_channels()
    assert len(channels) == 2, f"Expected 2 channels, got {len(channels)}"
    channel_names = [ch["channel_name"] for ch in channels]
    assert "weather" in channel_names
    assert "alerts" in channel_names
    print("✓ Channel 'alerts' tracked after sending message")

    # Send to default channel (None)
    mesh.send_message("Test default message", "text", channel=None)

    channels = mesh.get_active_channels()
    assert len(channels) == 3, f"Expected 3 channels, got {len(channels)}"
    assert any(ch["channel_idx"] == 0 and ch["channel_name"] is None for ch in channels)
    print("✓ Default channel (idx=0) tracked after sending message")

    mesh.stop()
    print()


def test_channels_file_created_on_send():
    """Test that channels.json is created when sending messages"""
    print("=" * 60)
    print("TEST: Channels File Created on Send")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        channels_file = os.path.join(tmpdir, "channels.json")

        mesh = MeshCore("test_node", debug=False)
        mesh.start()

        # Send messages to different channels
        mesh.send_message("Weather report", "text", channel="weather")

        # Save to file
        mesh.save_active_channels(channels_file)

        # Verify file exists and has correct content
        assert os.path.exists(channels_file), "Channels file should exist"
        print("✓ Channels file created after sending message")

        with open(channels_file, "r") as f:
            data = json.load(f)

        assert "channels" in data
        assert len(data["channels"]) == 1
        assert data["channels"][0]["channel_name"] == "weather"
        print("✓ Channels file contains correct data")

        mesh.stop()
        print()


def test_mixed_send_and_receive():
    """Test that channels are tracked from both send and receive"""
    print("=" * 60)
    print("TEST: Mixed Send and Receive")
    print("=" * 60)

    mesh = MeshCore("test_node", debug=False)
    mesh.start()

    # Send to 'weather' channel
    mesh.send_message("Outgoing weather", "text", channel="weather")

    # Simulate receiving on 'alerts' channel
    mesh._channel_map["alerts"] = 2
    mesh._reverse_channel_map[2] = "alerts"
    mesh._dispatch_channel_message("User: Alert!", channel_idx=2)

    channels = mesh.get_active_channels()
    assert len(channels) == 2, f"Expected 2 channels, got {len(channels)}"
    channel_names = [ch["channel_name"] for ch in channels]
    assert "weather" in channel_names
    assert "alerts" in channel_names
    print("✓ Both sent and received channels tracked correctly")

    mesh.stop()
    print()


def main():
    """Run all tests"""
    try:
        test_channels_tracked_on_send()
        test_channels_file_created_on_send()
        test_mixed_send_and_receive()

        print("=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
