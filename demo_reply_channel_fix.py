#!/usr/bin/env python3
"""
Demonstration of the fix for the weather bot reply channel issue.

This script shows how the bot now correctly replies to the channel
where messages originate, instead of broadcasting to hardcoded channels.
"""

import sys
from unittest.mock import MagicMock, patch
from meshcore import MeshCoreMessage
from weather_bot import WeatherBot


def demonstrate_fix():
    """Demonstrate the reply channel fix"""
    
    print("=" * 70)
    print("DEMONSTRATION: Weather Bot Reply Channel Fix")
    print("=" * 70)
    print()
    print("This demonstrates the fix for the issue where the bot was not")
    print("replying back to users on the correct channel.")
    print()
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "Barnsley",
                "country": "United Kingdom",
                "latitude": 53.55,
                "longitude": -1.48333
            }]
        }
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 7.1,
                "apparent_temperature": 4.0,
                "relative_humidity_2m": 85,
                "wind_speed_10m": 13.0,
                "wind_direction_10m": 246,
                "precipitation": 0.0,
                "weather_code": 3
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Create bot with configured channel 'wxtest'
        # (simulating the command: python3 weather_bot.py --channel wxtest)
        bot = WeatherBot(node_id="WX_BOT", debug=True, channel="wxtest")
        
        # Track sent messages
        sent_messages = []
        original_send = bot.mesh.send_message
        
        def track_send(content, message_type, channel):
            sent_messages.append({
                'content': content,
                'type': message_type,
                'channel': channel
            })
            return original_send(content, message_type, channel)
        
        bot.mesh.send_message = track_send
        bot.mesh.start()
        
        print("SCENARIO: User M3UXC sends weather request")
        print("-" * 70)
        print()
        print("  Command sent by user: 'Wx barnsley'")
        print("  Channel used by user: (unknown - could be any channel)")
        print("  Bot configured with: --channel wxtest")
        print()
        print("BEFORE THE FIX:")
        print("  - Bot would broadcast to 'wxtest' (hardcoded)")
        print("  - User on different channel wouldn't see the response")
        print("  - Result: Bot appears to be broken ❌")
        print()
        
        # Simulate receiving a message from M3UXC on a different channel
        # This simulates the scenario from the problem statement where
        # the user is on an unknown channel (not 'wxtest')
        incoming_msg = MeshCoreMessage(
            sender="M3UXC",
            content="Wx barnsley",
            message_type="text",
            channel="localchat"  # User is on 'localchat', not 'wxtest'
        )
        
        print("AFTER THE FIX:")
        print("  Processing message...")
        print()
        
        # Process the message
        sent_messages.clear()
        bot.handle_message(incoming_msg)
        
        # Check what channel the bot replied to
        if sent_messages:
            reply_channel = sent_messages[0]['channel']
            print(f"  - Bot detected incoming channel: '{incoming_msg.channel}'")
            print(f"  - Bot replied to: '{reply_channel}'")
            print()
            
            if reply_channel == incoming_msg.channel:
                print("  ✓ SUCCESS! Bot replied to the correct channel!")
                print("  ✓ User M3UXC will receive the response!")
            else:
                print("  ✗ ERROR: Bot replied to wrong channel")
        else:
            print("  ✗ ERROR: Bot didn't send any messages")
        
        print()
        print("-" * 70)
        print()
        
        # Demonstrate fallback behavior
        print("FALLBACK SCENARIO: Message without channel")
        print("-" * 70)
        print()
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        incoming_msg2 = MeshCoreMessage(
            sender="M3UXC",
            content="wx leeds",
            message_type="text",
            channel=None  # No channel specified
        )
        
        print("  Command sent by user: 'wx leeds'")
        print("  Channel used by user: (none)")
        print("  Bot configured with: --channel wxtest")
        print()
        print("  Processing message...")
        print()
        
        sent_messages.clear()
        bot.handle_message(incoming_msg2)
        
        if sent_messages:
            reply_channel = sent_messages[0]['channel']
            print(f"  - Bot detected no incoming channel")
            print(f"  - Bot used configured fallback: '{reply_channel}'")
            print()
            
            if reply_channel == 'wxtest':
                print("  ✓ SUCCESS! Bot used configured fallback channel!")
            else:
                print("  ✗ ERROR: Bot didn't use fallback correctly")
        
        print()
        print("-" * 70)
        print()
        
        bot.mesh.stop()


def main():
    """Run the demonstration"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Weather Bot Reply Channel Fix" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        demonstrate_fix()
        
        print("=" * 70)
        print("✅ DEMONSTRATION COMPLETE")
        print("=" * 70)
        print()
        print("Summary of the fix:")
        print("  1. Bot now detects which channel incoming messages come from")
        print("  2. Bot replies to the same channel (instead of hardcoded channel)")
        print("  3. Configured channels are used as fallback for broadcast scenarios")
        print()
        print("This ensures users receive responses on the channel they're using,")
        print("fixing the issue where the bot appeared to not be replying back.")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
