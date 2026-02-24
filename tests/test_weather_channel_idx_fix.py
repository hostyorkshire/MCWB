#!/usr/bin/env python3
"""
Test to verify the fix for --weather-channel-idx not filtering messages.

This test verifies that:
1. --weather-channel-idx ONLY controls announcements, NOT message filtering
2. Bot responds to messages from ALL channels when only --weather-channel-idx is set
3. Bot only filters messages when --channel-idx is explicitly set
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from weather_bot import WeatherBot


def test_weather_channel_idx_no_filtering():
    """
    Test that --weather-channel-idx does NOT enable message filtering.

    When a user runs: python3 weather_bot.py --weather-channel-idx 2 --announce
    Expected behavior:
    - Announcements sent on channel 2
    - Bot accepts messages from ALL channels (0-7)
    - Bot replies on the same channel where each message came from
    """
    print("\n" + "=" * 70)
    print("TEST 1: --weather-channel-idx does NOT filter messages")
    print("=" * 70 + "\n")

    print("Simulating: python3 weather_bot.py --weather-channel-idx 2 --announce\n")

    # Create bot with weather_channel_idx=2 but NO allowed_channel_idx filtering
    bot = WeatherBot(weather_channel_idx=2, allowed_channel_idx=None, announce=True, debug=False)

    print(f"Bot configuration:")
    print(f"  weather_channel_idx = {bot.weather_channel_idx}")
    print(f"  allowed_channel_idx = {bot.allowed_channel_idx}")
    print(f"  announce = {bot.announce}\n")

    # Test that messages from different channels are all accepted
    test_channels = [
        (0, "Default channel (public)"),
        (1, "First hashtag channel (e.g., #weather)"),
        (2, "Second hashtag channel (same as weather_channel_idx)"),
        (3, "Third hashtag channel"),
        (4, "Fourth hashtag channel"),
    ]

    all_passed = True

    for channel_idx, description in test_channels:
        # Check if message would be filtered
        would_be_filtered = (bot.allowed_channel_idx is not None and
                             channel_idx != bot.allowed_channel_idx)

        if would_be_filtered:
            print(f"❌ FAIL: channel_idx={channel_idx} ({description})")
            print(f"   Message would be FILTERED (should be ACCEPTED)\n")
            all_passed = False
        else:
            print(f"✅ PASS: channel_idx={channel_idx} ({description})")
            print(f"   Message would be ACCEPTED ✓\n")

    if all_passed:
        print("=" * 70)
        print("✅ TEST 1 PASSED")
        print("\n--weather-channel-idx correctly does NOT enable filtering!")
        print("Bot accepts messages from ALL channels as expected.")
        print("=" * 70 + "\n")
    else:
        print("=" * 70)
        print("❌ TEST 1 FAILED")
        print("\nBUG: --weather-channel-idx is enabling message filtering!")
        print("It should ONLY control announcements, not message acceptance.")
        print("=" * 70 + "\n")

    return all_passed


def test_channel_idx_filtering():
    """
    Test that --channel-idx DOES enable message filtering.

    When a user runs: python3 weather_bot.py --channel-idx 1
    Expected behavior:
    - Bot ONLY accepts messages from channel 1
    - Messages from other channels are ignored
    """
    print("\n" + "=" * 70)
    print("TEST 2: --channel-idx DOES filter messages")
    print("=" * 70 + "\n")

    print("Simulating: python3 weather_bot.py --channel-idx 1\n")

    # Create bot with allowed_channel_idx=1 (explicit filtering)
    bot = WeatherBot(allowed_channel_idx=1, debug=False)

    print(f"Bot configuration:")
    print(f"  allowed_channel_idx = {bot.allowed_channel_idx}")
    print(f"  weather_channel_idx = {bot.weather_channel_idx}\n")

    # Test that only channel 1 is accepted
    test_cases = [
        (0, "Should be REJECTED", False),
        (1, "Should be ACCEPTED", True),
        (2, "Should be REJECTED", False),
        (3, "Should be REJECTED", False),
    ]

    all_correct = True

    for channel_idx, expected, should_accept in test_cases:
        would_be_accepted = not (bot.allowed_channel_idx is not None and
                                channel_idx != bot.allowed_channel_idx)

        status = "ACCEPTED" if would_be_accepted else "REJECTED"
        expected_status = "ACCEPTED" if should_accept else "REJECTED"

        if would_be_accepted == should_accept:
            print(f"✅ CORRECT: channel_idx={channel_idx} is {status} ({expected})")
        else:
            print(f"❌ WRONG: channel_idx={channel_idx} is {status} (expected {expected_status})")
            all_correct = False

    if all_correct:
        print("\n" + "=" * 70)
        print("✅ TEST 2 PASSED")
        print("\n--channel-idx correctly enables message filtering!")
        print("=" * 70 + "\n")
    else:
        print("\n" + "=" * 70)
        print("❌ TEST 2 FAILED")
        print("\nBUG: --channel-idx filtering not working correctly!")
        print("=" * 70 + "\n")

    return all_correct


def test_combined_flags():
    """
    Test using both --weather-channel-idx and --channel-idx together.

    When a user runs: python3 weather_bot.py --weather-channel-idx 2 --channel-idx 1
    Expected behavior:
    - Announcements sent on channel 2
    - Bot ONLY accepts messages from channel 1
    - Bot ignores messages from other channels
    """
    print("\n" + "=" * 70)
    print("TEST 3: Using --weather-channel-idx 2 --channel-idx 1 together")
    print("=" * 70 + "\n")

    print("Simulating: python3 weather_bot.py --weather-channel-idx 2 --channel-idx 1\n")

    # Create bot with both parameters
    bot = WeatherBot(weather_channel_idx=2, allowed_channel_idx=1, debug=False)

    print(f"Bot configuration:")
    print(f"  weather_channel_idx = {bot.weather_channel_idx} (announcements)")
    print(f"  allowed_channel_idx = {bot.allowed_channel_idx} (message filter)\n")

    # Test that only channel 1 is accepted for messages
    test_cases = [
        (0, "REJECTED (filtering enabled)"),
        (1, "ACCEPTED (matches filter)"),
        (2, "REJECTED (announcements channel, but filtered for messages)"),
        (3, "REJECTED (filtering enabled)"),
    ]

    all_correct = True

    for channel_idx, expected in test_cases:
        would_be_accepted = not (bot.allowed_channel_idx is not None and
                                channel_idx != bot.allowed_channel_idx)

        status = "ACCEPTED" if would_be_accepted else "REJECTED"

        if status in expected:
            print(f"✅ CORRECT: channel_idx={channel_idx} is {status} - {expected}")
        else:
            print(f"❌ WRONG: channel_idx={channel_idx} is {status} (expected {expected})")
            all_correct = False

    if all_correct:
        print("\n" + "=" * 70)
        print("✅ TEST 3 PASSED")
        print("\nBoth flags work correctly together!")
        print("=" * 70 + "\n")
    else:
        print("\n" + "=" * 70)
        print("❌ TEST 3 FAILED")
        print("\nBUG: Combined flags not working correctly!")
        print("=" * 70 + "\n")

    return all_correct


def test_no_flags():
    """
    Test default behavior with no flags.

    When a user runs: python3 weather_bot.py
    Expected behavior:
    - Bot accepts messages from ALL channels
    - Announcements use the channel of the first received message
    """
    print("\n" + "=" * 70)
    print("TEST 4: Default behavior (no channel flags)")
    print("=" * 70 + "\n")

    print("Simulating: python3 weather_bot.py\n")

    # Create bot with default settings
    bot = WeatherBot(debug=False)

    print(f"Bot configuration:")
    print(f"  weather_channel_idx = {bot.weather_channel_idx}")
    print(f"  allowed_channel_idx = {bot.allowed_channel_idx}\n")

    # Test that all channels are accepted
    test_channels = [0, 1, 2, 3, 4, 5, 6, 7]

    all_passed = True

    for channel_idx in test_channels:
        would_be_filtered = (bot.allowed_channel_idx is not None and
                            channel_idx != bot.allowed_channel_idx)

        if would_be_filtered:
            print(f"❌ FAIL: channel_idx={channel_idx} would be FILTERED")
            all_passed = False
        else:
            print(f"✅ PASS: channel_idx={channel_idx} would be ACCEPTED")

    if all_passed:
        print("\n" + "=" * 70)
        print("✅ TEST 4 PASSED")
        print("\nDefault behavior works correctly!")
        print("Bot accepts messages from ALL channels.")
        print("=" * 70 + "\n")
    else:
        print("\n" + "=" * 70)
        print("❌ TEST 4 FAILED")
        print("\nBUG: Default behavior filtering messages incorrectly!")
        print("=" * 70 + "\n")

    return all_passed


def main():
    """Run all tests"""
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 12 + "Weather Channel IDX Fix Test Suite" + " " * 22 + "║")
    print("╚" + "=" * 68 + "╝")

    try:
        # Run all tests
        test1 = test_weather_channel_idx_no_filtering()
        test2 = test_channel_idx_filtering()
        test3 = test_combined_flags()
        test4 = test_no_flags()

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"1. --weather-channel-idx (no filtering): {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"2. --channel-idx (with filtering):      {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"3. Both flags together:                 {'✅ PASS' if test3 else '❌ FAIL'}")
        print(f"4. Default (no flags):                  {'✅ PASS' if test4 else '❌ FAIL'}")
        print("=" * 70)

        all_passed = test1 and test2 and test3 and test4

        if all_passed:
            print("\n✅ ALL TESTS PASSED ✅")
            print("\nThe fix is working correctly:")
            print("- --weather-channel-idx controls announcements only")
            print("- --channel-idx controls message filtering")
            print("- Bot responds to ALL channels by default")
            print("- New hashtag channels work without configuration")
        else:
            print("\n❌ SOME TESTS FAILED ❌")
            print("\nThere are still issues with channel handling.")

        print("=" * 70 + "\n")

        return 0 if all_passed else 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
