#!/usr/bin/env python3
"""
Test to verify channel_idx is extracted from incoming LoRa messages
"""

import sys
from meshcore import MeshCore
from unittest.mock import MagicMock

def test_channel_idx_extraction():
    """Test that incoming LoRa messages extract channel_idx and map back to channel name"""
    print("=" * 60)
    print("Testing channel_idx extraction from LoRa frames")
    print("=" * 60)
    
    received_messages = []
    
    def handler(message):
        received_messages.append(message)
        print(f"Received message:")
        print(f"  Sender: {message.sender}")
        print(f"  Content: {message.content}")
        print(f"  Channel: {message.channel}")
    
    # Create mesh node
    mesh = MeshCore("test_node", debug=True)
    mesh.register_handler("text", handler)
    mesh.running = True
    
    # Setup channel mappings
    # When the bot sends to "weather" channel, it gets channel_idx=1
    mesh._get_channel_idx("weather")  # This should map weather -> 1
    mesh._get_channel_idx("wxtest")   # This should map wxtest -> 2
    
    print(f"\nChannel mappings: {mesh._channel_map}")
    print(f"Expected: {{'weather': 1, 'wxtest': 2}}")
    
    # Mock serial port
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mesh._serial = mock_serial
    
    # Simulate receiving a channel message (RESP_CHANNEL_MSG format)
    # Format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    # Let's simulate a message on channel_idx=1 (weather channel)
    channel_idx = 1
    path_len = 0
    txt_type = 0
    timestamp = (0).to_bytes(4, "little")
    text = "TestUser: wx London".encode("utf-8")
    
    # Build the frame
    from meshcore import _RESP_CHANNEL_MSG, _FRAME_OUT
    payload = bytes([_RESP_CHANNEL_MSG, channel_idx, path_len, txt_type]) + timestamp + text
    frame_length = len(payload).to_bytes(2, "little")
    raw_frame = bytes([_FRAME_OUT]) + frame_length + payload + b'\n'
    
    print(f"\nSimulating incoming LoRa frame on channel_idx={channel_idx}")
    print(f"Expected Python channel name: 'weather'")
    
    # Process the frame directly
    mesh._handle_binary_frame(raw_frame)
    
    # Check what we received
    print(f"\nReceived {len(received_messages)} message(s)")
    if received_messages:
        msg = received_messages[0]
        print(f"Message channel: {msg.channel}")
        if msg.channel == "weather":
            print("✓ Channel correctly mapped back from channel_idx!")
        elif msg.channel is None:
            print("✗ ERROR: Channel not set on received message!")
            print("  This means channel_idx is not being extracted and mapped back")
        else:
            print(f"✗ ERROR: Unexpected channel: {msg.channel}")
    
    mesh.running = False
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_channel_idx_extraction()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
