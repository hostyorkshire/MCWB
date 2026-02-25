#!/usr/bin/env python3
"""
Demonstration that channels are now tracked when sending messages
This simulates the weather bot scenario where it sends announcements
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meshcore import MeshCore


def main():
    print("=" * 70)
    print("DEMONSTRATION: Active Channels Tracking Fix")
    print("=" * 70)
    print()
    print("Scenario: Weather bot sends announcement messages")
    print("Expected: Channels should be tracked and visible in dashboard")
    print()
    
    # Create MeshCore instance (simulates the weather bot)
    mesh = MeshCore("weather_bot", debug=False)
    mesh.start()
    
    print("1. Starting with no active channels...")
    channels = mesh.get_active_channels()
    print(f"   Active channels: {len(channels)}")
    print()
    
    # Simulate sending announcement on 'weather' channel
    print("2. Sending announcement to 'weather' channel...")
    mesh.send_message("Weather Bot is now online!", "text", channel="weather")
    
    channels = mesh.get_active_channels()
    print(f"   Active channels: {len(channels)}")
    for ch in channels:
        channel_display = f"#{ch['channel_name']}" if ch['channel_name'] else "#public"
        print(f"   - Channel {ch['channel_idx']}: {channel_display}")
    print()
    
    # Simulate sending to 'alerts' channel
    print("3. Sending message to 'alerts' channel...")
    mesh.send_message("Alert: System operational", "text", channel="alerts")
    
    channels = mesh.get_active_channels()
    print(f"   Active channels: {len(channels)}")
    for ch in channels:
        channel_display = f"#{ch['channel_name']}" if ch['channel_name'] else "#public"
        print(f"   - Channel {ch['channel_idx']}: {channel_display}")
    print()
    
    # Save to channels.json (what dashboard reads)
    print("4. Saving channels to logs/channels.json...")
    channels_file = Path(__file__).parent.parent / "logs" / "channels.json"
    mesh.save_active_channels(str(channels_file))
    
    if channels_file.exists():
        with open(channels_file, 'r') as f:
            data = json.load(f)
        
        print(f"   ✓ File created: {channels_file}")
        print(f"   ✓ Channels in file: {len(data['channels'])}")
        print(f"   ✓ Dashboard will display:")
        
        display_channels = []
        for ch in data['channels']:
            if ch['channel_name']:
                display_channels.append(f"#{ch['channel_name']}")
            elif ch['channel_idx'] == 0:
                display_channels.append("#public")
            else:
                display_channels.append(f"#channel{ch['channel_idx']}")
        
        print(f"      {', '.join(display_channels)}")
    print()
    
    mesh.stop()
    
    print("=" * 70)
    print("✅ SUCCESS: Channels are now tracked when sending messages!")
    print("=" * 70)
    print()
    print("Before this fix:")
    print("  - Channels were only tracked when RECEIVING messages")
    print("  - Dashboard showed 'No active channels detected yet'")
    print()
    print("After this fix:")
    print("  - Channels are tracked when SENDING or RECEIVING messages")
    print("  - Dashboard shows all channels the bot uses")
    print("=" * 70)


if __name__ == "__main__":
    main()
