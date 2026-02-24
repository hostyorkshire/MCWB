#!/usr/bin/env python3
"""
Demonstration that shows how the fix prevents garbled messages from being logged.
This simulates the exact scenario from the issue report.
"""

from weather_bot import WeatherBot
import io
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from contextlib import redirect_stdout
import time


def simulate_message_reception():
    """Simulate receiving messages like in the problem statement"""
    
    print("=" * 70)
    print("DEMONSTRATION: Invalid Channel Index Filtering")
    print("=" * 70)
    print()
    print("Simulating the scenario from the issue report where messages from")
    print("encrypted/invalid channels were showing up as garbled text...")
    print()
    
    bot = WeatherBot(debug=True)
    
    # Valid message on channel 0 (like in the log: "channel_idx=0 M3UXC/M: Wx leeds")
    print("\n1. VALID message on channel 0:")
    print("   " + "-" * 60)
    ts = int(time.time()).to_bytes(4, "little")
    valid_payload = bytes([0x88, 0, 0x05, 0x00]) + ts + b"M3UXC/M: Wx leeds"
    
    channel_idx, text = bot._parse_channel_message(valid_payload)
    print(f"   Parsed: channel_idx={channel_idx}, text=\"{text}\"")
    if channel_idx is not None:
        print(f"   ✅ This message would be processed correctly")
    
    # Invalid message on channel 49 (like in the log: "channel_idx=49 unknown: p...")
    print("\n2. ENCRYPTED/GARBLED message with channel_idx=49:")
    print("   " + "-" * 60)
    garbled_payload = bytes([0x88, 49, 0x05, 0x00]) + ts + b"\x70\x20\x0a\x6a\x36\x4c\x48\x0a"
    
    channel_idx, text = bot._parse_channel_message(garbled_payload)
    print(f"   Parsed: channel_idx={channel_idx}, text={repr(text)}")
    if channel_idx is None:
        print(f"   ✅ This garbled message is now BLOCKED!")
    else:
        print(f"   ❌ This shouldn't happen - garbled message leaked through!")
    
    # Invalid message on channel 50 (like in the log: "channel_idx=50 unknown: Y/7*M...")
    print("\n3. ENCRYPTED/GARBLED message with channel_idx=50:")
    print("   " + "-" * 60)
    garbled_payload2 = bytes([0x88, 50, 0x05, 0x00]) + ts + b"\x59\x2f\x37\x2a\x4d\x2e\x52"
    
    channel_idx, text = bot._parse_channel_message(garbled_payload2)
    print(f"   Parsed: channel_idx={channel_idx}, text={repr(text)}")
    if channel_idx is None:
        print(f"   ✅ This garbled message is now BLOCKED!")
    else:
        print(f"   ❌ This shouldn't happen - garbled message leaked through!")
    
    print()
    print("=" * 70)
    print("RESULT: Garbled messages with invalid channel indices are filtered!")
    print("=" * 70)
    print()
    print("Before the fix:")
    print("  [21:37:00] channel_idx=49 unknown: p j6LH  ← Confusing!")
    print("  [21:37:09] channel_idx=50 unknown: Y/7*M  ← Confusing!")
    print()
    print("After the fix:")
    print("  (no garbled messages in logs)  ← Clean!")
    print()


if __name__ == "__main__":
    simulate_message_reception()
