#!/usr/bin/env python3
"""
Test script to verify that incoming channel messages are properly received and processed
"""

import sys
from unittest.mock import MagicMock
from meshcore import MeshCore, MeshCoreMessage

def test_message_reception():
    """Test that channel messages trigger the message handler"""
    print("=" * 70)
    print("TEST: Message Reception and Handler Triggering")
    print("=" * 70)
    print()
    
    # Create MeshCore instance
    mesh = MeshCore("TEST_BOT", debug=True)
    mesh.running = True
    
    # Track whether handler was called
    handler_called = [False]
    received_message = [None]
    
    def test_handler(message: MeshCoreMessage):
        """Test message handler"""
        print(f"✅ Handler called with message: {message.content}")
        handler_called[0] = True
        received_message[0] = message
    
    # Register handler
    mesh.register_handler("text", test_handler)
    print("✓ Registered 'text' message handler")
    print()
    
    # Simulate receiving a channel message frame
    # Frame code 0x08 = RESP_CHANNEL_MSG
    # Format: channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    print("Step 1: Simulate receiving RESP_CHANNEL_MSG (0x08) frame")
    print("-" * 70)
    
    # Construct frame payload
    channel_idx = 1  # Channel #1
    path_len = 3
    txt_type = 1
    timestamp = (1771711343).to_bytes(4, "little")
    text = b"testuser: wx London"
    
    payload = bytes([0x08, channel_idx, path_len, txt_type]) + timestamp + text
    print(f"Payload: {payload.hex()}")
    print(f"Expected text: {text.decode('utf-8')}")
    print()
    
    # Parse the frame
    mesh._parse_binary_frame(payload)
    print()
    
    # Check if handler was called
    print("Step 2: Verify handler was triggered")
    print("-" * 70)
    if handler_called[0]:
        print(f"✅ Handler WAS called!")
        print(f"   Sender: {received_message[0].sender}")
        print(f"   Content: {received_message[0].content}")
        print(f"   Channel idx: {received_message[0].channel_idx}")
    else:
        print(f"❌ Handler was NOT called!")
        return False
    
    print()
    
    # Now test V3 format
    print("Step 3: Simulate receiving RESP_CHANNEL_MSG_V3 (0x11) frame")
    print("-" * 70)
    
    handler_called[0] = False
    received_message[0] = None
    
    # V3 format includes SNR prefix
    # Format: SNR(1) + reserved(2) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    snr = 15  # SNR value
    reserved = bytes([0, 0])
    text2 = b"anotheruser: weather Sheffield"
    
    payload_v3 = bytes([0x11, snr]) + reserved + bytes([channel_idx, path_len, txt_type]) + timestamp + text2
    print(f"Payload: {payload_v3.hex()}")
    print(f"Expected text: {text2.decode('utf-8')}")
    print()
    
    mesh._parse_binary_frame(payload_v3)
    print()
    
    if handler_called[0]:
        print(f"✅ Handler WAS called for V3 frame!")
        print(f"   Sender: {received_message[0].sender}")
        print(f"   Content: {received_message[0].content}")
        print(f"   Channel idx: {received_message[0].channel_idx}")
    else:
        print(f"❌ Handler was NOT called for V3 frame!")
        return False
    
    print()
    print("=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    print()
    print("The message reception logic is working correctly.")
    print("If messages aren't being processed in production, the issue is likely:")
    print("  1. Messages aren't arriving from the companion radio")
    print("  2. The companion radio isn't subscribed to the right channels")
    print("  3. The companion radio firmware needs configuration")
    print()
    
    return True

if __name__ == "__main__":
    success = test_message_reception()
    sys.exit(0 if success else 1)
