#!/usr/bin/env python3
"""
Test that garbled/encrypted messages are properly sanitized in logs.
This prevents terminal corruption from control characters and binary data.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
from weather_bot import WeatherBot


def test_garbled_message_sanitization():
    """Test that garbled messages with control characters are sanitized in debug logs."""
    
    # Create bot with debug mode enabled
    bot = WeatherBot(port=None, debug=True)
    
    # Capture stdout to check log output
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    try:
        # Simulate receiving a garbled message with control characters
        # This mimics encrypted data from another channel
        garbled_text = "\x01gF\x15K3(~\x12=\u0227cMC"
        channel_idx = 0
        
        # Call the internal handler (this would normally be called by _dispatch)
        bot._handle_channel_message(garbled_text, channel_idx)
        
        # Get the logged output
        output = captured_output.getvalue()
        
        # Verify that control characters are escaped in the output
        # The output should contain literal "\x01" not the actual control character
        assert "\\x01" in output or "\\x" in output, \
            "Control characters should be escaped with \\xNN notation"
        
        # Verify that the raw binary \x01 byte is NOT in the output
        # (this would indicate unsanitized output)
        assert "\x01" not in output, \
            "Raw control character \\x01 should not appear in output"
        
        # Verify we don't have the literal bell/alert character
        assert "\x07" not in output, \
            "Raw control character \\x07 should not appear in output"
        
        print("✓ Test passed: Garbled messages are properly sanitized")
        return True
        
    finally:
        # Restore stdout
        sys.stdout = sys.__stdout__


def test_garbled_sender_sanitization():
    """Test that garbled sender names are sanitized in logs."""
    
    bot = WeatherBot(port=None, debug=True)
    
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    try:
        # Simulate a message with garbled sender name (before colon)
        garbled_sender_text = "\x02\x03GarbledSender\x07: Hello World"
        channel_idx = 0
        
        bot._handle_channel_message(garbled_sender_text, channel_idx)
        
        output = captured_output.getvalue()
        
        # Verify sender is sanitized
        assert "\\x02" in output or "\\x03" in output or "\\x" in output, \
            "Control characters in sender should be escaped"
        
        # Verify raw control characters are not present
        assert "\x02" not in output and "\x03" not in output and "\x07" not in output, \
            "Raw control characters should not appear in sender output"
        
        print("✓ Test passed: Garbled sender names are properly sanitized")
        return True
        
    finally:
        sys.stdout = sys.__stdout__


def test_weather_command_output_sanitization():
    """Test that print statements for weather commands sanitize user data."""
    
    bot = WeatherBot(port=None, debug=True)
    
    # Mock the _get_weather method to avoid actual API calls
    def mock_get_weather(location):
        return f"Mock weather for {location}"
    
    # Mock the _send_channel_msg to avoid serial operations
    def mock_send_channel_msg(text, channel_idx):
        pass  # Don't actually send anything
    
    original_get_weather = bot._get_weather
    original_send_channel_msg = bot._send_channel_msg
    bot._get_weather = mock_get_weather
    bot._send_channel_msg = mock_send_channel_msg
    
    captured_output = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured_output
    
    try:
        # Simulate a weather command from a garbled sender
        # The content "wx london" matches the command regex, so it will print
        garbled_sender_text = "\x01Garbled\x15: wx london"
        channel_idx = 0
        
        bot._handle_channel_message(garbled_sender_text, channel_idx)
        
        output = captured_output.getvalue()
        
        # Restore stdout before assertions so we can print results
        sys.stdout = original_stdout
        
        # Verify that the sender name in the print output is sanitized
        # Look for the WX request line
        lines = output.split('\n')
        wx_request_line = [l for l in lines if "WX request" in l]
        
        if wx_request_line:
            # Should contain escaped form, not raw control chars
            assert "\x01" not in wx_request_line[0], \
                "Raw control characters should not appear in WX request output"
            assert "\\x01" in wx_request_line[0] or "\\x15" in wx_request_line[0], \
                "Control characters should be escaped in WX request output"
        
        print("✓ Test passed: Weather command output properly sanitizes user data")
        return True
        
    finally:
        # Restore original methods and stdout
        bot._get_weather = original_get_weather
        bot._send_channel_msg = original_send_channel_msg
        sys.stdout = original_stdout


def test_send_message_log_sanitization():
    """Test that sent message logs are sanitized."""
    
    bot = WeatherBot(port=None, debug=True)
    
    # Test the sanitize function directly
    test_text = "Normal text with \x01 control \x15 chars"
    safe_text = bot._sanitize_for_log(test_text)
    
    # Verify sanitization works
    assert "\\x01" in safe_text, "Control char \\x01 should be escaped"
    assert "\\x15" in safe_text, "Control char \\x15 should be escaped"
    assert "\x01" not in safe_text, "Raw control char \\x01 should not be present"
    assert "\x15" not in safe_text, "Raw control char \\x15 should not be present"
    
    print("✓ Test passed: Send message logs are sanitized")
    return True


if __name__ == "__main__":
    print("Testing garbled message sanitization...\n")
    
    try:
        test_garbled_message_sanitization()
        test_garbled_sender_sanitization()
        test_send_message_log_sanitization()
        test_weather_command_output_sanitization()
        
        print("\n✅ All sanitization tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
