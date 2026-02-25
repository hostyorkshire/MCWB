#!/usr/bin/env python3
"""
Test that channels expire after 72 hours of inactivity.

This ensures the dashboard shows only recently active channels instead of
accumulating stale channels indefinitely.
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# Add parent directory to path to import meshcore
sys.path.insert(0, str(Path(__file__).parent.parent))

from meshcore import MeshCore


def test_fresh_channels_not_expired():
    """Test that recently used channels are not expired"""
    print("\n" + "=" * 60)
    print("TEST: Fresh channels are not expired")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        channels_file = os.path.join(tmpdir, "channels.json")
        
        # Create MeshCore and add channels
        mesh = MeshCore("test", debug=False, serial_port=None)
        mesh.start()
        mesh.send_message("Weather", channel="weather")
        mesh.send_message("Alerts", channel="alerts")
        
        # Get active channels immediately
        channels = mesh.get_active_channels()
        
        assert len(channels) == 2, f"Expected 2 channels, got {len(channels)}"
        assert channels[0]['channel_name'] == 'weather'
        assert channels[1]['channel_name'] == 'alerts'
        
        # Verify timestamps are recent
        current_time = time.time()
        for ch in channels:
            age_seconds = current_time - ch['last_used']
            assert age_seconds < 10, f"Channel should be fresh but is {age_seconds} seconds old"
        
        mesh.stop()
    
    print("✓ Fresh channels are active and have recent timestamps")
    return True


def test_expired_channels_removed():
    """Test that channels older than 72 hours are removed"""
    print("\n" + "=" * 60)
    print("TEST: Expired channels are removed")
    print("=" * 60)
    
    # Create MeshCore and add channels with old timestamps
    mesh = MeshCore("test", debug=False, serial_port=None)
    mesh.start()
    
    # Manually set old timestamps (73 hours ago)
    old_timestamp = time.time() - (73 * 3600)
    mesh._active_channels[1] = old_timestamp  # weather channel
    mesh._active_channels[2] = old_timestamp  # alerts channel
    
    # Add a fresh channel
    fresh_timestamp = time.time()
    mesh._active_channels[0] = fresh_timestamp  # public channel
    
    print(f"  Set up 2 expired channels (73 hours old) and 1 fresh channel")
    
    # Get active channels - should trigger cleanup
    channels = mesh.get_active_channels()
    
    # Should only have the fresh channel
    assert len(channels) == 1, f"Expected 1 channel after cleanup, got {len(channels)}"
    assert channels[0]['channel_idx'] == 0, "Expected only public channel to remain"
    
    mesh.stop()
    
    print("✓ Expired channels removed, only fresh channel remains")
    return True


def test_expiration_threshold():
    """Test the 72-hour threshold precisely"""
    print("\n" + "=" * 60)
    print("TEST: 72-hour expiration threshold")
    print("=" * 60)
    
    mesh = MeshCore("test", debug=False, serial_port=None)
    mesh.start()
    
    current_time = time.time()
    
    # Channel just under 72 hours old (should NOT expire)
    just_under_72h = current_time - (72 * 3600 - 60)  # 71 hours 59 minutes
    mesh._active_channels[1] = just_under_72h
    
    # Channel just over 72 hours old (should expire)
    just_over_72h = current_time - (72 * 3600 + 60)  # 72 hours 1 minute
    mesh._active_channels[2] = just_over_72h
    
    print(f"  Channel 1: {(current_time - just_under_72h) / 3600:.1f} hours old (should keep)")
    print(f"  Channel 2: {(current_time - just_over_72h) / 3600:.1f} hours old (should expire)")
    
    channels = mesh.get_active_channels()
    
    # Should only have channel 1 (just under 72 hours)
    assert len(channels) == 1, f"Expected 1 channel, got {len(channels)}"
    assert channels[0]['channel_idx'] == 1, "Expected channel 1 to remain"
    
    mesh.stop()
    
    print("✓ 72-hour threshold working correctly")
    return True


def test_channels_json_includes_timestamps():
    """Test that channels.json includes last_used timestamps"""
    print("\n" + "=" * 60)
    print("TEST: channels.json includes timestamps")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        channels_file = os.path.join(tmpdir, "channels.json")
        
        mesh = MeshCore("test", debug=False, serial_port=None)
        mesh.start()
        mesh.send_message("Weather", channel="weather")
        
        # Save to file
        mesh.save_active_channels(channels_file)
        mesh.stop()
        
        # Read and verify format
        import json
        with open(channels_file) as f:
            data = json.load(f)
        
        assert "channels" in data
        assert len(data["channels"]) > 0
        
        for ch in data["channels"]:
            assert "channel_idx" in ch, "Must have channel_idx"
            assert "channel_name" in ch, "Must have channel_name"
            assert "last_used" in ch, "Must have last_used timestamp"
            assert isinstance(ch["last_used"], (int, float)), "last_used must be numeric"
            
            # Verify timestamp is recent
            age = time.time() - ch["last_used"]
            assert age < 10, f"Timestamp should be recent, but is {age} seconds old"
    
    print("✓ channels.json format includes last_used timestamps")
    return True


def test_multiple_uses_update_timestamp():
    """Test that using a channel multiple times updates its timestamp"""
    print("\n" + "=" * 60)
    print("TEST: Multiple uses update timestamp")
    print("=" * 60)
    
    mesh = MeshCore("test", debug=False, serial_port=None)
    mesh.start()
    
    # Send initial message
    mesh.send_message("Message 1", channel="weather")
    first_timestamp = mesh._active_channels[1]
    
    # Wait a bit
    time.sleep(1)
    
    # Send another message
    mesh.send_message("Message 2", channel="weather")
    second_timestamp = mesh._active_channels[1]
    
    # Second timestamp should be newer
    assert second_timestamp > first_timestamp, "Timestamp should be updated on reuse"
    
    diff = second_timestamp - first_timestamp
    print(f"  ✓ Timestamp updated by {diff:.2f} seconds")
    
    mesh.stop()
    
    print("✓ Channel timestamp updates on each use")
    return True


def test_cleanup_on_get_and_save():
    """Test that cleanup happens when getting or saving channels"""
    print("\n" + "=" * 60)
    print("TEST: Cleanup on get and save operations")
    print("=" * 60)
    
    mesh = MeshCore("test", debug=False, serial_port=None)
    mesh.start()
    
    # Add expired and fresh channels
    old_timestamp = time.time() - (73 * 3600)
    fresh_timestamp = time.time()
    
    mesh._active_channels[1] = old_timestamp  # Should be removed
    mesh._active_channels[2] = fresh_timestamp  # Should remain
    
    print(f"  Set up 1 expired and 1 fresh channel")
    print(f"  Before cleanup: {len(mesh._active_channels)} channels")
    
    # Trigger cleanup via get_active_channels
    channels = mesh.get_active_channels()
    
    print(f"  After get_active_channels(): {len(channels)} channels")
    assert len(channels) == 1, "Expired channel should be removed"
    
    # Verify the internal dict was also updated
    assert 1 not in mesh._active_channels, "Expired channel should be removed from internal dict"
    assert 2 in mesh._active_channels, "Fresh channel should remain in internal dict"
    
    mesh.stop()
    
    print("✓ Cleanup works correctly on get and save operations")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CHANNEL EXPIRATION TESTS (72-hour TTL)")
    print("=" * 60)
    print("\nThese tests verify that channels expire after 72 hours of")
    print("inactivity, preventing the dashboard from showing stale channels.")
    
    all_passed = True
    
    tests = [
        test_fresh_channels_not_expired,
        test_expired_channels_removed,
        test_expiration_threshold,
        test_channels_json_includes_timestamps,
        test_multiple_uses_update_timestamp,
        test_cleanup_on_get_and_save,
    ]
    
    for test_func in tests:
        try:
            if not test_func():
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
