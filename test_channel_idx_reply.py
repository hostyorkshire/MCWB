#!/usr/bin/env python3
"""
Test script to verify that the bot properly replies using configured channel
when one is set, otherwise replies on incoming channel_idx.

This test verifies:
1. Bot with configured channel uses that channel (dedicated service mode)
2. Bot without configured channel replies on incoming channel_idx
"""

import sys
from unittest.mock import MagicMock, patch
from meshcore import MeshCore, MeshCoreMessage
from weather_bot import WeatherBot


def test_reply_with_configured_channel():
    """
    Test that bot with configured channel uses that channel,
    not the incoming channel_idx.
    """
    print("=" * 60)
    print("TEST: Bot with Configured Channel")
    print("=" * 60)
    
    # Track what was sent
    sent_messages = []
    
    # Create a bot with a configured channel
    bot = WeatherBot(node_id="WX_BOT", debug=True, channel="wxtest")
    
    # Mock the serial port to prevent actual transmission
    bot.mesh._serial = MagicMock()
    bot.mesh._serial.is_open = True
    
    # Patch the weather API calls to return mock data
    with patch.object(bot, 'geocode_location') as mock_geocode, \
         patch.object(bot, 'get_weather') as mock_weather:
        
        # Mock successful weather lookup
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
        
        # Capture what gets sent
        def capture_write(data):
            sent_messages.append(data)
        
        bot.mesh._serial.write = capture_write
        
        # Simulate receiving a message on channel_idx=5
        incoming_message = MeshCoreMessage(
            sender="M3UXC",
            content="wx barnsley",
            message_type="text",
            channel=None,  # No name mapping
            channel_idx=5  # Raw channel_idx
        )
        
        print(f"\nReceived message on channel_idx={incoming_message.channel_idx}")
        print(f"Bot's configured channel: {bot.channels}")
        
        # Process the message
        bot.handle_message(incoming_message)
        
        # Debug: print all sent messages
        print(f"\nTotal frames sent: {len(sent_messages)}")
        
        # Verify at least one message was sent
        assert len(sent_messages) > 0, "No messages were sent"
        
        # Find the weather response frame (should be the longest one with actual message content)
        # The CMD_SYNC_NEXT_MSG frames are only 4 bytes: 0x3C + 0x01 0x00 + 0x0A
        weather_frames = [f for f in sent_messages if len(f) > 10]
        
        assert len(weather_frames) > 0, "No weather response frame found"
        
        # Check the weather response frame
        last_frame = weather_frames[-1]
        
        # Parse the frame to extract channel_idx
        # Frame format: 0x3C + length(2 bytes) + payload
        # Payload for CMD_SEND_CHAN_MSG: code(1) + txt_type(1) + channel_idx(1) + timestamp(4) + text
        if len(last_frame) >= 6:
            sent_channel_idx = last_frame[5]  # byte 5 is the channel_idx
            
            print(f"Sent reply on channel_idx={sent_channel_idx}")
            
            # Bot should use configured channel 'wxtest' (channel_idx 1), not incoming channel_idx 5
            assert sent_channel_idx == 1, \
                f"Expected reply on channel_idx 1 (configured 'wxtest'), but sent on {sent_channel_idx}"
            
            print(f"✓ Bot correctly used configured channel 'wxtest' (channel_idx {sent_channel_idx})")
            print(f"✓ Incoming channel_idx 5 was ignored (dedicated service mode)")
        else:
            raise AssertionError(f"Frame too short: {len(last_frame)} bytes")
    
    print()


def test_reply_with_channel_name_still_works():
    """
    Test that the bot still works correctly when replying to a named channel.
    This ensures backward compatibility.
    """
    print("=" * 60)
    print("TEST: Reply with Named Channel (Backward Compatibility)")
    print("=" * 60)
    
    sent_messages = []
    
    # Create a bot with a configured channel
    bot = WeatherBot(node_id="WX_BOT", debug=True, channel="wxtest")
    
    # Mock the serial port
    bot.mesh._serial = MagicMock()
    bot.mesh._serial.is_open = True
    
    # Patch the weather API calls
    with patch.object(bot, 'geocode_location') as mock_geocode, \
         patch.object(bot, 'get_weather') as mock_weather:
        
        mock_geocode.return_value = {
            "name": "Leeds",
            "country": "United Kingdom",
            "latitude": 53.8,
            "longitude": -1.5
        }
        
        mock_weather.return_value = {
            "current": {
                "temperature_2m": 10.0,
                "apparent_temperature": 8.0,
                "relative_humidity_2m": 75,
                "wind_speed_10m": 15.0,
                "wind_direction_10m": 180,
                "precipitation": 0.0,
                "weather_code": 1
            }
        }
        
        # Capture sent messages
        def capture_write(data):
            sent_messages.append(data)
        
        bot.mesh._serial.write = capture_write
        
        # First, send a message on a named channel to establish the mapping
        # This simulates the bot sending on 'localchat' which gets mapped to idx 1
        bot.mesh.send_message("test", "text", "localchat")
        
        # Now simulate receiving a message on that named channel
        incoming_message = MeshCoreMessage(
            sender="USER",
            content="wx leeds",
            message_type="text",
            channel="localchat",
            channel_idx=1  # Matches the mapping
        )
        
        print(f"\nReceived message on channel '{incoming_message.channel}' (idx={incoming_message.channel_idx})")
        
        # Clear sent messages to focus on the reply
        sent_messages.clear()
        
        # Process the message
        bot.handle_message(incoming_message)
        
        # Verify a message was sent
        assert len(sent_messages) > 0, "No reply was sent"
        
        # The bot should reply on channel_idx 1 (either through the name or the idx)
        last_frame = sent_messages[-1]
        if len(last_frame) >= 6:
            sent_channel_idx = last_frame[5]
            
            print(f"Sent reply on channel_idx={sent_channel_idx}")
            
            # Should reply on the same channel_idx
            assert sent_channel_idx == 1, \
                f"Expected reply on channel_idx 1, but sent on {sent_channel_idx}"
            
            print(f"✓ Bot correctly replied on channel_idx {sent_channel_idx}")
            print(f"✓ Named channels still work correctly")
    
    print()


def test_reply_without_configured_channel():
    """
    Test that bot WITHOUT configured channel replies on incoming channel_idx.
    """
    print("=" * 60)
    print("TEST: Bot WITHOUT Configured Channel")
    print("=" * 60)
    
    # Track what was sent
    sent_messages = []
    
    # Create a bot WITHOUT configured channel
    bot = WeatherBot(node_id="WX_BOT", debug=True, channel=None)
    
    # Mock the serial port to prevent actual transmission
    bot.mesh._serial = MagicMock()
    bot.mesh._serial.is_open = True
    
    # Patch the weather API calls to return mock data
    with patch.object(bot, 'geocode_location') as mock_geocode, \
         patch.object(bot, 'get_weather') as mock_weather:
        
        # Mock successful weather lookup
        mock_geocode.return_value = {
            "name": "York",
            "country": "United Kingdom",
            "latitude": 53.96,
            "longitude": -1.08
        }
        
        mock_weather.return_value = {
            "current": {
                "temperature_2m": 9.0,
                "apparent_temperature": 7.0,
                "relative_humidity_2m": 80,
                "wind_speed_10m": 10.0,
                "wind_direction_10m": 200,
                "precipitation": 0.0,
                "weather_code": 2
            }
        }
        
        # Capture what gets sent
        def capture_write(data):
            sent_messages.append(data)
        
        bot.mesh._serial.write = capture_write
        
        # Simulate receiving a message on channel_idx=5
        incoming_message = MeshCoreMessage(
            sender="M3UXC",
            content="wx york",
            message_type="text",
            channel=None,  # No name mapping
            channel_idx=5  # Raw channel_idx
        )
        
        print(f"\nReceived message on channel_idx={incoming_message.channel_idx}")
        print(f"Bot's configured channel: {bot.channels}")
        
        # Process the message
        bot.handle_message(incoming_message)
        
        # Verify at least one message was sent
        assert len(sent_messages) > 0, "No messages were sent"
        
        # Find the weather response frame
        weather_frames = [f for f in sent_messages if len(f) > 10]
        assert len(weather_frames) > 0, "No weather response frame found"
        
        # Check the weather response frame
        last_frame = weather_frames[-1]
        
        # Parse the frame to extract channel_idx
        if len(last_frame) >= 6:
            sent_channel_idx = last_frame[5]  # byte 5 is the channel_idx
            
            print(f"Sent reply on channel_idx={sent_channel_idx}")
            
            # Bot should reply on incoming channel_idx 5 (no configured channel)
            assert sent_channel_idx == 5, \
                f"Expected reply on channel_idx 5 (incoming), but sent on {sent_channel_idx}"
            
            print(f"✓ Bot correctly replied on incoming channel_idx {sent_channel_idx}")
            print(f"✓ No configured channel, so incoming channel_idx was used")
        else:
            raise AssertionError(f"Frame too short: {len(last_frame)} bytes")
    
    print()


def test_fallback_to_configured_channel():
    """
    Test that the bot falls back to configured channel when there's no
    channel_idx or channel name in the incoming message.
    """
    print("=" * 60)
    print("TEST: Fallback to Configured Channel")
    print("=" * 60)
    
    sent_messages = []
    
    # Create a bot with a configured channel
    bot = WeatherBot(node_id="WX_BOT", debug=True, channel="wxtest")
    
    # Mock the serial port
    bot.mesh._serial = MagicMock()
    bot.mesh._serial.is_open = True
    
    # Patch the weather API calls
    with patch.object(bot, 'geocode_location') as mock_geocode, \
         patch.object(bot, 'get_weather') as mock_weather:
        
        mock_geocode.return_value = {
            "name": "York",
            "country": "United Kingdom",
            "latitude": 53.96,
            "longitude": -1.08
        }
        
        mock_weather.return_value = {
            "current": {
                "temperature_2m": 9.0,
                "apparent_temperature": 7.0,
                "relative_humidity_2m": 80,
                "wind_speed_10m": 10.0,
                "wind_direction_10m": 270,
                "precipitation": 0.0,
                "weather_code": 2
            }
        }
        
        # Capture sent messages
        def capture_write(data):
            sent_messages.append(data)
        
        bot.mesh._serial.write = capture_write
        
        # Simulate receiving a message with NO channel info
        incoming_message = MeshCoreMessage(
            sender="OLDUSER",
            content="wx york",
            message_type="text",
            channel=None,
            channel_idx=None  # No channel info at all
        )
        
        print(f"\nReceived message with no channel info")
        print(f"Bot's configured channel: {bot.channels}")
        
        # Process the message
        bot.handle_message(incoming_message)
        
        # Verify a message was sent
        assert len(sent_messages) > 0, "No reply was sent"
        
        # The bot should fall back to its configured channel 'wxtest'
        # which will be mapped to channel_idx 1 (first named channel)
        last_frame = sent_messages[-1]
        if len(last_frame) >= 6:
            sent_channel_idx = last_frame[5]
            
            print(f"Sent reply on channel_idx={sent_channel_idx}")
            
            # Should use channel_idx 1 (mapped from 'wxtest')
            assert sent_channel_idx == 1, \
                f"Expected fallback to channel_idx 1 (wxtest), but sent on {sent_channel_idx}"
            
            print(f"✓ Bot correctly fell back to configured channel 'wxtest'")
            print(f"✓ Fallback behavior works as expected")
    
    print()


def main():
    """Run all channel_idx reply tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "Channel Index Reply Tests" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_reply_with_configured_channel()
        test_reply_without_configured_channel()
        test_reply_with_channel_name_still_works()
        test_fallback_to_configured_channel()

        print("=" * 60)
        print("✅ All channel index reply tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  • Bot with configured channel uses that channel (dedicated service)")
        print("  • Bot without configured channel replies on incoming channel_idx")
        print("  • Named channels still work correctly (backward compatible)")
        print("  • Fallback to configured channel works when no channel info")
        print()

        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
