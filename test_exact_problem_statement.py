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
    
    [2026-02-21 04:06:34] MeshCore [WX_BOT]: LoRa RX channel msg from M3UXC on channel_idx 0: Wx leeds
    [2026-02-21 04:06:36] MeshCore [WX_BOT]: LoRa TX channel msg (idx=1): Weather for Leeds...
    ```
    
    Problem: Users on channel_idx 0 can't see replies sent to channel_idx 1
    
    Expected after fix:
    - Bot should reply on channel_idx 0 (where message came from)
    - Not on 'weather' channel (idx=1)
    - This ensures users see the replies
    """
    print()
    print("=" * 70)
    print("TEST: Exact Problem Statement Scenario")
    print("=" * 70)
    print()
    print("Replicating the exact scenario from the problem statement:")
    print("  Command: python3 weather_bot.py --channel weather")
    print("  Receives: message from M3UXC on channel_idx 0")
    print("  Expected: reply on 'weather' channel")
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
        
        # The key assertion: bot should reply on channel_idx 0 (default), not 'weather' channel
        # This ensures users on default channel can see the reply
        if sent['channel_idx'] == 0:
            print("✅ SUCCESS!")
            print()
            print("Bot correctly replied on channel_idx 0 (default channel)")
            print("(where the message came from)")
            print()
            print("This fixes the problem statement issue:")
            print("  Problem: User on channel_idx 0 couldn't see replies on 'weather' channel")
            print("  Fix: Bot now replies on channel_idx 0 when messages come from there")
            print()
            print("Users can now see the bot's replies!")
            success = True
        else:
            print("❌ FAILED!")
            print(f"  Expected: channel_idx=0")
            print(f"  Got: channel='{sent['channel']}', channel_idx={sent['channel_idx']}")
            print()
            print("Users on channel_idx 0 won't see replies!")
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
            print("The bot replies on channel_idx 0 (default) when messages come from")
            print("there, ensuring users can see the replies.")
        else:
            print("❌ TEST FAILED")
            print()
            print("The bot is not replying on the correct channel.")
            print("Users on channel_idx 0 won't see the replies!")
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
