#!/usr/bin/env python3
"""
Test script to verify that different channel names are mapped to different channel_idx
values for actual LoRa transmission, fixing the issue where messages only appeared
in one channel when multiple channels were specified.
"""

import sys
from meshcore import MeshCore
from weather_bot import WeatherBot


def test_channel_idx_mapping():
    """Test that different channel names get different channel_idx values"""
    print("=" * 60)
    print("TEST: Channel Name to Channel Index Mapping")
    print("=" * 60)
    
    mesh = MeshCore("test_node", debug=False)
    
    # Test default channel (None)
    idx_default = mesh._get_channel_idx(None)
    assert idx_default == 0, f"Expected channel_idx=0 for None, got {idx_default}"
    print(f"✓ Channel None -> channel_idx {idx_default}")
    
    # Test named channels get sequential indices
    idx_weather = mesh._get_channel_idx("weather")
    assert idx_weather == 1, f"Expected channel_idx=1 for 'weather', got {idx_weather}"
    print(f"✓ Channel 'weather' -> channel_idx {idx_weather}")
    
    idx_wxtest = mesh._get_channel_idx("wxtest")
    assert idx_wxtest == 2, f"Expected channel_idx=2 for 'wxtest', got {idx_wxtest}"
    print(f"✓ Channel 'wxtest' -> channel_idx {idx_wxtest}")
    
    # Verify mapping is persistent (same channel returns same index)
    idx_weather_again = mesh._get_channel_idx("weather")
    assert idx_weather_again == idx_weather, "Channel mapping should be consistent"
    print(f"✓ Repeated lookup for 'weather' returns same channel_idx {idx_weather_again}")
    
    # Test more channels
    idx_alerts = mesh._get_channel_idx("alerts")
    assert idx_alerts == 3, f"Expected channel_idx=3 for 'alerts', got {idx_alerts}"
    print(f"✓ Channel 'alerts' -> channel_idx {idx_alerts}")
    
    # Verify all channels are different
    indices = [idx_default, idx_weather, idx_wxtest, idx_alerts]
    assert len(indices) == len(set(indices)), "All channel indices must be unique"
    print(f"✓ All channel indices are unique: {indices}")
    
    print()


def test_weather_bot_channel_mapping():
    """Test that WeatherBot correctly uses different channel indices"""
    print("=" * 60)
    print("TEST: WeatherBot Multi-Channel Transmission")
    print("=" * 60)
    
    bot = WeatherBot(node_id="WX_BOT", debug=False, channel="weather,wxtest")
    
    # Track the channel_idx used for each send
    channel_indices_used = []
    
    original_send = bot.mesh.send_message
    def track_send(content, msg_type, channel):
        channel_idx = bot.mesh._get_channel_idx(channel)
        channel_indices_used.append({"channel": channel, "channel_idx": channel_idx})
        return original_send(content, msg_type, channel)
    
    bot.mesh.send_message = track_send
    
    # Send a response to both channels
    bot.send_response("Test message")
    
    # Verify we sent to both channels with different indices
    assert len(channel_indices_used) == 2, f"Expected 2 sends, got {len(channel_indices_used)}"
    print(f"✓ Sent to {len(channel_indices_used)} channels")
    
    weather_send = channel_indices_used[0]
    wxtest_send = channel_indices_used[1]
    
    assert weather_send["channel"] == "weather", f"First send should be to 'weather'"
    assert wxtest_send["channel"] == "wxtest", f"Second send should be to 'wxtest'"
    print(f"✓ First send: channel='{weather_send['channel']}' -> channel_idx={weather_send['channel_idx']}")
    print(f"✓ Second send: channel='{wxtest_send['channel']}' -> channel_idx={wxtest_send['channel_idx']}")
    
    # Most importantly: verify different indices are used
    assert weather_send["channel_idx"] != wxtest_send["channel_idx"], \
        "Different channels must use different channel_idx values"
    print(f"✓ Different channel_idx values used: {weather_send['channel_idx']} != {wxtest_send['channel_idx']}")
    
    print()


def test_channel_idx_limit():
    """Test that we handle the channel limit gracefully"""
    print("=" * 60)
    print("TEST: Channel Index Limit Handling")
    print("=" * 60)
    
    mesh = MeshCore("test_node", debug=False)
    
    # Map 8 channels (indices 1-8, plus 0 for default)
    for i in range(1, 9):
        channel_name = f"channel{i}"
        idx = mesh._get_channel_idx(channel_name)
        print(f"  Channel '{channel_name}' -> channel_idx {idx}")
    
    # Try to add one more (should reuse idx 7)
    idx_overflow = mesh._get_channel_idx("channel9")
    assert idx_overflow == 7, f"Overflow channel should use idx 7, got {idx_overflow}"
    print(f"✓ Channel limit handled: 'channel9' -> channel_idx {idx_overflow} (reused)")
    
    print()


def test_problem_statement_fix():
    """
    Test the exact fix for the problem statement:
    Messages now go to BOTH weather and wxtest channels (different channel_idx values)
    instead of only appearing in wxtest
    """
    print("=" * 60)
    print("TEST: Problem Statement Fix Verification")
    print("=" * 60)
    print("Command: python3 weather_bot.py -n WX_BOT --channel weather,wxtest")
    print("Expected: Messages appear in BOTH weather AND wxtest channels")
    print()
    
    bot = WeatherBot(node_id="WX_BOT", debug=False, channel="weather,wxtest")
    
    # Capture what would be transmitted over LoRa
    lora_transmissions = []
    
    original_send = bot.mesh.send_message
    def capture_transmission(content, msg_type, channel):
        channel_idx = bot.mesh._get_channel_idx(channel)
        lora_transmissions.append({
            "content": content,
            "channel_name": channel,
            "channel_idx": channel_idx
        })
        return original_send(content, msg_type, channel)
    
    bot.mesh.send_message = capture_transmission
    
    # Simulate a weather request
    bot.send_response("Weather: 15°C, Sunny")
    
    print("LoRa Transmissions:")
    for i, tx in enumerate(lora_transmissions, 1):
        print(f"  {i}. Channel '{tx['channel_name']}' (idx={tx['channel_idx']}): {tx['content']}")
    
    # Verify the fix
    assert len(lora_transmissions) == 2, "Should transmit to 2 channels"
    assert lora_transmissions[0]["channel_name"] == "weather", "First should be weather"
    assert lora_transmissions[1]["channel_name"] == "wxtest", "Second should be wxtest"
    assert lora_transmissions[0]["channel_idx"] != lora_transmissions[1]["channel_idx"], \
        "CRITICAL FIX: Must use different channel_idx values"
    
    print()
    print("✅ FIX VERIFIED:")
    print(f"  • 'weather' channel uses channel_idx {lora_transmissions[0]['channel_idx']}")
    print(f"  • 'wxtest' channel uses channel_idx {lora_transmissions[1]['channel_idx']}")
    print(f"  • Different indices ensure both channels receive the message")
    print()


def main():
    """Run all channel index mapping tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 8 + "Channel Index Mapping Tests" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_channel_idx_mapping()
        test_weather_bot_channel_mapping()
        test_channel_idx_limit()
        test_problem_statement_fix()

        print("=" * 60)
        print("✅ All channel index mapping tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  ✓ Channel names are mapped to unique channel_idx values (1-7)")
        print("  ✓ Default/None channel uses channel_idx 0")
        print("  ✓ Mapping is persistent and consistent")
        print("  ✓ WeatherBot sends to different channel_idx for each channel")
        print("  ✓ Fix ensures messages appear in ALL specified channels")
        print()
        print("The Fix:")
        print("  Before: Both 'weather' and 'wxtest' used channel_idx=0")
        print("          → LoRa/firmware deduplicated → only one appeared")
        print("  After:  'weather' uses channel_idx=1, 'wxtest' uses channel_idx=2")
        print("          → Different indices → both messages transmitted")
        print()

        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
