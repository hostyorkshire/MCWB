#!/usr/bin/env python3
"""
Comprehensive test demonstrating the fix for the weather and wxtest channel issue.

Problem: Incoming LoRa messages had channel_idx but it wasn't being extracted and mapped
back to the Python channel name, causing received messages to have channel=None.

Solution: Extract channel_idx from binary frames and reverse-map it to Python channel name.
"""

import sys
from meshcore import MeshCore, _RESP_CHANNEL_MSG, _RESP_CHANNEL_MSG_V3, _FRAME_OUT
from unittest.mock import MagicMock

def test_weather_and_wxtest_channels():
    """
    Test that the weather bot can correctly receive and respond to messages
    on both weather and wxtest channels.
    """
    print("=" * 70)
    print("  Testing Weather and Wxtest Channel Reception (Issue Fix)")
    print("=" * 70)
    
    received_messages = []
    
    def handler(message):
        received_messages.append(message)
        print(f"\n  Handler received message:")
        print(f"    Sender: {message.sender}")
        print(f"    Content: {message.content}")
        print(f"    Channel: {message.channel}")
    
    # Create mesh node (simulating the weather bot)
    mesh = MeshCore("WX_BOT", debug=False)
    mesh.register_handler("text", handler)
    mesh.running = True
    
    # Setup channel mappings as the weather bot would
    # When bot is started with --channel weather,wxtest
    mesh._get_channel_idx("weather")  # Maps to channel_idx=1
    mesh._get_channel_idx("wxtest")   # Maps to channel_idx=2
    
    print(f"\nBot configured for channels: {list(mesh._channel_map.keys())}")
    print(f"Channel mappings: {mesh._channel_map}")
    
    # Mock serial port
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    print("\n" + "-" * 70)
    print("Test 1: Receive message on 'weather' channel (channel_idx=1)")
    print("-" * 70)
    
    # Simulate receiving a message on weather channel (channel_idx=1)
    channel_idx = 1
    path_len = 0
    txt_type = 0
    timestamp = (0).to_bytes(4, "little")
    text = "User1: wx London".encode("utf-8")
    
    payload = bytes([_RESP_CHANNEL_MSG, channel_idx, path_len, txt_type]) + timestamp + text
    frame_length = len(payload).to_bytes(2, "little")
    raw_frame = bytes([_FRAME_OUT]) + frame_length + payload + b'\n'
    
    length = int.from_bytes(raw_frame[1:3], 'little'); payload = raw_frame[3:3+length]; mesh._parse_binary_frame(payload)
    
    assert len(received_messages) == 1, "Should have received 1 message"
    assert received_messages[0].channel == "weather", f"Expected channel='weather', got '{received_messages[0].channel}'"
    assert received_messages[0].content == "wx London"
    print("  ✓ Message correctly received on 'weather' channel")
    
    print("\n" + "-" * 70)
    print("Test 2: Receive message on 'wxtest' channel (channel_idx=2)")
    print("-" * 70)
    
    # Simulate receiving a message on wxtest channel (channel_idx=2)
    received_messages.clear()
    channel_idx = 2
    text = "User2: wx Manchester".encode("utf-8")
    
    payload = bytes([_RESP_CHANNEL_MSG, channel_idx, path_len, txt_type]) + timestamp + text
    frame_length = len(payload).to_bytes(2, "little")
    raw_frame = bytes([_FRAME_OUT]) + frame_length + payload + b'\n'
    
    length = int.from_bytes(raw_frame[1:3], 'little'); payload = raw_frame[3:3+length]; mesh._parse_binary_frame(payload)
    
    assert len(received_messages) == 1, "Should have received 1 message"
    assert received_messages[0].channel == "wxtest", f"Expected channel='wxtest', got '{received_messages[0].channel}'"
    assert received_messages[0].content == "wx Manchester"
    print("  ✓ Message correctly received on 'wxtest' channel")
    
    print("\n" + "-" * 70)
    print("Test 3: Receive V3 message on 'weather' channel")
    print("-" * 70)
    
    # Simulate receiving a V3 message (with SNR) on weather channel
    received_messages.clear()
    snr = 50  # SNR value
    reserved = bytes([0, 0])
    channel_idx = 1  # weather channel
    text = "User3: weather York".encode("utf-8")
    
    # V3 format: SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    payload = bytes([_RESP_CHANNEL_MSG_V3, snr]) + reserved + bytes([channel_idx, path_len, txt_type]) + timestamp + text
    frame_length = len(payload).to_bytes(2, "little")
    raw_frame = bytes([_FRAME_OUT]) + frame_length + payload + b'\n'
    
    length = int.from_bytes(raw_frame[1:3], 'little'); payload = raw_frame[3:3+length]; mesh._parse_binary_frame(payload)
    
    assert len(received_messages) == 1, "Should have received 1 message"
    assert received_messages[0].channel == "weather", f"Expected channel='weather', got '{received_messages[0].channel}'"
    assert received_messages[0].content == "weather York"
    print("  ✓ V3 message correctly received on 'weather' channel")
    
    print("\n" + "-" * 70)
    print("Test 4: Receive message on default channel (channel_idx=0)")
    print("-" * 70)
    
    # Simulate receiving a message on default/broadcast channel (channel_idx=0)
    received_messages.clear()
    channel_idx = 0  # default channel
    text = "User4: wx Bristol".encode("utf-8")
    
    payload = bytes([_RESP_CHANNEL_MSG, channel_idx, path_len, txt_type]) + timestamp + text
    frame_length = len(payload).to_bytes(2, "little")
    raw_frame = bytes([_FRAME_OUT]) + frame_length + payload + b'\n'
    
    length = int.from_bytes(raw_frame[1:3], 'little'); payload = raw_frame[3:3+length]; mesh._parse_binary_frame(payload)
    
    assert len(received_messages) == 1, "Should have received 1 message"
    assert received_messages[0].channel is None, f"Expected channel=None for default channel, got '{received_messages[0].channel}'"
    assert received_messages[0].content == "wx Bristol"
    print("  ✓ Message correctly received on default channel (no channel name)")
    
    print("\n" + "=" * 70)
    print("  ✅ All tests passed! Weather and wxtest channels working correctly.")
    print("=" * 70)
    
    print("\nSummary of the fix:")
    print("  • channel_idx is now extracted from incoming LoRa binary frames")
    print("  • channel_idx is reverse-mapped to Python channel names")
    print("  • Received messages now have correct channel attribute")
    print("  • Weather bot can now properly receive on 'weather' and 'wxtest' channels")
    print()
    
    mesh.running = False

if __name__ == "__main__":
    try:
        test_weather_and_wxtest_channels()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
