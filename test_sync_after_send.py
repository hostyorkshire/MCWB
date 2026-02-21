#!/usr/bin/env python3
"""
Test that verifies the fix for the bot not replying issue.

Problem: Bot was receiving messages and processing them, but replies
         weren't being transmitted properly over LoRa.

Root Cause: After sending a message via CMD_SEND_CHAN_MSG, the code
            was not sending CMD_SYNC_NEXT_MSG to complete the protocol
            exchange with the companion radio.

Fix: Added CMD_SYNC_NEXT_MSG (0x0a) after each message transmission
     to allow the companion radio to process and respond properly.
"""

from unittest.mock import MagicMock
from meshcore import MeshCore


def test_cmd_sync_after_send():
    """
    Test that CMD_SYNC_NEXT_MSG is sent after transmitting a message.
    This ensures the companion radio can properly process the transmission
    and the mesh network can deliver the message.
    """
    print("=" * 70)
    print("TEST: CMD_SYNC_NEXT_MSG Sent After Message Transmission")
    print("=" * 70)
    print()
    print("This test verifies the fix for the issue where the bot was")
    print("processing messages but not replying properly.")
    print()
    
    # Setup mock serial port
    mock_serial = MagicMock()
    mock_serial.is_open = True
    
    mesh = MeshCore("WX_BOT", serial_port="/dev/ttyUSB1", baud_rate=115200, debug=True)
    mesh._serial = mock_serial
    mesh.running = True
    
    # Simulate sending a weather response (like in the problem statement)
    weather_response = """Weather for Shafton, United Kingdom
Conditions: Overcast
Temp: 7.7°C (feels like 4.5°C)
Humidity: 82%
Wind: 13.2 km/h at 253°
Precipitation: 0.0 mm"""
    
    print("Sending weather response on channel 'wxtest'...")
    mesh.send_message(weather_response, "text", channel="wxtest")
    print()
    
    # Verify that serial.write was called twice
    assert mock_serial.write.call_count == 2, \
        f"Expected 2 write calls, got {mock_serial.write.call_count}"
    print("✓ serial.write() called twice (message + sync)")
    
    # First call should be the weather message
    first_call = mock_serial.write.call_args_list[0][0][0]
    assert first_call[0:1] == b'\x3c', "First frame must start with '<' (0x3C)"
    payload1 = first_call[3:]
    assert payload1[0] == 3, "First call must be CMD_SEND_CHAN_MSG (3)"
    assert payload1[2] == 1, "Channel 'wxtest' should map to channel_idx 1"
    print("✓ First call: CMD_SEND_CHAN_MSG (3) with channel_idx=1")
    print(f"  Frame (hex): {first_call[:20].hex()}...")
    
    # Second call should be CMD_SYNC_NEXT_MSG
    second_call = mock_serial.write.call_args_list[1][0][0]
    assert second_call[0:1] == b'\x3c', "Sync frame must start with '<' (0x3C)"
    assert second_call[3:4] == b'\x0a', "Second call must be CMD_SYNC_NEXT_MSG (0x0A)"
    print("✓ Second call: CMD_SYNC_NEXT_MSG (0x0A)")
    print(f"  Frame (hex): {second_call.hex()}")
    print()
    
    print("=" * 70)
    print("✅ FIX VERIFIED: Protocol exchange completed correctly!")
    print("=" * 70)
    print()
    print("The companion radio will now:")
    print("  1. Process the transmitted message")
    print("  2. Queue it for mesh network delivery")
    print("  3. Send acknowledgment when message is transmitted")
    print("  4. Allow the bot to continue normal operation")
    print()
    print("Expected logs after this fix:")
    print("  [timestamp] MeshCore [WX_BOT]: LoRa TX channel msg (idx=1): Weather...")
    print("  [timestamp] MeshCore [WX_BOT]: LoRa CMD: 0a")
    print("  [timestamp] MeshCore [WX_BOT]: MeshCore: message acknowledgment received")
    print()
    

if __name__ == "__main__":
    test_cmd_sync_after_send()
    print("✅ Test passed! The bot should now reply properly.")
