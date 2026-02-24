#!/usr/bin/env python3
"""
Test script for active channel tracking functionality
Tests that channels are properly tracked and can be retrieved
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meshcore import MeshCore, MeshCoreMessage


def test_active_channels_tracking():
    """Test that active channels are tracked when messages are dispatched"""
    print("=" * 60)
    print("TEST: Active Channels Tracking")
    print("=" * 60)

    mesh = MeshCore("test_node", debug=False)
    mesh.start()

    # Initially no active channels
    channels = mesh.get_active_channels()
    assert len(channels) == 0
    print("✓ Initially no active channels")

    # Simulate receiving a message on channel_idx 0
    mesh._dispatch_channel_message("TestUser: Hello", channel_idx=0)
    
    channels = mesh.get_active_channels()
    assert len(channels) == 1
    assert channels[0]['channel_idx'] == 0
    assert channels[0]['channel_name'] is None
    print("✓ Channel 0 tracked after receiving message")

    # Simulate receiving a message on channel_idx 1 (mapped to 'weather')
    mesh._channel_map['weather'] = 1
    mesh._reverse_channel_map[1] = 'weather'
    mesh._dispatch_channel_message("WeatherBot: Temperature 20C", channel_idx=1)
    
    channels = mesh.get_active_channels()
    assert len(channels) == 2
    assert any(ch['channel_idx'] == 1 and ch['channel_name'] == 'weather' for ch in channels)
    print("✓ Channel 1 ('weather') tracked after receiving message")

    # Simulate receiving a message on channel_idx 2 (mapped to 'alerts')
    mesh._channel_map['alerts'] = 2
    mesh._reverse_channel_map[2] = 'alerts'
    mesh._dispatch_channel_message("AlertBot: Storm warning", channel_idx=2)
    
    channels = mesh.get_active_channels()
    assert len(channels) == 3
    assert any(ch['channel_idx'] == 2 and ch['channel_name'] == 'alerts' for ch in channels)
    print("✓ Channel 2 ('alerts') tracked after receiving message")

    # Verify all channels are present
    channel_indices = [ch['channel_idx'] for ch in channels]
    assert 0 in channel_indices
    assert 1 in channel_indices
    assert 2 in channel_indices
    print("✓ All three channels present in active channels list")

    mesh.stop()
    print()


def test_save_active_channels():
    """Test that active channels can be saved to JSON file"""
    print("=" * 60)
    print("TEST: Save Active Channels to JSON")
    print("=" * 60)

    # Use temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        channels_file = os.path.join(tmpdir, "channels.json")
        
        mesh = MeshCore("test_node", debug=False)
        mesh.start()

        # Setup channels
        mesh._channel_map['weather'] = 1
        mesh._reverse_channel_map[1] = 'weather'
        mesh._channel_map['alerts'] = 2
        mesh._reverse_channel_map[2] = 'alerts'
        
        # Simulate receiving messages
        mesh._dispatch_channel_message("User1: wx London", channel_idx=1)
        mesh._dispatch_channel_message("User2: Alert!", channel_idx=2)
        
        # Save channels
        mesh.save_active_channels(channels_file)
        
        # Verify file exists
        assert os.path.exists(channels_file)
        print("✓ Channels file created")
        
        # Verify file content
        with open(channels_file, 'r') as f:
            data = json.load(f)
        
        assert 'channels' in data
        assert 'last_updated' in data
        assert len(data['channels']) == 2
        print("✓ Channels JSON has correct structure")
        
        # Verify channel data
        channels = data['channels']
        channel_map = {ch['channel_idx']: ch['channel_name'] for ch in channels}
        assert 1 in channel_map and channel_map[1] == 'weather'
        assert 2 in channel_map and channel_map[2] == 'alerts'
        print("✓ Channel data correctly saved with names")
        
        mesh.stop()
        print()


def test_get_active_channels_format():
    """Test the format of get_active_channels() output"""
    print("=" * 60)
    print("TEST: Active Channels Output Format")
    print("=" * 60)

    mesh = MeshCore("test_node", debug=False)
    mesh.start()

    # Setup and simulate channels
    mesh._channel_map['weather'] = 1
    mesh._reverse_channel_map[1] = 'weather'
    mesh._dispatch_channel_message("User: test", channel_idx=0)
    mesh._dispatch_channel_message("User: test", channel_idx=1)
    
    channels = mesh.get_active_channels()
    
    # Check structure
    assert isinstance(channels, list)
    print("✓ get_active_channels() returns a list")
    
    assert len(channels) == 2
    print("✓ List contains 2 channels")
    
    # Check first channel (channel 0 - default)
    ch0 = channels[0]
    assert 'channel_idx' in ch0
    assert 'channel_name' in ch0
    assert ch0['channel_idx'] == 0
    assert ch0['channel_name'] is None
    print("✓ Channel 0 has correct structure and None name")
    
    # Check second channel (channel 1 - weather)
    ch1 = channels[1]
    assert ch1['channel_idx'] == 1
    assert ch1['channel_name'] == 'weather'
    print("✓ Channel 1 has correct structure and 'weather' name")
    
    # Check sorted order
    assert channels[0]['channel_idx'] < channels[1]['channel_idx']
    print("✓ Channels are sorted by channel_idx")
    
    mesh.stop()
    print()


def main():
    """Run all tests"""
    try:
        test_active_channels_tracking()
        test_save_active_channels()
        test_get_active_channels_format()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
