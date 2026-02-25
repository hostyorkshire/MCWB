#!/usr/bin/env python3
"""
End-to-end test: Verify the complete flow from sending messages to dashboard display
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meshcore import MeshCore


def test_end_to_end_flow():
    """Test complete flow: send message -> track channel -> save to file -> dashboard reads"""
    print("=" * 70)
    print("END-TO-END TEST: Complete Dashboard Flow")
    print("=" * 70)
    print()
    
    # Setup
    channels_file = Path(__file__).parent.parent / "logs" / "channels.json"
    if channels_file.exists():
        channels_file.unlink()
        print("✓ Cleaned up existing channels.json")
    
    # Step 1: Create bot and send messages
    print("\n1. Bot sends messages to channels...")
    mesh = MeshCore("test_bot", debug=False)
    mesh.start()
    
    mesh.send_message("Weather update", "text", channel="weather")
    mesh.send_message("Alert message", "text", channel="alerts")
    mesh.send_message("Public message", "text", channel=None)
    
    channels = mesh.get_active_channels()
    print(f"   ✓ Tracked {len(channels)} channels")
    
    # Step 2: Save to file (happens automatically in send_message, but let's be explicit)
    print("\n2. Saving channels to JSON file...")
    mesh.save_active_channels(str(channels_file))
    assert channels_file.exists(), "channels.json should exist"
    print(f"   ✓ File saved: {channels_file}")
    
    # Step 3: Simulate dashboard API reading the file
    print("\n3. Dashboard API reads channels.json...")
    with open(channels_file, 'r') as f:
        data = json.load(f)
    
    assert 'channels' in data, "JSON should have 'channels' key"
    assert 'last_updated' in data, "JSON should have 'last_updated' key"
    print(f"   ✓ Found {len(data['channels'])} channels in file")
    print(f"   ✓ Last updated: {data['last_updated']}")
    
    # Step 4: Format for display (like web_dashboard.py does)
    print("\n4. Formatting channels for display...")
    formatted_channels = []
    for ch in data['channels']:
        channel_name = ch.get('channel_name')
        if channel_name:
            formatted_channels.append(f"#{channel_name}")
        elif ch.get('channel_idx') == 0:
            formatted_channels.append("#public")
        else:
            formatted_channels.append(f"#channel{ch.get('channel_idx')}")
    
    print(f"   ✓ Dashboard will display:")
    for ch in formatted_channels:
        print(f"     • {ch}")
    
    # Step 5: Verify expected channels
    print("\n5. Verifying expected channels...")
    assert "#weather" in formatted_channels, "Should have #weather channel"
    assert "#alerts" in formatted_channels, "Should have #alerts channel"
    assert "#public" in formatted_channels, "Should have #public channel"
    print("   ✓ All expected channels present")
    
    mesh.stop()
    
    print("\n" + "=" * 70)
    print("✅ END-TO-END TEST PASSED")
    print("=" * 70)
    print("\nComplete flow verified:")
    print("  1. Bot sends messages to different channels")
    print("  2. MeshCore tracks active channels")
    print("  3. Channels are saved to logs/channels.json")
    print("  4. Dashboard API reads and formats channels")
    print("  5. Dashboard displays: " + ", ".join(formatted_channels))
    print("=" * 70)
    
    return 0


def main():
    try:
        return test_end_to_end_flow()
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
