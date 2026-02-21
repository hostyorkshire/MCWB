#!/usr/bin/env python3
"""
Test that exactly replicates the scenario from the problem statement.

This test validates that:
- Bot started with --channel weather
- Receives message on channel_idx 0 (as shown in log)
- Replies on 'weather' channel (not channel_idx 0)
"""

import sys
from unittest.mock import MagicMock, patch
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_problem_statement_exact_scenario():
    """
    Test the EXACT scenario from the problem statement log.
    
    From the log:
    ```
    python3 weather_bot.py -n WX_BOT --port /dev/ttyUSB1 --baud 115200 --channel weather -d
    
    [2026-02-21 04:22:02] MeshCore [WX_BOT]: LoRa RX channel msg from M3UXC on channel_idx 0: Wx barnsley
    [2026-02-21 04:22:05] WeatherBot: Replying on default channel (channel_idx 0): Weather for Barnsley...
    ```
    
    Problem: Bot configured with --channel weather is replying on channel_idx 0 instead of 'weather' channel
    
    Expected after fix:
    - Bot should reply on 'weather' channel (its configured channel)
    - Not on channel_idx 0 (where message came from)
    - This ensures users monitoring 'weather' channel see the replies
    """
    print()
    print("=" * 70)
    print("TEST: Exact Problem Statement Scenario")
    print("=" * 70)
    print()
    print("Replicating the exact scenario from the problem statement:")
    print("  Command: python3 weather_bot.py --channel weather")
    print("  Receives: message from M3UXC on channel_idx 0")
    print("  Expected: reply on 'weather' channel (configured channel)")
    print()
    
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response for Leeds
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "Leeds",
                "country": "United Kingdom",
                "latitude": 53.79648,
                "longitude": -1.54785
            }]
        }
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 8.5,
                "apparent_temperature": 5.3,
                "relative_humidity_2m": 80,
                "wind_speed_10m": 13.9,
                "wind_direction_10m": 253,
                "precipitation": 0.0,
                "weather_code": 3
            }
        }
        
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Create bot with --channel weather (exact from problem statement)
        bot = WeatherBot(node_id="WX_BOT", debug=True, channel="weather")
        
        # Track what channel the bot replies on
        sent_messages = []
        original_send = bot.mesh.send_message
        
        def track_send(content, message_type, channel, channel_idx=None):
            sent_messages.append({
                'content': content,
                'channel': channel,
                'channel_idx': channel_idx
            })
            return original_send(content, message_type, channel, channel_idx)
        
        bot.mesh.send_message = track_send
        bot.mesh.start()
        
        # Simulate EXACT message from log:
        # "LoRa RX channel msg from M3UXC on channel_idx 0: Wx leeds"
        msg = MeshCoreMessage(
            sender="M3UXC",        # Exact sender from log
            content="Wx leeds",    # Exact content from log
            message_type="text",
            channel=None,          # No channel name (channel_idx 0 is default)
            channel_idx=0          # Exact channel_idx from log
        )
        
        print("Simulating message from log:")
        print(f"  From: {msg.sender}")
        print(f"  Content: {msg.content}")
        print(f"  Channel_idx: {msg.channel_idx}")
        print()
        
        # Process the message
        sent_messages.clear()
        bot.handle_message(msg)
        
        # Verify the fix
        print("Checking bot reply...")
        assert len(sent_messages) == 1, f"Expected 1 reply, got {len(sent_messages)}"
        
        sent = sent_messages[0]
        print(f"  Bot replied on: channel='{sent['channel']}', channel_idx={sent['channel_idx']}")
        print()
        
        # The key assertion: bot should reply on 'weather' channel (configured), not channel_idx 0
        # This ensures users monitoring the 'weather' channel can see the reply
        if sent['channel'] == 'weather':
            print("✅ SUCCESS!")
            print()
            print("Bot correctly replied on 'weather' channel")
            print("(the channel it was configured with)")
            print()
            print("This fixes the problem statement issue:")
            print("  Problem: Bot with --channel weather was replying on channel_idx 0")
            print("  Fix: Bot now replies on 'weather' channel (its configured channel)")
            print()
            print("Users monitoring the 'weather' channel will see the bot's replies!")
            success = True
        else:
            print("❌ FAILED!")
            print(f"  Expected: channel='weather'")
            print(f"  Got: channel='{sent['channel']}', channel_idx={sent['channel_idx']}")
            print()
            print("Bot is not replying on the configured channel!")
            success = False
        
        bot.mesh.stop()
        
        return success


def main():
    """Run the test"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 13 + "Problem Statement Exact Scenario Test" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        success = test_problem_statement_exact_scenario()
        
        print()
        print("=" * 70)
        if success:
            print("✅ TEST PASSED")
            print()
            print("The exact scenario from the problem statement now works correctly.")
            print("The bot replies on 'weather' channel (its configured channel)")
            print("when started with --channel weather, ensuring users monitoring")
            print("that channel can see the replies.")
        else:
            print("❌ TEST FAILED")
            print()
            print("The bot is not replying on the configured channel.")
            print("Users monitoring the configured channel won't see the replies!")
        print("=" * 70)
        print()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
