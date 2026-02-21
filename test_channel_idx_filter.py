#!/usr/bin/env python3
"""
Test channel index filtering functionality.
Verifies that the bot only responds to messages from the specified channel_idx.
"""

import sys
import io
from contextlib import redirect_stdout
from unittest.mock import Mock
from weather_bot import WeatherBot


def test_no_filter():
    """Test that bot accepts messages from all channels when no filter is set."""
    print("\n" + "="*70)
    print("TEST 1: No channel filter (accepts all channels)")
    print("="*70)
    
    bot = WeatherBot(debug=True, allowed_channel_idx=None)
    # Mock serial connection
    bot._ser = Mock()
    bot._ser.write = Mock()
    
    # Simulate messages from different channels
    test_cases = [
        (0, "User1: wx London", True),
        (1, "User2: wx Manchester", True),
        (2, "User3: wx York", True),
    ]
    
    for channel_idx, text, should_process in test_cases:
        output = io.StringIO()
        with redirect_stdout(output):
            bot._handle_channel_message(text, channel_idx)
        result = output.getvalue()
        
        # Check if weather request was processed
        processed = "WX request" in result
        
        if processed == should_process:
            print(f"✅ PASS: channel_idx={channel_idx} - {'processed' if processed else 'ignored'} (expected)")
        else:
            print(f"❌ FAIL: channel_idx={channel_idx} - {'processed' if processed else 'ignored'} (unexpected)")
            return False
    
    return True


def test_with_filter():
    """Test that bot only accepts messages from the specified channel_idx."""
    print("\n" + "="*70)
    print("TEST 2: Channel filter set to channel_idx=1 (weather channel)")
    print("="*70)
    
    bot = WeatherBot(debug=True, allowed_channel_idx=1)
    # Mock serial connection
    bot._ser = Mock()
    bot._ser.write = Mock()
    
    # Simulate messages from different channels
    test_cases = [
        (0, "User1: wx London", False),      # Should be ignored
        (1, "User2: wx Manchester", True),   # Should be processed
        (2, "User3: wx York", False),        # Should be ignored
    ]
    
    for channel_idx, text, should_process in test_cases:
        output = io.StringIO()
        with redirect_stdout(output):
            bot._handle_channel_message(text, channel_idx)
        result = output.getvalue()
        
        # Check if weather request was processed
        processed = "WX request" in result
        
        if processed == should_process:
            print(f"✅ PASS: channel_idx={channel_idx} - {'processed' if processed else 'ignored'} (expected)")
        else:
            print(f"❌ FAIL: channel_idx={channel_idx} - {'processed' if processed else 'ignored'} (unexpected)")
            return False
    
    return True


def test_filter_logs_rejection():
    """Test that rejected messages are logged in debug mode."""
    print("\n" + "="*70)
    print("TEST 3: Verify rejected messages are logged")
    print("="*70)
    
    bot = WeatherBot(debug=True, allowed_channel_idx=1)
    # Mock serial connection
    bot._ser = Mock()
    bot._ser.write = Mock()
    
    # Capture log output
    output = io.StringIO()
    original_log = bot._log
    
    logged_messages = []
    def capture_log(msg):
        logged_messages.append(msg)
        original_log(msg)
    
    bot._log = capture_log
    
    # Send message on wrong channel
    bot._handle_channel_message("User1: wx London", 0)
    
    # Check if rejection was logged
    rejection_logged = any("Ignoring message" in msg and "channel_idx=0" in msg for msg in logged_messages)
    
    if rejection_logged:
        print("✅ PASS: Rejection was logged in debug mode")
        return True
    else:
        print("❌ FAIL: Rejection was not logged")
        return False


def main():
    """Run all tests."""
    print("\n╔" + "="*68 + "╗")
    print("║" + " "*18 + "Channel Index Filter Tests" + " "*24 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        test1 = test_no_filter()
        test2 = test_with_filter()
        test3 = test_filter_logs_rejection()
        
        print("\n" + "="*70)
        if test1 and test2 and test3:
            print("✅ ALL TESTS PASSED")
            print("\nChannel index filtering is working correctly:")
            print("- Without filter: Bot accepts messages from all channels")
            print("- With filter: Bot only accepts messages from specified channel_idx")
            print("- Rejected messages are logged in debug mode")
        else:
            print("❌ SOME TESTS FAILED")
        print("="*70 + "\n")
        
        return 0 if (test1 and test2 and test3) else 1
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
