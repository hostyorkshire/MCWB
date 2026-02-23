#!/usr/bin/env python3
"""
Demonstration: Weather bot responds to wx commands from ANY hashtag channel

This script proves that the bot accepts and responds to wx commands from:
- Channel 0 (default channel)
- Channels 1-7 (hashtag channels like #weather, #wxtest, #alerts, etc.)

Run this to confirm: python3 demo_hashtag_channels_work.py
"""

import sys
import time
from io import BytesIO
from weather_bot import WeatherBot

# Binary protocol frame codes
_RESP_CHANNEL_MSG_V3 = 0x11


class MockSerial:
    """Mock serial port that simulates MeshCore receiving messages on different channels"""
    
    def __init__(self):
        self.is_open = True
        self.in_waiting = 0
        self.buffer = BytesIO()
        self.sent_frames = []
        
    def read(self, size):
        return self.buffer.read(size)
        
    def readline(self):
        return b''
        
    def write(self, data):
        self.sent_frames.append(data)
        
    def close(self):
        self.is_open = False
        
    def inject_channel_msg_v3(self, channel_idx, sender, text):
        """Inject a message on a specific channel (V3 format)"""
        code = bytes([_RESP_CHANNEL_MSG_V3])
        chan_idx = bytes([channel_idx])
        path_len = bytes([2])
        txt_type = bytes([0])
        timestamp = int(time.time()).to_bytes(4, 'little')
        message = f"{sender}: {text}".encode('utf-8')
        
        payload = code + chan_idx + path_len + txt_type + timestamp + message
        length = len(payload) - 1
        frame = bytes([0xFE, 0xFE]) + bytes([length]) + payload
        
        self.buffer = BytesIO(frame)
        self.in_waiting = len(frame)
        return frame


def test_hashtag_channels():
    """Test that bot responds to wx commands from any hashtag channel"""
    
    print("=" * 70)
    print("DEMONSTRATION: Weather Bot Works From Any Hashtag Channel")
    print("=" * 70)
    print()
    
    # Create bot with NO channel restrictions (default behavior)
    mock_serial = MockSerial()
    bot = WeatherBot(node_id="TEST_BOT", port=None, debug=False)
    bot._ser = mock_serial
    
    # Test scenarios: Different hashtag channels sending wx commands
    test_cases = [
        (0, "DefaultUser", "wx London", "Channel 0 (default channel)"),
        (1, "WeatherUser", "wx Paris", "Channel 1 (e.g., #weather)"),
        (2, "TestUser", "wx Berlin", "Channel 2 (e.g., #wxtest)"),
        (3, "AlertUser", "wx Madrid", "Channel 3 (e.g., #alerts)"),
        (7, "RandomUser", "wx Rome", "Channel 7 (any hashtag channel)"),
    ]
    
    print("Testing bot with NO channel restrictions...")
    print(f"Bot configuration: allowed_channel_idx = {bot.allowed_channel_idx}")
    print()
    
    all_passed = True
    
    for channel_idx, sender, command, description in test_cases:
        print(f"Test: {description}")
        print(f"  Sending: '{command}' from {sender} on channel_idx={channel_idx}")
        
        # Clear previous sent frames
        mock_serial.sent_frames.clear()
        
        # Inject message on this channel
        mock_serial.inject_channel_msg_v3(channel_idx, sender, command)
        
        # Process the message by dispatching it
        try:
            # Build the payload (excluding the frame wrapper)
            code = _RESP_CHANNEL_MSG_V3
            chan_idx = channel_idx
            path_len = 2
            txt_type = 0
            timestamp = int(time.time())
            message_text = f"{sender}: {command}"
            
            # Construct V3 format: code(1) + SNR(1) + reserved(2) + channel_idx(1) + 
            #                      path_len(1) + txt_type(1) + timestamp(4) + text
            payload = bytes([
                code,           # 0x11
                50,             # SNR (dummy value)
                0, 0,           # reserved
                chan_idx,       # channel_idx
                path_len,       # path_len
                txt_type,       # txt_type
            ]) + timestamp.to_bytes(4, 'little') + message_text.encode('utf-8')
            
            bot._dispatch(payload)
            
            # Check if bot sent a response
            if len(mock_serial.sent_frames) > 0:
                print(f"  ✅ Bot responded on channel_idx={channel_idx}")
                
                # Verify the response went to the same channel
                # Frame format: CMD_SEND_CHAN_MSG has channel_idx at byte 2
                for frame in mock_serial.sent_frames:
                    if len(frame) > 5 and frame[3] == 0x03:  # CMD_SEND_CHAN_MSG
                        response_channel = frame[5]  # channel_idx position
                        if response_channel == channel_idx:
                            print(f"  ✅ Response sent to same channel_idx={channel_idx}")
                        else:
                            print(f"  ❌ Response sent to wrong channel_idx={response_channel} (expected {channel_idx})")
                            all_passed = False
            else:
                print(f"  ❌ Bot did NOT respond")
                all_passed = False
                
        except Exception as e:
            print(f"  ❌ Error processing message: {e}")
            all_passed = False
            
        print()
    
    print("=" * 70)
    if all_passed:
        print("✅ SUCCESS: Bot responds to wx commands from ALL hashtag channels!")
        print()
        print("This means:")
        print("  • Users can send 'wx [location]' from channel 0")
        print("  • Users can send 'wx [location]' from #weather (channel 1)")
        print("  • Users can send 'wx [location]' from #wxtest (channel 2)")
        print("  • Users can send 'wx [location]' from #alerts (channel 3)")
        print("  • Users can send 'wx [location]' from ANY hashtag channel (1-7)")
        print()
        print("The bot automatically replies on the same channel where the")
        print("command was received, so each user gets their response on")
        print("their preferred channel.")
    else:
        print("❌ FAILURE: Some tests did not pass")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    try:
        success = test_hashtag_channels()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error running demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
