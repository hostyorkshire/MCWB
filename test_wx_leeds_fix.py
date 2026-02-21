#!/usr/bin/env python3
"""
Test to verify the fix for "wx leeds" not being recognized.

The bug was an off-by-one error in RESP_CHANNEL_MSG_V3 frame parsing
that caused the first character of messages to be skipped, turning
"wx leeds" into "x leeds", which wouldn't match the weather command pattern.
"""

import sys
from unittest.mock import MagicMock, patch
from meshcore import MeshCore, MeshCoreMessage
from weather_bot import WeatherBot


def test_wx_leeds_command():
    """Test that 'wx leeds' command is properly recognized and processed"""
    print("=" * 70)
    print("TEST: 'wx leeds' Command Recognition (V3 Frame Format)")
    print("=" * 70)
    print()
    print("This test verifies the fix for the off-by-one error in V3 frame")
    print("parsing that was causing the first character to be skipped.")
    print()
    
    # Track whether handler was called with correct content
    handler_called = [False]
    received_content = [None]
    
    # Create a weather bot
    with patch('weather_bot.requests.get') as mock_get:
        # Mock geocoding response for Leeds
        geocoding_response = MagicMock()
        geocoding_response.json.return_value = {
            "results": [{
                "name": "Leeds",
                "country": "United Kingdom",
                "latitude": 53.8008,
                "longitude": -1.5491
            }]
        }
        geocoding_response.raise_for_status = MagicMock()
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 10.5,
                "apparent_temperature": 8.2,
                "relative_humidity_2m": 75,
                "wind_speed_10m": 15.0,
                "wind_direction_10m": 180,
                "precipitation": 0.0,
                "weather_code": 2
            }
        }
        weather_response.raise_for_status = MagicMock()
        
        # Set up mock to return different responses
        mock_get.side_effect = [geocoding_response, weather_response]
        
        # Create bot instance
        bot = WeatherBot(node_id="WX_BOT", debug=True, announce_channel="wxtest")
        
        # Wrap the original handler to track calls
        original_handler = bot.handle_message
        def tracking_handler(message: MeshCoreMessage):
            handler_called[0] = True
            received_content[0] = message.content
            return original_handler(message)
        
        bot.mesh.message_handlers["text"] = tracking_handler
        bot.mesh.start()
        
        print("Scenario: User sends 'wx leeds' on wxtest channel")
        print("-" * 70)
        print()
        
        # Simulate receiving "wx leeds" via V3 frame format
        # This is the format the bot receives when app_ver=0x03 is used
        # Frame: RESP_CHANNEL_MSG_V3 (0x11)
        # Format: SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
        
        channel_idx = 1  # wxtest channel
        snr = 20
        reserved = bytes([0, 0])
        path_len = 3
        txt_type = 1
        timestamp = (1771711343).to_bytes(4, "little")
        text = b"testuser: wx leeds"  # This is what the radio sends
        
        # Construct the V3 frame payload
        payload = bytes([0x11, snr]) + reserved + bytes([channel_idx, path_len, txt_type]) + timestamp + text
        
        print(f"Incoming V3 frame:")
        print(f"  Raw payload: {payload.hex()}")
        print(f"  Expected text: '{text.decode('utf-8')}'")
        print(f"  Expected sender: 'testuser'")
        print(f"  Expected content: 'wx leeds'")
        print()
        
        # Parse the frame (this triggers the message handling)
        bot.mesh._parse_binary_frame(payload)
        
        print()
        print("Result:")
        print("-" * 70)
        
        if handler_called[0]:
            print(f"✅ Handler WAS called!")
            print(f"   Received content: '{received_content[0]}'")
            
            # Check if it's recognized as a weather command
            location = bot.parse_weather_command(received_content[0])
            if location:
                print(f"✅ Recognized as weather command!")
                print(f"   Parsed location: '{location}'")
                
                if location.lower() == "leeds":
                    print(f"✅ Location correctly parsed as 'leeds'!")
                    print()
                    print("=" * 70)
                    print("✅ TEST PASSED - Fix is working correctly!")
                    print("=" * 70)
                    print()
                    print("The bot will now:")
                    print("  1. Geocode 'leeds' to get coordinates")
                    print("  2. Fetch weather data for Leeds")
                    print("  3. Send response back on the wxtest channel")
                    print()
                    bot.mesh.stop()
                    return True
                else:
                    print(f"❌ Location mismatch: expected 'leeds', got '{location}'")
            else:
                print(f"❌ NOT recognized as weather command!")
                print(f"   Content was: '{received_content[0]}'")
                print(f"   (Bug: first character may have been skipped)")
        else:
            print(f"❌ Handler was NOT called!")
        
        bot.mesh.stop()
    
    print()
    print("=" * 70)
    print("❌ TEST FAILED")
    print("=" * 70)
    return False


def test_before_fix_simulation():
    """Demonstrate what happened before the fix"""
    print("=" * 70)
    print("DEMONSTRATION: Before the fix (simulated)")
    print("=" * 70)
    print()
    
    # Simulate the buggy behavior
    payload_with_bug = b"x leeds"  # First character 'w' was skipped
    print(f"With the bug, 'wx leeds' became: '{payload_with_bug.decode('utf-8')}'")
    print(f"  → Does NOT match weather command pattern!")
    print(f"  → Bot would ignore the message")
    print()
    
    # Show the fix
    payload_fixed = b"wx leeds"  # All characters preserved
    print(f"With the fix, 'wx leeds' stays: '{payload_fixed.decode('utf-8')}'")
    print(f"  → DOES match weather command pattern!")
    print(f"  → Bot processes the request")
    print()


if __name__ == "__main__":
    print()
    test_before_fix_simulation()
    print()
    success = test_wx_leeds_command()
    sys.exit(0 if success else 1)
