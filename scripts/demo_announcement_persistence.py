#!/usr/bin/env python3
"""
Manual demonstration of announcement persistence feature.
Shows that bot ALWAYS announces on startup, with timestamp tracking for periodic 3-hour announcements.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time

from weather_bot import ANNOUNCE_INTERVAL, ANNOUNCE_TIMESTAMP_FILE


def demonstrate_feature():
    """Demonstrate the announcement persistence feature"""

    print("\n" + "=" * 70)
    print("DEMONSTRATION: Announcement Behavior on Bot Restart")
    print("=" * 70)
    print("Note: Bot ALWAYS announces on startup. Timestamp only tracks periodic announcements.")
    print()

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
        print("Cleaned up any existing timestamp file")

    print("\nScenario 1: First bot startup (no previous announcement)")
    print("-" * 70)
    from weather_bot import WeatherBot

    bot1 = WeatherBot(node_id="DEMO_BOT", debug=False, announce=True)
    last_announce = bot1._get_last_announce_time()
    print(f"  Last announcement time: {last_announce} (0 = never)")

    current_time = time.time()

    if bot1.announce:
        print(f"  ✓ Bot WILL ALWAYS announce on startup (first startup)")
        bot1._save_last_announce_time(current_time)
    else:
        print(f"  ✗ Announcements disabled (--announce flag not set)")

    print()
    print("\nScenario 2: Bot restart after 30 minutes")
    print("-" * 70)

    # Simulate 30 minutes passing
    simulated_time = current_time - (30 * 60)
    bot1._save_last_announce_time(simulated_time)

    # Create new bot instance (simulates restart)
    bot2 = WeatherBot(node_id="DEMO_BOT", debug=False, announce=True)
    last_announce = bot2._get_last_announce_time()
    current_time = time.time()
    time_since = current_time - last_announce if last_announce > 0 else ANNOUNCE_INTERVAL + 1

    minutes_since = int(time_since / 60)
    minutes_until = int((ANNOUNCE_INTERVAL - time_since) / 60) if time_since < ANNOUNCE_INTERVAL else 0

    print(f"  Last announcement: {minutes_since} minutes ago")
    print(f"  Time until next periodic announcement: {minutes_until} minutes")

    if bot2.announce:
        print(f"  ✓ Bot WILL ALWAYS announce on startup")
        print(f"  ℹ️ Periodic announcements respect 3-hour interval (not startup)")
    else:
        print(f"  ✗ Announcements disabled (--announce flag not set)")

    print()
    print("\nScenario 3: Bot restart after 4 hours")
    print("-" * 70)

    # Simulate 4 hours passing
    simulated_time = current_time - (4 * 60 * 60)
    bot2._save_last_announce_time(simulated_time)

    # Create new bot instance (simulates restart)
    bot3 = WeatherBot(node_id="DEMO_BOT", debug=False, announce=True)
    last_announce = bot3._get_last_announce_time()
    current_time = time.time()
    time_since = current_time - last_announce if last_announce > 0 else ANNOUNCE_INTERVAL + 1

    hours_since = time_since / 3600

    print(f"  Last announcement: {hours_since:.1f} hours ago")
    print(f"  Announcement interval: {ANNOUNCE_INTERVAL / 3600} hours")

    if bot3.announce:
        print(f"  ✓ Bot WILL ALWAYS announce on startup")
        print(f"  ℹ️ Next periodic announcement will occur immediately (>3 hours passed)")
    else:
        print(f"  ✗ Announcements disabled (--announce flag not set)")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("The bot behavior:")
    print("  • ALWAYS announces on startup (every boot with --announce flag)")
    print("  • Persists timestamp for periodic 3-hour announcements (not startup)")
    print("  • Reads last timestamp only for logging purposes on startup")
    print("  • Periodic announcements respect the 3-hour interval")
    print("  • No code prevents re-announcing on multiple reboots")
    print()

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
        print("Cleaned up timestamp file")
    print()


if __name__ == "__main__":
    demonstrate_feature()
