#!/usr/bin/env python3
"""
Test to reproduce the problem statement issue
"""

import sys
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage

def test_multi_channel_broadcast():
    """Test that weather bot broadcasts correctly to multiple channels"""
    print("=" * 60)
    print("Testing weather bot with weather and wxtest channels")
    print("=" * 60)
    
    # Create a weather bot configured for both weather and wxtest channels
    bot = WeatherBot(node_id="test_bot", debug=True, channel="weather,wxtest")
    
    print(f"\nBot channels configured: {bot.channels}")
    print(f"Expected: ['weather', 'wxtest']")
    
    # Start the bot
    bot.start()
    
    # Simulate a weather request
    msg = MeshCoreMessage(
        sender="test_user",
        content="wx London",
        message_type="text"
    )
    
    print("\nSimulating weather request: wx London")
    print("=" * 60)
    
    # Process the message (this should trigger a response to both channels)
    bot.handle_message(msg)
    
    bot.stop()
    
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_multi_channel_broadcast()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
