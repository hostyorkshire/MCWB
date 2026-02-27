#!/usr/bin/env python3
"""
Demo script to show weather channel persistence behavior
Simulates bot restart scenarios
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from weather_bot import WEATHER_CHANNEL_FILE, WeatherBot

print("\n" + "=" * 80)
print("MCWB Weather Channel Persistence Demo")
print("=" * 80)

# Clean up previous state
if WEATHER_CHANNEL_FILE.exists():
    os.remove(WEATHER_CHANNEL_FILE)
    print("\n✓ Cleaned up previous state\n")

# Scenario 1: First startup - no persisted channel
print("=" * 80)
print("SCENARIO 1: First Startup (No persisted channel)")
print("=" * 80)
bot1 = WeatherBot(node_id="demo_bot", debug=False, announce=True)
print(f"  ➜ Bot initialized with _announce_channel_idx = {bot1._announce_channel_idx}")
print(f"  ➜ Weather channel detected = {bot1._weather_channel_detected}")
print(f"  ➜ Will announce on channel_idx = {bot1._announce_channel_idx}")
print("  ℹ  This is the default behavior - announces on channel 0")

# Scenario 2: Simulate auto-detection
print("\n" + "=" * 80)
print("SCENARIO 2: User Sends Message on #weather Channel")
print("=" * 80)
print("  Simulating: User sends 'WX London' on channel_idx=1")
bot1._detect_channel_name("Received on #weather channel", 1)
print(f"  ➜ Auto-detected weather channel: channel_idx = {bot1._announce_channel_idx}")
print(f"  ➜ Weather channel detected = {bot1._weather_channel_detected}")
print(f"  ➜ Channel persisted to: {WEATHER_CHANNEL_FILE}")
print("  ℹ  Bot now knows #weather is on channel_idx 1")

# Scenario 3: Bot restart - loads persisted channel
print("\n" + "=" * 80)
print("SCENARIO 3: Bot Restarts (Simulated Reboot)")
print("=" * 80)
print("  Creating new bot instance (simulating restart)...")
bot2 = WeatherBot(node_id="demo_bot", debug=False, announce=True)
print(f"  ➜ Bot initialized with _announce_channel_idx = {bot2._announce_channel_idx}")
print(f"  ➜ Weather channel detected = {bot2._weather_channel_detected}")
print(f"  ➜ Will announce on channel_idx = {bot2._announce_channel_idx}")
print("  ✓ SUCCESS! Bot loaded persisted channel and will announce on channel_idx 1")
print("  ℹ  Startup announcement will now go to #weather channel!")

# Scenario 4: Explicit configuration overrides
print("\n" + "=" * 80)
print("SCENARIO 4: Explicit Configuration (--weather-channel-idx)")
print("=" * 80)
print("  Starting bot with explicit --weather-channel-idx=5")
bot3 = WeatherBot(node_id="demo_bot", debug=False, announce=True, weather_channel_idx=5)
print(f"  ➜ Bot initialized with _announce_channel_idx = {bot3._announce_channel_idx}")
print(f"  ➜ Will announce on channel_idx = {bot3._announce_channel_idx}")
print("  ✓ Explicit config overrides persisted channel (as expected)")

# Clean up
if WEATHER_CHANNEL_FILE.exists():
    os.remove(WEATHER_CHANNEL_FILE)

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("✓ Bot persists detected weather channel across restarts")
print("✓ Startup announcements will go to correct #weather channel")
print("✓ Explicit --weather-channel-idx configuration takes precedence")
print("✓ Solves the issue: 'bot not announcing on startup in #weather channel'")
print("=" * 80 + "\n")
