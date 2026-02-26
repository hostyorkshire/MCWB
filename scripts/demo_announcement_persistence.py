#!/usr/bin/env python3
"""
Manual demonstration of announcement persistence feature.
Shows that bot won't announce on restart if it announced recently.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time

from weather_bot import ANNOUNCE_INTERVAL, ANNOUNCE_TIMESTAMP_FILE


def demonstrate_feature():
    """Demonstrate the announcement persistence feature"""

    print("\n" + "=" * 70)
    print("DEMONSTRATION: Announcement Persistence on Bot Restart")
    print("=" * 70)
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
    time_since = current_time - last_announce if last_announce > 0 else ANNOUNCE_INTERVAL + 1

    if bot1.announce and time_since >= ANNOUNCE_INTERVAL:
        print(f"  ✓ Bot WILL announce (first startup)")
        bot1._save_last_announce_time(current_time)
    else:
        print(f"  ✗ Bot will NOT announce")

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
    minutes_until = int((ANNOUNCE_INTERVAL - time_since) / 60)

    print(f"  Last announcement: {minutes_since} minutes ago")
    print(f"  Time until next announcement: {minutes_until} minutes")

    if bot2.announce and time_since >= ANNOUNCE_INTERVAL:
        print(f"  ✓ Bot WILL announce")
    else:
        print(f"  ✗ Bot will NOT announce (too recent)")

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

    if bot3.announce and time_since >= ANNOUNCE_INTERVAL:
        print(f"  ✓ Bot WILL announce (sufficient time passed)")
    else:
        print(f"  ✗ Bot will NOT announce")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("The bot now:")
    print("  • Persists the timestamp of the last announcement to a file")
    print("  • On startup, checks if an announcement was made within 3 hours")
    print("  • Only announces if more than 3 hours have passed")
    print("  • Shows informative message when skipping announcement")
    print()

    # Clean up
    if os.path.exists(ANNOUNCE_TIMESTAMP_FILE):
        os.remove(ANNOUNCE_TIMESTAMP_FILE)
        print("Cleaned up timestamp file")
    print()


if __name__ == "__main__":
    demonstrate_feature()
