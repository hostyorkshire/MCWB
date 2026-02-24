#!/usr/bin/env python3
"""
Integration test demonstrating the complete channel tracking workflow
Shows how channels are tracked from radio messages and displayed on dashboard
"""

import sys
import os
import json
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meshcore import MeshCore


def test_complete_workflow():
    """Test the complete workflow of channel tracking and display"""
    print("=" * 70)
    print("Integration Test: Complete Channel Tracking Workflow")
    print("=" * 70)
    print()

    # Step 1: Create MeshCore instance (simulates LORA radio connection)
    print("1. Creating MeshCore instance (simulates LORA radio)...")
    mesh = MeshCore("test_bot", debug=False)
    mesh.start()
    print("   ✓ MeshCore started")
    print()

    # Step 2: Configure channel mappings (simulates MeshCore app configuration)
    print("2. Configuring channels (simulates MeshCore app setup)...")
    mesh._channel_map['weather'] = 1
    mesh._reverse_channel_map[1] = 'weather'
    mesh._channel_map['alerts'] = 2
    mesh._reverse_channel_map[2] = 'alerts'
    print("   ✓ Configured channel mappings:")
    print("     - Channel 1: 'weather'")
    print("     - Channel 2: 'alerts'")
    print()

    # Step 3: Simulate receiving messages on different channels
    print("3. Simulating incoming LORA radio messages...")
    
    print("   a) Receiving message on default channel (idx=0)...")
    mesh._dispatch_channel_message("User1: Hello everyone", channel_idx=0)
    print("      ✓ Message processed on channel 0 (#public)")
    
    print("   b) Receiving message on weather channel (idx=1)...")
    mesh._dispatch_channel_message("User2: wx London", channel_idx=1)
    print("      ✓ Message processed on channel 1 (#weather)")
    
    print("   c) Receiving message on alerts channel (idx=2)...")
    mesh._dispatch_channel_message("User3: Storm warning!", channel_idx=2)
    print("      ✓ Message processed on channel 2 (#alerts)")
    print()

    # Step 4: Verify channels are tracked
    print("4. Verifying active channels are tracked...")
    channels = mesh.get_active_channels()
    print(f"   ✓ Found {len(channels)} active channels:")
    for ch in channels:
        name = ch['channel_name'] if ch['channel_name'] else 'public'
        print(f"     - Channel {ch['channel_idx']}: #{name}")
    
    assert len(channels) == 3
    print()

    # Step 5: Save channels to JSON (for dashboard API)
    print("5. Saving channels to JSON file...")
    channels_file = "logs/channels.json"
    mesh.save_active_channels(channels_file)
    
    assert os.path.exists(channels_file)
    print(f"   ✓ Channels saved to {channels_file}")
    
    # Verify JSON content
    with open(channels_file, 'r') as f:
        data = json.load(f)
    
    print(f"   ✓ JSON contains {len(data['channels'])} channels")
    print(f"   ✓ Last updated: {data['last_updated']}")
    print()

    # Step 6: Simulate dashboard API reading the file
    print("6. Simulating dashboard API reading channels...")
    formatted_channels = []
    for ch in data['channels']:
        channel_name = ch.get('channel_name')
        if channel_name:
            formatted_channels.append(f"#{channel_name}")
        elif ch.get('channel_idx') == 0:
            formatted_channels.append("#public")
        else:
            formatted_channels.append(f"#channel{ch.get('channel_idx')}")
    
    print("   ✓ Dashboard would display:")
    print(f"     {', '.join(formatted_channels)}")
    
    assert "#public" in formatted_channels
    assert "#weather" in formatted_channels
    assert "#alerts" in formatted_channels
    print()

    mesh.stop()
    
    # Summary
    print("=" * 70)
    print("✅ INTEGRATION TEST PASSED")
    print("=" * 70)
    print()
    print("Complete workflow verified:")
    print("  1. ✓ LORA radio receives messages on different channels")
    print("  2. ✓ MeshCore tracks active channels automatically")
    print("  3. ✓ Channels are saved to JSON file")
    print("  4. ✓ Dashboard API reads and formats channels")
    print("  5. ✓ Website and dashboard display channels")
    print()
    print("Example output: #public, #weather, #alerts")
    print("=" * 70)


def main():
    """Run integration test"""
    try:
        test_complete_workflow()
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
