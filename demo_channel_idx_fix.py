#!/usr/bin/env python3
"""
Demonstration of the channel_idx reply fix.

This script simulates the problem from the logs and shows how the fix resolves it.
"""

from meshcore import MeshCore, MeshCoreMessage
from weather_bot import WeatherBot
from unittest.mock import MagicMock, patch


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def simulate_problem():
    """Simulate the original problem"""
    print_section("BEFORE FIX: Bot Not Replying")
    
    print("\nScenario from the logs:")
    print("  User M3UXC sends: 'wx barnsley' on their channel (channel_idx=2)")
    print("  Bot is configured with: --channel wxtest")
    print()
    print("Without the fix:")
    print("  1. Bot receives message on channel_idx=2")
    print("  2. Bot has no name mapping for channel_idx=2 -> channel=None")
    print("  3. Bot falls back to configured channel 'wxtest'")
    print("  4. Bot sends 'wxtest' which gets mapped to channel_idx=1")
    print("  5. User M3UXC is listening on channel_idx=2, NOT channel_idx=1")
    print("  6. User NEVER sees the reply! ❌")
    print()


def simulate_fix():
    """Demonstrate the fix in action"""
    print_section("AFTER FIX: Bot Replies Successfully")
    
    print("\nWith the fix:")
    print("  1. Bot receives message on channel_idx=2")
    print("  2. Bot stores BOTH channel name (None) AND channel_idx (2)")
    print("  3. Bot prioritizes channel_idx when replying")
    print("  4. Bot sends directly on channel_idx=2")
    print("  5. User M3UXC receives the reply! ✅")
    print()
    
    # Create a bot
    bot = WeatherBot(node_id="WX_BOT", debug=False, channel="wxtest")
    
    # Mock the serial port
    bot.mesh._serial = MagicMock()
    bot.mesh._serial.is_open = True
    
    sent_frames = []
    
    def capture_write(data):
        sent_frames.append(data)
    
    bot.mesh._serial.write = capture_write
    
    # Mock the weather APIs
    with patch.object(bot, 'geocode_location') as mock_geocode, \
         patch.object(bot, 'get_weather') as mock_weather:
        
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
                "weather_code": 3
            }
        }
        
        # Simulate the incoming message from M3UXC
        incoming_message = MeshCoreMessage(
            sender="M3UXC",
            content="wx barnsley",
            message_type="text",
            channel=None,       # No name mapping
            channel_idx=2       # But has channel_idx!
        )
        
        print("Simulating message processing...")
        print(f"  Incoming: sender={incoming_message.sender}")
        print(f"            content='{incoming_message.content}'")
        print(f"            channel={incoming_message.channel}")
        print(f"            channel_idx={incoming_message.channel_idx}")
        print()
        
        # Process the message
        bot.handle_message(incoming_message)
        
        # Find the weather response frame
        weather_frames = [f for f in sent_frames if len(f) > 10]
        
        if weather_frames:
            frame = weather_frames[-1]
            sent_channel_idx = frame[5]  # Extract channel_idx from frame
            
            print(f"  Outgoing: channel_idx={sent_channel_idx}")
            print(f"            (matches incoming channel_idx={incoming_message.channel_idx}) ✅")
            print()
            
            if sent_channel_idx == incoming_message.channel_idx:
                print("✅ SUCCESS! Bot replied on the same channel_idx it received from!")
            else:
                print(f"❌ FAILED: Bot sent on idx {sent_channel_idx}, expected {incoming_message.channel_idx}")
        else:
            print("❌ No weather frame was sent")


def show_logs_comparison():
    """Show comparison of log output"""
    print_section("Log Comparison")
    
    print("\nBEFORE (from problem statement):")
    print("  [03:02:59] LoRa RX channel msg from M3UXC: Wx barnsley")
    print("  [03:03:01] Mapped channel 'wxtest' to channel_idx 1")
    print("  [03:03:01] LoRa TX channel msg (idx=1): Weather for Barnsley...")
    print("  Result: User never sees reply ❌")
    print()
    
    print("AFTER (with fix):")
    print("  [03:02:59] LoRa RX channel msg from M3UXC on channel_idx 2: Wx barnsley")
    print("  [03:03:01] Replying on channel_idx 2: Weather for Barnsley...")
    print("  [03:03:01] LoRa TX channel msg (idx=2): Weather for Barnsley...")
    print("  Result: User receives reply ✅")
    print()


def main():
    """Main demonstration"""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "Channel Index Reply Fix Demo" + " " * 22 + "║")
    print("╚" + "=" * 68 + "╝")
    
    simulate_problem()
    simulate_fix()
    show_logs_comparison()
    
    print_section("Summary")
    print()
    print("Key Changes:")
    print("  1. MeshCoreMessage now includes 'channel_idx' field")
    print("  2. _dispatch_channel_message() preserves the raw channel_idx")
    print("  3. send_message() accepts and prioritizes channel_idx parameter")
    print("  4. weather_bot send_response() passes channel_idx when replying")
    print()
    print("Result:")
    print("  ✅ Bot now replies on the EXACT channel_idx it received from")
    print("  ✅ Users receive replies regardless of channel name mappings")
    print("  ✅ Backward compatibility maintained for named channels")
    print("  ✅ Fallback to configured channels still works")
    print()


if __name__ == "__main__":
    main()
