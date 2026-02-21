#!/usr/bin/env python3
"""
Test to verify channel naming convention (with/without hash)
"""

from weather_bot import WeatherBot
from meshcore import MeshCore


def test_channel_naming_convention():
    """Test that demonstrates correct channel naming (without hash)"""
    print("=" * 70)
    print("CHANNEL NAMING CONVENTION TEST")
    print("=" * 70)
    print()
    
    print("Testing channel names with and without hash prefix...")
    print()
    
    # Test 1: Correct usage (no hash)
    print("1. Testing correct usage (no hash):")
    bot1 = WeatherBot(node_id="TEST1", announce_channel="wxtest")
    print(f"   announce_channel='wxtest' → bot.announce_channel='{bot1.announce_channel}'")
    assert bot1.announce_channel == "wxtest", "Channel name should be 'wxtest'"
    print("   ✓ Correct: No hash in channel name")
    print()
    
    # Test 2: Wrong usage (with hash)
    print("2. Testing wrong usage (with hash):")
    bot2 = WeatherBot(node_id="TEST2", announce_channel="#wxtest")
    print(f"   announce_channel='#wxtest' → bot.announce_channel='{bot2.announce_channel}'")
    assert bot2.announce_channel == "#wxtest", "Channel name includes the hash"
    print("   ⚠ Warning: Hash is part of channel name (creates different channel)")
    print()
    
    # Test 3: Compare
    print("3. Comparing channels:")
    print(f"   'wxtest' == '#wxtest'? {bot1.announce_channel == bot2.announce_channel}")
    assert bot1.announce_channel != bot2.announce_channel, "They should be different"
    print("   ✓ They are DIFFERENT channels")
    print()
    
    # Test 4: MeshCore channel naming
    print("4. Testing MeshCore channel naming:")
    mesh1 = MeshCore("node1")
    mesh1.start()
    
    # Map channels without hash
    idx1 = mesh1._get_channel_idx("weather")
    print(f"   'weather' → channel_idx {idx1}")
    
    # Map channel with hash (wrong but demonstrates the issue)
    idx2 = mesh1._get_channel_idx("#weather")
    print(f"   '#weather' → channel_idx {idx2}")
    
    assert idx1 != idx2, "Different names should get different indices"
    print(f"   ✓ 'weather' and '#weather' are treated as DIFFERENT channels")
    print(f"     (channel_idx {idx1} vs {idx2})")
    
    mesh1.stop()
    print()
    
    # Test 5: Command line style channel list
    print("5. Testing channel list (like --channel parameter):")
    
    # Correct
    correct_channel = "weather,alerts,news"
    channels_correct = [ch.strip() for ch in correct_channel.split(',')]
    print(f"   Correct: '{correct_channel}'")
    print(f"   Parsed: {channels_correct}")
    print("   ✓ No hash in any channel name")
    print()
    
    # Wrong
    wrong_channel = "#weather,#alerts,#news"
    channels_wrong = [ch.strip() for ch in wrong_channel.split(',')]
    print(f"   Wrong: '{wrong_channel}'")
    print(f"   Parsed: {channels_wrong}")
    print("   ⚠ Hash included in all channel names (creates wrong channels)")
    print()
    
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print()
    print("✓ In Python code, use channel names WITHOUT the hash (#)")
    print("✓ Examples: 'wxtest', 'weather', 'alerts', 'news'")
    print()
    print("✗ Do NOT use channel names WITH the hash (#)")
    print("✗ Wrong: '#wxtest', '#weather', '#alerts', '#news'")
    print()
    print("The hash (#) is only used in the MeshCore app UI for display.")
    print("It is NOT part of the actual channel name in the protocol.")
    print()


if __name__ == "__main__":
    test_channel_naming_convention()
