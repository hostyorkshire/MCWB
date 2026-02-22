#!/usr/bin/env python3
"""
Manual demonstration of the reboot notification feature.

This script simulates the bot starting multiple times to show how the
reboot notification feature works.
"""

import os
import sys
import time
from weather_bot import STATE_FILE, REBOOT_NOTIFY_MESSAGE


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_state():
    """Check and display the current state"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            timestamp = f.read().strip()
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))
        print(f"State file exists: {STATE_FILE}")
        print(f"  Last marked running at: {time_str}")
        return True
    else:
        print(f"State file does not exist: {STATE_FILE}")
        return False


def simulate_bot_start(run_number):
    """Simulate a bot startup"""
    print_header(f"Simulated Bot Start #{run_number}")
    
    print("\n1. Checking for previous state...")
    is_reboot = check_state()
    
    print("\n2. Bot initialization...")
    if is_reboot:
        print(f"   ⚠️  REBOOT DETECTED!")
        print(f"   📤 Would send notification: '{REBOOT_NOTIFY_MESSAGE}'")
    else:
        print("   ✓ First run - no reboot notification needed")
    
    print("\n3. Marking bot as running...")
    with open(STATE_FILE, 'w') as f:
        f.write(f"{int(time.time())}\n")
    print(f"   ✓ State file created/updated")
    
    print("\n4. Bot is now running normally...")
    print("   (Press Ctrl+C to simulate crash/power loss)")


def main():
    """Run the demonstration"""
    print_header("REBOOT NOTIFICATION FEATURE DEMONSTRATION")
    print("""
This demonstration shows how the reboot notification feature works:

- On FIRST RUN: No state file exists, so no notification is sent
- On RESTART: State file exists, indicating a previous run, so a 
  notification is sent to alert users that the bot has restarted
  
This is useful for detecting:
  • Power losses
  • System crashes
  • Service restarts
  • Unexpected reboots

The state file is stored at: {STATE_FILE}
    """.format(STATE_FILE=STATE_FILE))
    
    # Clean up any existing state
    if os.path.exists(STATE_FILE):
        print(f"\nCleaning up existing state file for clean demo...")
        os.remove(STATE_FILE)
    
    input("\nPress Enter to simulate FIRST RUN...")
    simulate_bot_start(1)
    
    input("\n\nPress Enter to simulate RESTART (power restored after crash)...")
    simulate_bot_start(2)
    
    input("\n\nPress Enter to simulate ANOTHER RESTART...")
    simulate_bot_start(3)
    
    print_header("DEMONSTRATION COMPLETE")
    print("""
Summary:
  ✓ Run #1: First run - No notification sent
  ✓ Run #2: Restart detected - Notification would be sent
  ✓ Run #3: Another restart detected - Notification would be sent
  
In a real deployment with --reboot-notify flag:
  • Each restart after the first would trigger a LoRa mesh message
  • Users on the mesh network would see the restart notification
  • This helps with monitoring remote/unattended installations
  
To enable in your bot, add the --reboot-notify flag:
  python3 weather_bot.py --reboot-notify
    """)
    
    # Clean up
    if os.path.exists(STATE_FILE):
        print(f"\nCleaning up state file...")
        os.remove(STATE_FILE)
    
    print("\n✓ Demo complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        sys.exit(0)
