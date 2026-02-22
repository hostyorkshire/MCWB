#!/usr/bin/env python3
"""
MeshCore Send - Utility for sending messages via MeshCore network
This is a simple command-line utility for sending messages through the MeshCore network.
"""

import sys
import argparse
from typing import Optional
from meshcore import MeshCore


def send_message(node_id: str, content: str, message_type: str = "text",
                 channel: Optional[str] = None, channel_idx: Optional[int] = None,
                 debug: bool = False,
                 serial_port: Optional[str] = None, baud_rate: int = 9600):
    """
    Send a message via MeshCore network

    Args:
        node_id: Unique identifier for this node
        content: Message content to send
        message_type: Type of message (default: "text")
        channel: Optional channel name to broadcast to (e.g. "weather").
        channel_idx: Optional raw channel slot index (0-7) to use directly.
                     This is the MESHCORE_CHANNEL_IDX value – the numeric slot
                     configured on the companion radio.  When provided, it takes
                     precedence over the channel name.  Use this when you know
                     exactly which physical channel slot you want to send on
                     (e.g. ``--channel-idx 1`` for channel slot 1).
        debug: Enable debug output
        serial_port: Serial port for LoRa module (e.g., /dev/ttyUSB0).
                     When None, runs in simulation mode.
        baud_rate: Baud rate for LoRa serial connection (default: 9600)

    Returns:
        MeshCoreMessage object representing the sent message
    """
    mesh = MeshCore(node_id, debug=debug, serial_port=serial_port, baud_rate=baud_rate)
    mesh.start()

    message = mesh.send_message(content, message_type, channel, channel_idx)

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
        "-c", "--channel",
        help="Channel name to broadcast to (e.g. 'weather'). "
             "The name is mapped to a channel slot index internally."
    )

    parser.add_argument(
        "-x", "--channel-idx",
        type=int,
        metavar="IDX",
        help="Channel slot index (0-7) to send on directly "
             "(MESHCORE_CHANNEL_IDX). "
             "Use this when you know the exact numeric slot configured on "
             "your companion radio (e.g. 1 for the first named channel). "
             "Takes precedence over --channel when both are given."
    )

    parser.add_argument(
        "-p", "--port",
        help="Serial port for LoRa module (e.g., /dev/ttyUSB0). "
             "When omitted, the message is sent in simulation mode."
    )

    parser.add_argument(
        "-b", "--baud",
        type=int,
        default=9600,
        help="Baud rate for LoRa serial connection (default: 9600)"
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
        channel=args.channel,
        channel_idx=args.channel_idx,
        debug=args.debug,
        serial_port=args.port,
        baud_rate=args.baud
    )

    if not args.debug:
        channel_info = f" on channel '{args.channel}'" if args.channel else ""
        if args.channel_idx is not None:
            channel_info += f" (channel_idx={args.channel_idx})"
        print(f"Message sent{channel_info}: {message.content}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
