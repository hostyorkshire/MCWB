#!/usr/bin/env python3
"""
Diagnostic script to help identify channel filtering issues
Run this to check if your bot configuration is blocking responses
"""

import sys
import argparse

print("="*70)
print("Weather Bot Channel Configuration Diagnostic")
print("="*70)
print()

def diagnose_command(command):
    """Diagnose a command line to see if it will block channels"""
    print(f"Command: {command}")
    print()
    
    has_channel_filter = "--channel" in command or "-c " in command
    has_announce = "--announce-channel" in command or "-a " in command
    
    if has_channel_filter:
        # Extract channel value
        parts = command.split()
        channel_val = None
        for i, part in enumerate(parts):
            if part in ["--channel", "-c"] and i + 1 < len(parts):
                channel_val = parts[i + 1]
                break
        
        print("⚠ WARNING: Channel filter is ENABLED")
        print(f"  Filter value: {channel_val}")
        print()
        print("This means:")
        if channel_val and channel_val != '""' and channel_val != "''":
            print(f"  ✗ Bot will ONLY accept queries from '{channel_val}' channel")
            print(f"  ✗ Queries from other channels will be IGNORED")
            print()
            print("To fix: Remove the --channel parameter entirely")
        else:
            print("  ✓ Channel filter is empty (accepts all channels)")
    else:
        print("✓ Channel filter is NOT set")
        print("  ✓ Bot accepts queries from ALL channels")
        print("  ✓ Bot replies on the same channel where each query came from")
    
    print()
    
    if has_announce:
        parts = command.split()
        announce_val = None
        for i, part in enumerate(parts):
            if part in ["--announce-channel", "-a"] and i + 1 < len(parts):
                announce_val = parts[i + 1]
                break
        print(f"ℹ Announce channel: {announce_val}")
        print("  (This only affects periodic announcements, not query responses)")
    else:
        print("ℹ No announce channel parameter (defaults to 'wxtest')")
    
    print()
    print("="*70)

# Check common scenarios
print("Checking common bot startup commands:")
print()

scenarios = [
    ("DEFAULT (no parameters)",
     "python3 weather_bot.py --port auto --baud 115200 -d"),
    
    ("WITH channel filter (BLOCKS other channels)",
     "python3 weather_bot.py --port auto --baud 115200 --channel weather -d"),
    
    ("WITH empty channel filter (ALLOWS all channels)",
     "python3 weather_bot.py --port auto --baud 115200 --channel \"\" -d"),
    
    ("WITH announce channel only (ALLOWS all channels)",
     "python3 weather_bot.py --port auto --baud 115200 --announce-channel wxtest -d"),
]

for name, cmd in scenarios:
    print(f"\nScenario: {name}")
    print("-"*70)
    diagnose_command(cmd)

print("\n" + "="*70)
print("RECOMMENDATIONS")
print("="*70)
print()
print("1. To accept queries from ALL channels:")
print("   - Don't use --channel parameter")
print("   - Current service file is correct:")
print("     ExecStart=... --port auto --baud 115200 -d")
print()
print("2. If bot is still not responding on other channels:")
print("   a) Check the actual command being used:")
print("      systemctl status weather_bot")
print("      journalctl -u weather_bot -n 50")
print()
print("   b) Check bot logs for 'Channel filter enabled' messages")
print("      If you see this, the bot is filtering!")
print()
print("   c) Verify physical radio channel configuration")
print("      The bot sends responses to channel_idx, which must")
print("      match the physical radio channel slots")
print()
print("3. To test manually:")
print("   python3 weather_bot.py --interactive")
print("   Then try: wx London")
print()
print("="*70)
