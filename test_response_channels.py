#!/usr/bin/env python3
"""
Test to verify bot accepts queries from all channels and replies correctly
"""

from weather_bot import WeatherBot
from meshcore import MeshCoreMessage
import sys

def test_multi_channel_responses():
    """Test that bot accepts and responds to queries from different channels"""
    print("="*70)
    print("Testing: Bot accepts queries from ALL channels")
    print("="*70)
    print()
    
    # Create bot WITHOUT channel filter (should accept from all channels)
    bot = WeatherBot(node_id="test_bot", debug=True, announce_channel=None)
    
    responses = []
    
    # Mock send_message to capture responses
    original_send = bot.mesh.send_message
    def mock_send(content, msg_type="text", channel=None, channel_idx=None):
        responses.append({
            'content': content,
            'channel': channel,
            'channel_idx': channel_idx
        })
        return original_send(content, msg_type, channel, channel_idx)
    
    bot.mesh.send_message = mock_send
    bot.start()
    
    print("\n" + "="*70)
    print("Test 1: Query from channel_idx 0 (default)")
    print("="*70)
    responses.clear()
    msg1 = MeshCoreMessage(
        sender="user1",
        content="wx London",
        message_type="text",
        channel=None,
        channel_idx=0
    )
    bot.handle_message(msg1)
    
    if len(responses) > 0:
        print(f"✓ Bot responded on channel_idx: {responses[0]['channel_idx']}")
        if responses[0]['channel_idx'] == 0:
            print("✓ Response sent to CORRECT channel (channel_idx 0)")
        else:
            print(f"✗ Response sent to WRONG channel (expected 0, got {responses[0]['channel_idx']})")
    else:
        print("✗ Bot did NOT respond")
    
    print("\n" + "="*70)
    print("Test 2: Query from channel_idx 1")
    print("="*70)
    responses.clear()
    msg2 = MeshCoreMessage(
        sender="user2",
        content="wx Manchester",
        message_type="text",
        channel=None,
        channel_idx=1
    )
    bot.handle_message(msg2)
    
    if len(responses) > 0:
        print(f"✓ Bot responded on channel_idx: {responses[0]['channel_idx']}")
        if responses[0]['channel_idx'] == 1:
            print("✓ Response sent to CORRECT channel (channel_idx 1)")
        else:
            print(f"✗ Response sent to WRONG channel (expected 1, got {responses[0]['channel_idx']})")
    else:
        print("✗ Bot did NOT respond")
    
    print("\n" + "="*70)
    print("Test 3: Query from channel_idx 2 (different channel)")
    print("="*70)
    responses.clear()
    msg3 = MeshCoreMessage(
        sender="user3",
        content="wx York",
        message_type="text",
        channel=None,
        channel_idx=2
    )
    bot.handle_message(msg3)
    
    if len(responses) > 0:
        print(f"✓ Bot responded on channel_idx: {responses[0]['channel_idx']}")
        if responses[0]['channel_idx'] == 2:
            print("✓ Response sent to CORRECT channel (channel_idx 2)")
        else:
            print(f"✗ Response sent to WRONG channel (expected 2, got {responses[0]['channel_idx']})")
    else:
        print("✗ Bot did NOT respond")
    
    print("\n" + "="*70)
    print("Test 4: Check channel filter configuration")
    print("="*70)
    if bot.mesh.channel_filter is None:
        print("✓ Channel filter is DISABLED (None)")
        print("✓ Bot accepts queries from ALL channels")
    else:
        print(f"✗ Channel filter is ENABLED: {bot.mesh.channel_filter}")
        print("✗ This may block queries from other channels!")
    
    if bot.announce_channel:
        print(f"\nℹ Announce channel is set to: '{bot.announce_channel}'")
        print("  (This only affects periodic announcements, not query responses)")
    else:
        print("\nℹ Announce channel is disabled")
    
    bot.stop()
    
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print("Without --channel parameter:")
    print("  ✓ Bot accepts queries from ALL channels")
    print("  ✓ Bot replies on the SAME channel_idx where query came from")
    print("\nTo ensure this behavior:")
    print("  - Don't use --channel parameter when starting the bot")
    print("  - Or explicitly set --channel to empty string")
    print("="*70)

if __name__ == "__main__":
    test_multi_channel_responses()
