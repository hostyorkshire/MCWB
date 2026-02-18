#!/usr/bin/env python3
"""
MeshCore - Core library for mesh radio network communication
This module provides the core functionality for communicating via MeshCore mesh radio network.
"""

import json
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime


class MeshCoreMessage:
    """Represents a message in the MeshCore network"""
    
    def __init__(self, sender: str, content: str, message_type: str = "text", 
                 timestamp: Optional[float] = None):
        self.sender = sender
        self.content = content
        self.message_type = message_type
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "sender": self.sender,
            "content": self.content,
            "type": self.message_type,
            "timestamp": self.timestamp
        }
    
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
            timestamp=data.get("timestamp")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MeshCoreMessage':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class MeshCore:
    """Main MeshCore communication handler"""
    
    def __init__(self, node_id: str, debug: bool = False):
        """
        Initialize MeshCore
        
        Args:
            node_id: Unique identifier for this node
            debug: Enable debug output
        """
        self.node_id = node_id
        self.debug = debug
        self.message_handlers = {}
        self.running = False
        
    def log(self, message: str):
        """Log debug messages"""
        if self.debug:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] MeshCore [{self.node_id}]: {message}")
    
    def register_handler(self, message_type: str, handler: Callable):
        """
        Register a handler for a specific message type
        
        Args:
            message_type: Type of message to handle
            handler: Callback function to handle the message
        """
        self.message_handlers[message_type] = handler
        self.log(f"Registered handler for message type: {message_type}")
    
    def send_message(self, content: str, message_type: str = "text") -> MeshCoreMessage:
        """
        Send a message via MeshCore network
        
        Args:
            content: Message content
            message_type: Type of message
            
        Returns:
            MeshCoreMessage object
        """
        message = MeshCoreMessage(
            sender=self.node_id,
            content=content,
            message_type=message_type
        )
        
        self.log(f"Sending message: {message.to_json()}")
        
        # In a real implementation, this would transmit via radio
        # For now, we'll simulate by returning the message
        return message
    
    def receive_message(self, message: MeshCoreMessage):
        """
        Receive and process a message
        
        Args:
            message: MeshCoreMessage object to process
        """
        self.log(f"Received message from {message.sender}: {message.content}")
        
        # Check if we have a handler for this message type
        if message.message_type in self.message_handlers:
            handler = self.message_handlers[message.message_type]
            handler(message)
        else:
            self.log(f"No handler for message type: {message.message_type}")
    
    def start(self):
        """Start the MeshCore listener"""
        self.running = True
        self.log("MeshCore started")
    
    def stop(self):
        """Stop the MeshCore listener"""
        self.running = False
        self.log("MeshCore stopped")
    
    def is_running(self) -> bool:
        """Check if MeshCore is running"""
        return self.running


if __name__ == "__main__":
    # Example usage
    mesh = MeshCore("node_001", debug=True)
    
    def text_handler(message: MeshCoreMessage):
        print(f"Text message from {message.sender}: {message.content}")
    
    mesh.register_handler("text", text_handler)
    mesh.start()
    
    # Send a test message
    msg = mesh.send_message("Hello, MeshCore!", "text")
    
    # Simulate receiving the message
    mesh.receive_message(msg)
    
    mesh.stop()
