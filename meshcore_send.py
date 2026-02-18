#!/usr/bin/env python3
"""
MeshCore Send - Utility for sending messages via MeshCore network
This is a simple command-line utility for sending messages through the MeshCore network.
"""

import sys
import argparse
from meshcore import MeshCore, MeshCoreMessage


def send_message(node_id: str, content: str, message_type: str = "text", debug: bool = False):
    """
    Send a message via MeshCore network
    
    Args:
        node_id: Unique identifier for this node
        content: Message content to send
        message_type: Type of message (default: "text")
        debug: Enable debug output
        
    Returns:
        MeshCoreMessage object representing the sent message
    """
    mesh = MeshCore(node_id, debug=debug)
    mesh.start()
    
    message = mesh.send_message(content, message_type)
    
    mesh.stop()
    
    return message


def main():
    """Main entry point for meshcore_send utility"""
    parser = argparse.ArgumentParser(
        description="Send messages via MeshCore mesh radio network"
    )
    
    parser.add_argument(
        "content",
        help="Message content to send"
    )
    
    parser.add_argument(
        "-n", "--node-id",
        default="sender_node",
        help="Node ID for this sender (default: sender_node)"
    )
    
    parser.add_argument(
        "-t", "--type",
        default="text",
        help="Message type (default: text)"
    )
    
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    args = parser.parse_args()
    
    # Send the message
    message = send_message(
        node_id=args.node_id,
        content=args.content,
        message_type=args.type,
        debug=args.debug
    )
    
    if not args.debug:
        print(f"Message sent: {message.content}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
