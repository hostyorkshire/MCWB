#!/usr/bin/env python3
"""
Validation script that simulates the EXACT scenario from the problem statement.

This proves the fix resolves the user's issue.
"""

from meshcore import MeshCore, MeshCoreMessage
from weather_bot import WeatherBot
from unittest.mock import MagicMock, patch


def simulate_problem_statement():
    """
    Simulate the exact scenario from the problem statement logs:
    - User M3UXC sends "Wx barnsley" 
    - Bot is running with: --channel wxtest
    - Before fix: Bot sends on wrong channel_idx, user doesn't see reply
    - After fix: Bot sends on same channel_idx, user sees reply
    """
    print("=" * 70)
    print("VALIDATION: Problem Statement Scenario")
    print("=" * 70)
    print()
    print("User's Setup:")
    print("  Command: python3 weather_bot.py -n WX_BOT --port /dev/ttyUSB1")
    print("           --baud 115200 --channel wxtest -d")
    print()
    print("User M3UXC: Sends 'Wx barnsley' on their channel")
    print("            (Let's say they're on channel_idx=2)")
    print()
    
    # Create bot exactly as user did
    bot = WeatherBot(node_id="WX_BOT", debug=True, channel="wxtest")
    
    # Mock serial
    bot.mesh._serial = MagicMock()
    bot.mesh._serial.is_open = True
    
    sent_frames = []
    
    def capture_write(data):
        sent_frames.append(data)
    
    bot.mesh._serial.write = capture_write
    
    # Mock weather APIs
    with patch.object(bot, 'geocode_location') as mock_geocode, \
         patch.object(bot, 'get_weather') as mock_weather:
        
        # Exact data from logs
        mock_geocode.return_value = {
            "name": "Barnsley",
            "country": "United Kingdom",
            "latitude": 53.55,
            "longitude": -1.48333
        }
        
        mock_weather.return_value = {
            "current": {
                "temperature_2m": 7.0,
                "apparent_temperature": 4.0,
                "relative_humidity_2m": 86,
                "wind_speed_10m": 12.6,
                "wind_direction_10m": 243,
                "precipitation": 0.0,
                "weather_code": 3  # Overcast
            }
        }
        
        # Simulate the EXACT incoming message from logs
        # "LoRa RX channel msg from M3UXC: Wx barnsley"
        # The user is on some channel (let's say channel_idx=2)
        incoming = MeshCoreMessage(
            sender="M3UXC",
            content="Wx barnsley",  # Exact content from logs (case preserved)
            message_type="text",
            channel=None,       # Bot doesn't know the channel name
            channel_idx=2       # But it knows the raw index
        )
        
        print("Processing incoming message...")
        print(f"  From: {incoming.sender}")
        print(f"  Content: {incoming.content}")
        print(f"  channel: {incoming.channel}")
        print(f"  channel_idx: {incoming.channel_idx}")
        print()
        
        # Process the message
        bot.handle_message(incoming)
        
        # Check the response
        weather_frames = [f for f in sent_frames if len(f) > 10]
        
        if not weather_frames:
            print("❌ FAILED: No weather response was sent")
            return False
        
        # Get the channel_idx from the sent frame
        frame = weather_frames[-1]
        sent_idx = frame[5]  # byte 5 is the channel_idx
        
        print("Response sent:")
        print(f"  channel_idx: {sent_idx}")
        print()
        
        # Verification
        print("VERIFICATION:")
        print(f"  Incoming channel_idx: {incoming.channel_idx}")
        print(f"  Outgoing channel_idx: {sent_idx}")
        
        if sent_idx == incoming.channel_idx:
            print()
            print("✅ SUCCESS!")
            print("   Bot replied on the SAME channel_idx it received from")
            print("   User M3UXC will see the reply!")
            print()
            print("Expected log output:")
            print(f"   [LoRa RX channel msg from M3UXC on channel_idx {incoming.channel_idx}: Wx barnsley]")
            print(f"   [Replying on channel_idx {sent_idx}: Weather for Barnsley...]")
            print(f"   [LoRa TX channel msg (idx={sent_idx}): Weather for Barnsley...]")
            return True
        else:
            print()
            print("❌ FAILED!")
            print(f"   Bot replied on channel_idx {sent_idx}")
            print(f"   But message came from channel_idx {incoming.channel_idx}")
            print("   User M3UXC will NOT see the reply!")
            return False


def main():
    """Main validation"""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Problem Statement Validation" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    success = simulate_problem_statement()
    
    print()
    print("=" * 70)
    if success:
        print("✅ Fix validated - Problem statement scenario RESOLVED")
    else:
        print("❌ Fix validation FAILED")
    print("=" * 70)
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
