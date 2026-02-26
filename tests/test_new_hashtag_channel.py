#!/usr/bin/env python3
"""
Test to verify that the bot responds to messages on new hashtag channels
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from weather_bot import WeatherBot


def test_new_hashtag_channel():
    """
    Test that WeatherBot responds to weather commands on different channel indices.
    This simulates the scenario where a user creates a new hashtag channel in the
    MeshCore app and expects the bot to respond.
    """
    print("\n" + "=" * 70)
    print("TEST: Bot Response on New Hashtag Channels")
    print("=" * 70 + "\n")

    # Create bot without any channel filtering (default behavior)
    bot = WeatherBot(debug=True)

    # Test different channel indices (0-7)
    test_channels = [
        (0, "Default channel (public)"),
        (1, "First hashtag channel (e.g., #weather)"),
        (2, "Second hashtag channel (e.g., #alerts)"),
        (3, "Third hashtag channel (e.g., #news)"),
        (5, "Random hashtag channel"),
    ]

    all_passed = True

    for channel_idx, description in test_channels:
        print(f"\n--- Testing {description} (channel_idx={channel_idx}) ---")

        # Simulate receiving a weather command message
        # Format: "SenderName: wx location"
        test_message = f"TestUser: wx London"

        # Check if the message would be filtered out
        if bot.allowed_channel_idx is not None and channel_idx != bot.allowed_channel_idx:
            print(f"❌ FAIL: Message would be FILTERED OUT")
            print(f"   Bot has allowed_channel_idx={bot.allowed_channel_idx}")
            print(f"   But message arrived on channel_idx={channel_idx}")
            all_passed = False
        else:
            print(f"✅ PASS: Message would be ACCEPTED")
            print(f"   Bot has allowed_channel_idx={bot.allowed_channel_idx} (None = accepts all)")

            # Test that the command would be parsed correctly
            content = test_message.split(": ", 1)[1] if ": " in test_message else test_message
            location = bot._parse_command(content)
            if location:
                print(f"   Command parsed successfully: location = '{location}'")
            else:
                print(f"   ⚠️  Warning: Command not recognized")

    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nBot correctly accepts messages from ALL channels!")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nBot is filtering out messages from some channels!")
    print("=" * 70 + "\n")

    return all_passed


def test_with_channel_filtering():
    """
    Test that channel filtering works when explicitly configured.
    """
    print("\n" + "=" * 70)
    print("TEST: Bot with Channel Filtering (--channel-idx 1)")
    print("=" * 70 + "\n")

    # Create bot WITH channel filtering (--channel-idx 1)
    bot = WeatherBot(allowed_channel_idx=1, debug=True)

    print(f"Bot configured with allowed_channel_idx={bot.allowed_channel_idx}")
    print(f"This simulates running: python3 weather_bot.py --channel-idx 1\n")

    # Test different channel indices
    test_cases = [
        (0, "Should be REJECTED", False),
        (1, "Should be ACCEPTED", True),
        (2, "Should be REJECTED", False),
        (3, "Should be REJECTED", False),
    ]

    all_correct = True

    for channel_idx, expected, should_accept in test_cases:
        print(f"Testing channel_idx={channel_idx}: {expected}")

        will_be_accepted = not (bot.allowed_channel_idx is not None and channel_idx != bot.allowed_channel_idx)

        if will_be_accepted == should_accept:
            print(f"  ✅ CORRECT: {'ACCEPTED' if will_be_accepted else 'REJECTED'}")
        else:
            print(
                f"  ❌ WRONG: {'ACCEPTED' if will_be_accepted else 'REJECTED'} (expected {'ACCEPTED' if should_accept else 'REJECTED'})"
            )
            all_correct = False

    print("\n" + "=" * 70)
    if all_correct:
        print("✅ FILTERING TESTS PASSED")
    else:
        print("❌ FILTERING TESTS FAILED")
    print("=" * 70 + "\n")

    return all_correct


def main():
    """Run all tests"""
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "New Hashtag Channel Test Suite" + " " * 23 + "║")
    print("╚" + "=" * 68 + "╝")

    try:
        # Test 1: Default behavior (no filtering)
        test1_passed = test_new_hashtag_channel()

        # Test 2: With channel filtering
        test2_passed = test_with_channel_filtering()

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Default behavior (no filtering): {'✅ PASS' if test1_passed else '❌ FAIL'}")
        print(f"With channel filtering:          {'✅ PASS' if test2_passed else '❌ FAIL'}")
        print("=" * 70 + "\n")

        return 0 if (test1_passed and test2_passed) else 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
