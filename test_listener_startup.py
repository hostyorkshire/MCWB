#!/usr/bin/env python3
"""
Test to verify that the listener thread properly receives messages after startup.
This test specifically addresses the issue where CMD_SYNC_NEXT_MSG was being sent
before the listener thread started, causing messages to be missed.
"""

import time
import threading
from io import BytesIO
from meshcore import MeshCore

# Frame constants
_FRAME_OUT = 0x3E
_RESP_NO_MORE_MSGS = 10
_RESP_CHANNEL_MSG_V3 = 17


class MockSerial:
    """Mock serial port that simulates real LoRa companion radio behavior"""
    
    def __init__(self):
        self.write_buffer = []
        self.read_buffer = BytesIO()
        self.is_open = True
        self.rts = None
        self.dtr = None
        self.in_waiting = 0
        self._lock = threading.Lock()
        
        # When CMD_SYNC_NEXT_MSG is received, we'll respond
        self.auto_respond_to_sync = True
        
    def write(self, data):
        """Record writes and optionally auto-respond"""
        with self._lock:
            self.write_buffer.append(data)
            
            # If this is a CMD_SYNC_NEXT_MSG (0x0a), respond with RESP_NO_MORE_MSGS
            if self.auto_respond_to_sync and len(data) >= 4:
                # Check if this is CMD_SYNC_NEXT_MSG frame: 3c 01 00 0a
                if data[0] == 0x3C and data[3] == 0x0A:
                    # Respond with RESP_NO_MORE_MSGS
                    response = bytes([_FRAME_OUT, 1, 0, _RESP_NO_MORE_MSGS])
                    self.read_buffer = BytesIO(response)
                    self.in_waiting = len(response)
    
    def read(self, size=1):
        """Read from the buffer"""
        with self._lock:
            data = self.read_buffer.read(size)
            self.in_waiting = max(0, self.in_waiting - len(data))
            return data
    
    def readline(self):
        """Read a line from the buffer"""
        with self._lock:
            line = self.read_buffer.readline()
            self.in_waiting = max(0, self.in_waiting - len(line))
            return line
    
    def close(self):
        """Close the mock serial port"""
        self.is_open = False
    
    def get_write_count(self):
        """Get number of writes performed"""
        with self._lock:
            return len(self.write_buffer)


def test_listener_receives_initial_sync_response():
    """
    Test that the listener thread receives the response to the initial CMD_SYNC_NEXT_MSG.
    
    This test verifies the fix for the issue where CMD_SYNC_NEXT_MSG was sent before
    the listener thread started, causing responses to be lost.
    """
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Test: Listener Receives Initial Sync Response".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Create a MeshCore instance with mock serial
    mesh = MeshCore("test_bot", debug=True)
    mock_serial = MockSerial()
    mesh._serial = mock_serial
    mesh.serial_port = "/dev/ttyUSB0"
    
    # Track received frames
    frames_received = []
    original_parse = mesh._parse_binary_frame
    
    def tracking_parse(payload):
        frames_received.append(payload[0])  # Track the frame code
        return original_parse(payload)
    
    mesh._parse_binary_frame = tracking_parse
    
    print("Step 1: Starting MeshCore (which starts listener thread)...")
    mesh.running = True
    
    # Manually call _start_listener to simulate what start() does
    mesh._start_listener()
    
    # Give the listener thread time to start and process
    time.sleep(0.5)
    
    print(f"Step 2: Checking that CMD_SYNC_NEXT_MSG was sent...")
    writes = mock_serial.get_write_count()
    print(f"   Total writes: {writes}")
    
    # The listener should have sent CMD_SYNC_NEXT_MSG
    assert writes >= 1, "CMD_SYNC_NEXT_MSG should have been sent"
    print("   ✓ CMD_SYNC_NEXT_MSG was sent")
    
    print(f"Step 3: Checking that listener received the response...")
    print(f"   Frames received: {len(frames_received)}")
    print(f"   Frame codes: {[f'0x{code:02x}' for code in frames_received]}")
    
    # The listener should have received RESP_NO_MORE_MSGS (0x0A)
    assert _RESP_NO_MORE_MSGS in frames_received, \
        f"RESP_NO_MORE_MSGS (0x{_RESP_NO_MORE_MSGS:02x}) should have been received"
    print(f"   ✓ RESP_NO_MORE_MSGS (0x{_RESP_NO_MORE_MSGS:02x}) was received")
    
    print()
    print("Step 4: Stopping MeshCore...")
    mesh.stop()
    
    print()
    print("=" * 60)
    print("✅ TEST PASSED: Listener properly receives initial sync response")
    print("=" * 60)
    print()
    print("This confirms that moving CMD_SYNC_NEXT_MSG to _start_listener()")
    print("fixed the race condition where responses were lost.")
    print()


def test_listener_receives_channel_message():
    """
    Test that the listener thread receives and processes channel messages.
    
    This simulates the real-world scenario from the problem statement where
    the bot should receive and process incoming weather queries.
    """
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Test: Listener Receives Channel Messages".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Create a MeshCore instance with mock serial
    mesh = MeshCore("WX_BOT", debug=True)
    mock_serial = MockSerial()
    
    # Prepare a channel message using the old format (code 8)
    # Format: code(1) + channel_idx(1) + path_len(1) + txt_type(1) + timestamp(4) + text
    message_text = b"User: wx London"
    payload = bytes([
        8,      # RESP_CHANNEL_MSG (old format)
        0,      # channel_idx = 0 (default channel)
        1,      # path_len
        0,      # txt_type
        0, 0, 0, 0,  # timestamp (placeholder)
    ]) + message_text
    
    # Create the complete frame
    frame = bytes([_FRAME_OUT]) + len(payload).to_bytes(2, "little") + payload
    
    # Set up mock serial to provide this frame
    mock_serial.read_buffer = BytesIO(frame)
    mock_serial.in_waiting = len(frame)
    mock_serial.auto_respond_to_sync = False  # Don't auto-respond for this test
    
    mesh._serial = mock_serial
    mesh.serial_port = "/dev/ttyUSB0"
    
    # Track received messages
    messages_received = []
    
    def message_handler(message):
        messages_received.append(message)
        print(f"   📨 Received message from '{message.sender}': {message.content}")
    
    mesh.register_handler("text", message_handler)
    
    print("Step 1: Starting MeshCore with listener thread...")
    mesh.running = True
    mesh._start_listener()
    
    # Give the listener thread time to read and process the frame
    time.sleep(0.5)
    
    print(f"Step 2: Checking that message was received and processed...")
    print(f"   Messages received: {len(messages_received)}")
    
    assert len(messages_received) >= 1, "At least one message should have been received"
    
    msg = messages_received[0]
    # The sender should be "User" and content should be "wx London"
    # Note: _dispatch_channel_message parses "sender: content" format
    assert "wx London" in msg.content, f"Expected content to contain 'wx London', got '{msg.content}'"
    assert msg.channel_idx == 0, f"Expected channel_idx 0, got {msg.channel_idx}"
    
    print(f"   ✓ Message properly parsed:")
    print(f"     - Sender: {msg.sender}")
    print(f"     - Content: {msg.content}")
    print(f"     - Channel idx: {msg.channel_idx}")
    
    print()
    print("Step 3: Stopping MeshCore...")
    mesh.stop()
    
    print()
    print("=" * 60)
    print("✅ TEST PASSED: Listener properly receives channel messages")
    print("=" * 60)
    print()


if __name__ == "__main__":
    print()
    print("Testing listener thread startup behavior...")
    print()
    
    try:
        test_listener_receives_initial_sync_response()
        print()
        test_listener_receives_channel_message()
        
        print()
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 58 + "║")
        print("║" + "  ✅ ALL TESTS PASSED".center(58) + "║")
        print("║" + " " * 58 + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        print("The fix successfully resolves the 'bot is not listening' issue.")
        print()
        print("What was fixed:")
        print("  • CMD_SYNC_NEXT_MSG is now sent AFTER the listener thread starts")
        print("  • This ensures responses from the companion radio are received")
        print("  • The bot can now properly process incoming messages")
        print()
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        exit(1)
