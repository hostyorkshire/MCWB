#!/usr/bin/env python3
"""
Diagnostic script to test announcement functionality
"""

import sys
import time
from weather_bot import WeatherBot, ANNOUNCE_MESSAGE, ANNOUNCE_INTERVAL

def test_announcement_config():
    """Test announcement configuration"""
    print("=" * 70)
    print("ANNOUNCEMENT DIAGNOSTIC TOOL")
    print("=" * 70)
    print()
    
    print("1. Checking announcement constants...")
    print(f"   ANNOUNCE_INTERVAL: {ANNOUNCE_INTERVAL} seconds ({ANNOUNCE_INTERVAL / 3600} hours)")
    print(f"   ANNOUNCE_MESSAGE: {ANNOUNCE_MESSAGE}")
    print()
    
    print("2. Creating bot with default announce_channel (wxtest)...")
    try:
        bot = WeatherBot(node_id="DIAG_BOT", debug=True, announce_channel="wxtest")
        print(f"   ✓ Bot created")
        print(f"   ✓ announce_channel = '{bot.announce_channel}'")
    except Exception as e:
        print(f"   ✗ Error creating bot: {e}")
        return False
    print()
    
    print("3. Starting bot...")
    try:
        bot.start()
        print("   ✓ Bot started successfully")
    except Exception as e:
        print(f"   ✗ Error starting bot: {e}")
        return False
    print()
    
    print("4. Testing send_announcement() method...")
    try:
        bot.send_announcement()
        print("   ✓ Announcement sent successfully")
    except Exception as e:
        print(f"   ✗ Error sending announcement: {e}")
        bot.stop()
        return False
    print()
    
    print("5. Verifying bot is still running...")
    if bot.mesh.is_running():
        print("   ✓ Bot is still running")
    else:
        print("   ✗ Bot has stopped")
        return False
    print()
    
    print("6. Stopping bot...")
    bot.stop()
    print("   ✓ Bot stopped cleanly")
    print()
    
    print("=" * 70)
    print("DIAGNOSIS: Announcement code is WORKING correctly")
    print("=" * 70)
    print()
    print("If announcements are not being received on #wxtest channel:")
    print("  1. Check that devices are subscribed to channel 'wxtest'")
    print("  2. Verify channel 'wxtest' is mapped correctly in MeshCore app")
    print("  3. Check radio configuration and channel settings")
    print("  4. Ensure channel_idx mapping is correct (log shows 'wxtest' -> idx 1)")
    print()
    
    return True

def test_with_hardware():
    """Test with hardware detection"""
    print("=" * 70)
    print("HARDWARE DETECTION TEST")
    print("=" * 70)
    print()
    
    try:
        from meshcore import find_serial_ports
        ports = find_serial_ports(debug=True)
        if ports:
            print(f"✓ Found serial ports: {ports}")
            print()
            print("To run bot with hardware:")
            print(f"  python3 weather_bot.py -n WX_BOT --port {ports[0]} --baud 115200 -d")
        else:
            print("✗ No serial ports found")
            print("  Bot will run in simulation mode")
    except Exception as e:
        print(f"✗ Error detecting ports: {e}")
    print()

if __name__ == "__main__":
    success = test_announcement_config()
    test_with_hardware()
    
    sys.exit(0 if success else 1)
