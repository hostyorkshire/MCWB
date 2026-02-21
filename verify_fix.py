#!/usr/bin/env python3
"""
Manual verification script to simulate the exact scenario from the problem statement logs.

This simulates:
1. Bot started with --channel wxtest
2. Message arrives on channel_idx 0: "Wx leeds"
3. Bot should process the message (not ignore it)
"""

from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_scenario_wxtest():
    """Test the exact scenario from the first log"""
    print("=" * 70)
    print("SCENARIO 1: Bot with --channel wxtest")
    print("=" * 70)
    print()
    print("Command: python3 weather_bot.py -n WX_BOT --port /dev/ttyUSB1")
    print("         --baud 115200 --channel wxtest -d")
    print()
    
    # Create bot with wxtest channel
    bot = WeatherBot(node_id="WX_BOT", debug=True, channel="wxtest")
    
    # Track whether message was processed by hooking into the mesh handler
    processed = []
    
    def tracking_handler(msg):
        processed.append(msg.content)
        print(f"✅ Message processed by handler: {msg.content}")
    
    # Replace the text handler in mesh to avoid API calls
    bot.mesh.message_handlers["text"] = tracking_handler
    bot.start()
    
    # Simulate the exact message from the logs:
    # [2026-02-21 03:32:42] MeshCore [WX_BOT]: LoRa RX channel msg from M3UXC on channel_idx 0: Wx leeds
    print("\nSimulating incoming message:")
    print("  [LoRa RX channel msg from M3UXC on channel_idx 0: Wx leeds]")
    print()
    
    msg = MeshCoreMessage(
        sender="M3UXC",
        content="Wx leeds",
        message_type="text",
        channel=None,  # channel_idx 0 maps to None
        channel_idx=0
    )
    
    bot.mesh.receive_message(msg)
    bot.stop()
    
    print()
    if processed:
        print("✅ SUCCESS: Message was processed (not ignored)")
        print(f"   Processed: {processed}")
    else:
        print("❌ FAILURE: Message was ignored")
    print()
    
    return len(processed) > 0


def test_scenario_weather():
    """Test the exact scenario from the second log"""
    print("=" * 70)
    print("SCENARIO 2: Bot with --channel weather")
    print("=" * 70)
    print()
    print("Command: python3 weather_bot.py -n WX_BOT --port /dev/ttyUSB1")
    print("         --baud 115200 --channel weather -d")
    print()
    
    # Create bot with weather channel
    bot = WeatherBot(node_id="WX_BOT", debug=True, channel="weather")
    
    # Track whether message was processed by hooking into the mesh handler
    processed = []
    
    def tracking_handler(msg):
        processed.append(msg.content)
        print(f"✅ Message processed by handler: {msg.content}")
    
    # Replace the text handler in mesh to avoid API calls
    bot.mesh.message_handlers["text"] = tracking_handler
    bot.start()
    
    # Simulate the exact message from the logs:
    # [2026-02-21 03:34:58] MeshCore [WX_BOT]: LoRa RX channel msg from M3UXC on channel_idx 0: Wx leeds
    print("\nSimulating incoming message:")
    print("  [LoRa RX channel msg from M3UXC on channel_idx 0: Wx leeds]")
    print()
    
    msg = MeshCoreMessage(
        sender="M3UXC",
        content="Wx leeds",
        message_type="text",
        channel=None,  # channel_idx 0 maps to None
        channel_idx=0
    )
    
    bot.mesh.receive_message(msg)
    bot.stop()
    
    print()
    if processed:
        print("✅ SUCCESS: Message was processed (not ignored)")
        print(f"   Processed: {processed}")
    else:
        print("❌ FAILURE: Message was ignored")
    print()
    
    return len(processed) > 0


def main():
    """Run manual verification"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "Manual Verification" + " " * 31 + "║")
    print("║" + " " * 16 + "Problem Statement Fix" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print("This script simulates the exact scenarios from the problem")
    print("statement logs to verify the fix works correctly.")
    print()
    
    result1 = test_scenario_wxtest()
    result2 = test_scenario_weather()
    
    print("=" * 70)
    if result1 and result2:
        print("✅ ALL SCENARIOS PASSED")
        print()
        print("Summary:")
        print("  • Bot with --channel wxtest now accepts messages on channel_idx 0")
        print("  • Bot with --channel weather now accepts messages on channel_idx 0")
        print("  • The problem 'bot is now not replying on any channel' is FIXED")
        print()
        print("Root Cause:")
        print("  Messages were arriving on channel_idx 0 (default channel) which")
        print("  has channel=None. The channel filter was rejecting these since")
        print("  None was not in ['wxtest'] or ['weather'].")
        print()
        print("Fix:")
        print("  Modified receive_message() to accept messages on channel_idx 0")
        print("  when a channel filter is set, since users typically don't")
        print("  explicitly configure channels in their radios.")
    else:
        print("❌ SOME SCENARIOS FAILED")
        if not result1:
            print("  • Scenario 1 (wxtest) failed")
        if not result2:
            print("  • Scenario 2 (weather) failed")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
