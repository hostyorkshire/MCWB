#!/usr/bin/env python3
"""
Test to check if the bot is receiving messages from weather and wxtest channels
"""

import sys
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage

def test_receiving_on_channels():
    """Test that weather bot can receive messages on weather and wxtest channels"""
    print("=" * 60)
    print("Testing weather bot receiving on weather and wxtest channels")
    print("=" * 60)
    
    # Create a weather bot configured for both weather and wxtest channels
    bot = WeatherBot(node_id="test_bot", debug=True, channel="weather,wxtest")
    
    print(f"\nBot channels configured: {bot.channels}")
    print(f"Expected: ['weather', 'wxtest']")
    print(f"Channel filter: {bot.mesh.channel_filter}")
    
    # Start the bot
    bot.start()
    
    # Test 1: Message without channel (should be processed)
    print("\n" + "=" * 60)
    print("Test 1: Message without channel")
    print("=" * 60)
    msg1 = MeshCoreMessage(
        sender="test_user",
        content="wx London",
        message_type="text",
        channel=None
    )
    bot.mesh.receive_message(msg1)
    
    # Test 2: Message on weather channel (should be processed)
    print("\n" + "=" * 60)
    print("Test 2: Message on 'weather' channel")
    print("=" * 60)
    msg2 = MeshCoreMessage(
        sender="test_user",
        content="wx Manchester",
        message_type="text",
        channel="weather"
    )
    bot.mesh.receive_message(msg2)
    
    # Test 3: Message on wxtest channel (should be processed)
    print("\n" + "=" * 60)
    print("Test 3: Message on 'wxtest' channel")
    print("=" * 60)
    msg3 = MeshCoreMessage(
        sender="test_user",
        content="wx York",
        message_type="text",
        channel="wxtest"
    )
    bot.mesh.receive_message(msg3)
    
    # Test 4: Message on different channel (what should happen?)
    print("\n" + "=" * 60)
    print("Test 4: Message on 'news' channel")
    print("=" * 60)
    msg4 = MeshCoreMessage(
        sender="test_user",
        content="wx Bristol",
        message_type="text",
        channel="news"
    )
    bot.mesh.receive_message(msg4)
    
    bot.stop()
    
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_receiving_on_channels()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
