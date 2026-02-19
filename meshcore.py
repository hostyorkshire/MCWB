#!/usr/bin/env python3
"""
MeshCore - Core library for mesh radio network communication
This module provides the core functionality for communicating via MeshCore mesh radio network.
"""

import json
import time
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime

try:
    import serial
    from serial import SerialException
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    # Provide a fallback so SerialException can be caught safely without pyserial installed
    class SerialException(Exception):  # type: ignore[no-redef]
        pass


class MeshCoreMessage:
    """Represents a message in the MeshCore network"""
    
    def __init__(self, sender: str, content: str, message_type: str = "text", 
                 timestamp: Optional[float] = None, channel: Optional[str] = None):
        self.sender = sender
        self.content = content
        self.message_type = message_type
        self.timestamp = timestamp or time.time()
        self.channel = channel
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        data = {
            "sender": self.sender,
            "content": self.content,
            "type": self.message_type,
            "timestamp": self.timestamp
        }
        if self.channel:
            data["channel"] = self.channel
        return data
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeshCoreMessage':
        """Create message from dictionary"""
        return cls(
            sender=data.get("sender", "unknown"),
            content=data.get("content", ""),
            message_type=data.get("type", "text"),
            timestamp=data.get("timestamp"),
            channel=data.get("channel")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MeshCoreMessage':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class MeshCore:
    """Main MeshCore communication handler"""
    
    def __init__(self, node_id: str, debug: bool = False,
                 serial_port: Optional[str] = None, baud_rate: int = 9600):
        """
        Initialize MeshCore
        
        Args:
            node_id: Unique identifier for this node
            debug: Enable debug output
            serial_port: Serial port for LoRa module (e.g., /dev/ttyUSB0). When None,
                         the node operates in simulation mode (no actual radio transmission).
            baud_rate: Baud rate for LoRa serial connection (default: 9600)
        """
        self.node_id = node_id
        self.debug = debug
        self.message_handlers = {}
        self.running = False
        self.channel_filter = None  # None means listen to all channels

        # LoRa serial connection
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self._serial = None
        self._listener_thread = None
        
    def log(self, message: str):
        """Log debug messages"""
        if self.debug:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] MeshCore [{self.node_id}]: {message}")
    
    def set_channel_filter(self, channel: Optional[str]):
        """
        Set channel filter for receiving messages
        
        Args:
            channel: Channel name to filter on, or None to receive all channels
        """
        self.channel_filter = channel
        self.log(f"Channel filter set to: {channel if channel else 'all channels'}")
    
    def register_handler(self, message_type: str, handler: Callable):
        """
        Register a handler for a specific message type
        
        Args:
            message_type: Type of message to handle
            handler: Callback function to handle the message
        """
        self.message_handlers[message_type] = handler
        self.log(f"Registered handler for message type: {message_type}")
    
    def send_message(self, content: str, message_type: str = "text", channel: Optional[str] = None) -> MeshCoreMessage:
        """
        Send a message via MeshCore network
        
        Args:
            content: Message content
            message_type: Type of message
            channel: Optional channel to broadcast to
            
        Returns:
            MeshCoreMessage object
        """
        message = MeshCoreMessage(
            sender=self.node_id,
            content=content,
            message_type=message_type,
            channel=channel
        )
        
        channel_info = f" on channel '{channel}'" if channel else ""
        self.log(f"Sending message{channel_info}: {message.to_json()}")
        
        if self._serial and self._serial.is_open:
            # Transmit over LoRa via serial port
            try:
                data = (message.to_json() + "\n").encode("utf-8")
                self._serial.write(data)
                self.log(f"LoRa TX: {message.to_json()}")
            except SerialException as e:
                self.log(f"LoRa TX error: {e}")
        else:
            # Simulation mode - no radio hardware attached
            self.log("Simulation mode: message not transmitted over radio")
        
        return message
    
    def receive_message(self, message: MeshCoreMessage):
        """
        Receive and process a message
        
        Args:
            message: MeshCoreMessage object to process
        """
        # Apply channel filter if set
        if self.channel_filter and message.channel != self.channel_filter:
            self.log(f"Ignoring message from channel '{message.channel}' (filter: '{self.channel_filter}')")
            return
        
        channel_info = f" on channel '{message.channel}'" if message.channel else ""
        self.log(f"Received message from {message.sender}{channel_info}: {message.content}")
        
        # Check if we have a handler for this message type
        if message.message_type in self.message_handlers:
            handler = self.message_handlers[message.message_type]
            handler(message)
        else:
            self.log(f"No handler for message type: {message.message_type}")
    
    def _connect_serial(self):
        """Open the serial port for the LoRa module"""
        if not SERIAL_AVAILABLE:
            self.log("pyserial is not installed. Install with: pip install pyserial")
            return
        try:
            self._serial = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            self.log(f"LoRa connected on {self.serial_port} at {self.baud_rate} baud")
        except SerialException as e:
            self.log(f"Failed to open serial port {self.serial_port}: {e}")
            self._serial = None

    def _start_listener(self):
        """Start background thread to listen for incoming LoRa messages"""
        self._listener_thread = threading.Thread(
            target=self._listen_loop, daemon=True, name="lora-listener"
        )
        self._listener_thread.start()
        self.log("LoRa listener thread started")

    def _listen_loop(self):
        """
        Background loop: read lines from the LoRa serial port, parse them as
        JSON-encoded MeshCoreMessage objects and dispatch to registered handlers.
        """
        while self.running and self._serial and self._serial.is_open:
            try:
                raw = self._serial.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                self.log(f"LoRa RX: {line}")
                try:
                    message = MeshCoreMessage.from_json(line)
                    self.receive_message(message)
                except (json.JSONDecodeError, KeyError) as e:
                    self.log(f"Could not parse LoRa message: {e} | raw: {line}")
            except SerialException as e:
                self.log(f"LoRa serial read error: {e}")
                break

    def start(self):
        """Start the MeshCore listener"""
        self.running = True
        if self.serial_port:
            self._connect_serial()
            if self._serial and self._serial.is_open:
                self._start_listener()
        self.log("MeshCore started")
    
    def stop(self):
        """Stop the MeshCore listener"""
        self.running = False
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=2)
        if self._serial and self._serial.is_open:
            self._serial.close()
            self.log(f"LoRa serial port {self.serial_port} closed")
        self.log("MeshCore stopped")
    
    def is_running(self) -> bool:
        """Check if MeshCore is running"""
        return self.running


if __name__ == "__main__":
    # Example usage
    mesh = MeshCore("node_001", debug=True)
    
    def text_handler(message: MeshCoreMessage):
        channel_info = f" on channel '{message.channel}'" if message.channel else ""
        print(f"Text message from {message.sender}{channel_info}: {message.content}")
    
    mesh.register_handler("text", text_handler)
    mesh.start()
    
    # Send a test message without channel
    msg1 = mesh.send_message("Hello, MeshCore!", "text")
    
    # Send a test message with channel
    msg2 = mesh.send_message("Weather broadcast", "text", channel="weather")
    
    # Simulate receiving the messages
    mesh.receive_message(msg1)
    mesh.receive_message(msg2)
    
    # Test channel filtering
    print("\nSetting channel filter to 'weather'...")
    mesh.set_channel_filter("weather")
    
    mesh.receive_message(msg1)  # Should be ignored
    mesh.receive_message(msg2)  # Should be processed
    
    mesh.stop()
