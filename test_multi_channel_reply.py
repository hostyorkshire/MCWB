#!/usr/bin/env python3
"""
Comprehensive test to verify the weather bot correctly replies on all channel_idx values.

This test validates that the bot:
1. Receives messages on channel_idx 0-7
2. Replies on the SAME channel_idx where each message came from
3. Works correctly with both RESP_CHANNEL_MSG and RESP_CHANNEL_MSG_V3 binary formats

This addresses the issue: "It's still only replying to LoRa TX channel msg (idx=0)"
"""

import sys
import time
from io import BytesIO
from weather_bot import WeatherBot
from meshcore import _RESP_CHANNEL_MSG, _RESP_CHANNEL_MSG_V3


class MockSerial:
    """Mock serial port that simulates the MeshCore binary protocol"""
    
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
        
    def inject_channel_msg(self, channel_idx, sender, text):
        """Inject a RESP_CHANNEL_MSG frame (older format)"""
        code = bytes([_RESP_CHANNEL_MSG])  # 0x08
        chan_idx = bytes([channel_idx])
        path_len = bytes([2])
        txt_type = bytes([0])
        timestamp = int(time.time()).to_bytes(4, 'little')
        message = f"{sender}: {text}".encode('utf-8')
        
        payload = code + chan_idx + path_len + txt_type + timestamp + message
        frame = bytes([0x3E]) + len(payload).to_bytes(2, 'little') + payload
        
        self.buffer = BytesIO(frame)
        self.in_waiting = len(frame)
        return frame
        
    def inject_channel_msg_v3(self, channel_idx, sender, text):
        """Inject a RESP_CHANNEL_MSG_V3 frame (newer format with SNR)"""
        code = bytes([_RESP_CHANNEL_MSG_V3])  # 0x11
        snr = bytes([10])
        reserved = bytes([0, 0])
        chan_idx = bytes([channel_idx])
        path_len = bytes([2])
        txt_type = bytes([0])
        timestamp = int(time.time()).to_bytes(4, 'little')
        message = f"{sender}: {text}".encode('utf-8')
        
        payload = code + snr + reserved + chan_idx + path_len + txt_type + timestamp + message
        frame = bytes([0x3E]) + len(payload).to_bytes(2, 'little') + payload
        
        self.buffer = BytesIO(frame)
        self.in_waiting = len(frame)
        return frame


def setup_bot():
    """Create a weather bot with mocked serial and API"""
    bot = WeatherBot(node_id='WX_BOT', debug=False, serial_port='/dev/mock', baud_rate=9600)
    
    # Replace serial with mock
    mock_serial = MockSerial()
    bot.mesh._serial = mock_serial
    
    # Mock weather API
    bot.geocode_location = lambda loc: {
        'name': 'London', 
        'country': 'GB', 
        'latitude': 51.5074, 
        'longitude': -0.1278
    }
    bot.get_weather = lambda lat, lon: {
        'current': {
            'temperature_2m': 15.5,
            'apparent_temperature': 14.2,
            'relative_humidity_2m': 70,
            'wind_speed_10m': 10.5,
            'wind_direction_10m': 180,
            'precipitation': 0.0,
            'weather_code': 1
        }
    }
    
    return bot, mock_serial


def extract_reply_channel(sent_frames):
    """Extract the channel_idx from sent SEND_CHAN_MSG frames"""
    for frame in sent_frames:
        if len(frame) > 5 and frame[3] == 3:  # CMD_SEND_CHAN_MSG = 3
            return frame[5]  # channel_idx is at byte 5
    return None


def test_channel_msg_format():
    """Test with RESP_CHANNEL_MSG (older format without SNR)"""
    print("\n" + "="*70)
    print("TEST: RESP_CHANNEL_MSG Format (older format)")
    print("="*70)
    
    bot, mock_serial = setup_bot()
    results = []
    
    # Test all channel indices 0-7
    for channel_idx in range(8):
        mock_serial.sent_frames = []
        
        # Inject incoming message
        frame = mock_serial.inject_channel_msg(channel_idx, 'USER1', 'wx London')
        bot.mesh._parse_binary_frame(frame[3:])
        
        # Check reply
        reply_idx = extract_reply_channel(mock_serial.sent_frames)
        
        success = (reply_idx == channel_idx)
        results.append(success)
        
        status = "✅" if success else "❌"
        print(f"  Channel {channel_idx}: Received={channel_idx}, Replied={reply_idx} {status}")
    
    return all(results)


def test_channel_msg_v3_format():
    """Test with RESP_CHANNEL_MSG_V3 (newer format with SNR)"""
    print("\n" + "="*70)
    print("TEST: RESP_CHANNEL_MSG_V3 Format (newer format with SNR)")
    print("="*70)
    
    bot, mock_serial = setup_bot()
    results = []
    
    # Test all channel indices 0-7
    for channel_idx in range(8):
        mock_serial.sent_frames = []
        
        # Inject incoming message
        frame = mock_serial.inject_channel_msg_v3(channel_idx, 'USER1', 'wx London')
        bot.mesh._parse_binary_frame(frame[3:])
        
        # Check reply
        reply_idx = extract_reply_channel(mock_serial.sent_frames)
        
        success = (reply_idx == channel_idx)
        results.append(success)
        
        status = "✅" if success else "❌"
        print(f"  Channel {channel_idx}: Received={channel_idx}, Replied={reply_idx} {status}")
    
    return all(results)


def test_mixed_channels():
    """Test that the bot handles multiple messages on different channels correctly"""
    print("\n" + "="*70)
    print("TEST: Mixed Channel Messages (simulating real mesh traffic)")
    print("="*70)
    
    bot, mock_serial = setup_bot()
    
    test_cases = [
        (0, 'USER_A', 'wx London'),
        (2, 'USER_B', 'wx Manchester'),
        (1, 'USER_C', 'wx York'),
        (3, 'USER_D', 'wx Leeds'),
        (0, 'USER_E', 'wx Birmingham'),
    ]
    
    results = []
    for channel_idx, sender, message in test_cases:
        mock_serial.sent_frames = []
        
        # Use V3 format (most common)
        frame = mock_serial.inject_channel_msg_v3(channel_idx, sender, message)
        bot.mesh._parse_binary_frame(frame[3:])
        
        reply_idx = extract_reply_channel(mock_serial.sent_frames)
        success = (reply_idx == channel_idx)
        results.append(success)
        
        status = "✅" if success else "❌"
        print(f"  {sender} on channel {channel_idx}: Replied on {reply_idx} {status}")
    
    return all(results)


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "Multi-Channel Reply Validation" + " "*23 + "║")
    print("╚" + "="*68 + "╝")
    print("\nValidating: Weather bot correctly replies on all channel_idx values")
    print("Issue: 'It's still only replying to LoRa TX channel msg (idx=0)'")
    
    try:
        # Run all tests
        test1 = test_channel_msg_format()
        test2 = test_channel_msg_v3_format()
        test3 = test_mixed_channels()
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        if test1 and test2 and test3:
            print("✅ ALL TESTS PASSED")
            print("\nThe weather bot correctly:")
            print("  • Receives messages on ANY channel_idx (0-7)")
            print("  • Replies on the SAME channel_idx where each message came from")
            print("  • Works with both RESP_CHANNEL_MSG and RESP_CHANNEL_MSG_V3 formats")
            print("\nConclusion:")
            print("  The bot is NOT 'only replying to LoRa TX channel msg (idx=0)'")
            print("  It correctly handles ALL channel indices (0-7)")
            print("\nIf users are experiencing issues, possible causes:")
            print("  1. Radio hardware configuration issues")
            print("  2. Firewall blocking API requests")
            print("  3. Serial port permission issues")
            print("  4. Outdated bot version (update to latest)")
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            print(f"  RESP_CHANNEL_MSG: {'PASS' if test1 else 'FAIL'}")
            print(f"  RESP_CHANNEL_MSG_V3: {'PASS' if test2 else 'FAIL'}")
            print(f"  Mixed channels: {'PASS' if test3 else 'FAIL'}")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
