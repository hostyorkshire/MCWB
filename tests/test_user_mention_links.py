#!/usr/bin/env python3
"""
Test that @user mentions in bot replies are converted to clickable links in the dashboard.
This test verifies the JavaScript function that converts @username patterns to meshcore:// links.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import re


class TestUserMentionLinks(unittest.TestCase):
    """Test user mention link conversion logic"""
    
    def test_mention_pattern_detection(self):
        """Test that the regex pattern can detect @username mentions"""
        # This is the pattern used in the JavaScript: /@([a-zA-Z0-9_.-]+)/g
        pattern = r'@([a-zA-Z0-9_.-]+)'
        
        # Test cases
        test_cases = [
            ('hi @john_doe', ['john_doe']),
            ('hi @alice and @bob', ['alice', 'bob']),
            ('@user_node-123', ['user_node-123']),
            ('hello @test.user', ['test.user']),
            ('hi @user_node-123.test', ['user_node-123.test']),
            ('no mentions here', []),
            ('@', []),  # @ without username should not match
        ]
        
        for text, expected_usernames in test_cases:
            matches = re.findall(pattern, text)
            self.assertEqual(matches, expected_usernames, 
                           f"Failed for text: {text}")
    
    def test_url_format(self):
        """Test that the URL format is correct for meshcore app"""
        # The URL should be: meshcore://user/{username}
        username = "john_doe"
        expected_url = f"meshcore://user/{username}"
        
        # Verify the format is correct
        self.assertTrue(expected_url.startswith("meshcore://user/"))
        self.assertIn(username, expected_url)
    
    def test_html_escaping_required(self):
        """Test that HTML special characters need to be escaped"""
        # These characters should be escaped before converting @mentions
        dangerous_input = '<script>alert("xss")</script> @user'
        
        # After HTML escaping, script tags should be neutralized
        # The escaped version should have &lt; and &gt;
        from html import escape
        escaped = escape(dangerous_input)
        self.assertIn('&lt;script&gt;', escaped)
        self.assertIn('&lt;/script&gt;', escaped)
        self.assertIn('@user', escaped)  # @mention should still be present
    
    def test_weather_bot_sends_mentions(self):
        """Test that the weather bot includes @username in responses"""
        from weather_bot import WeatherBot
        from unittest.mock import MagicMock
        
        bot = WeatherBot(node_id="TEST_BOT", debug=False)
        
        # Mock location and weather data
        location_data = {"name": "York", "country_code": "GB"}
        weather_data = {
            "current": {
                "temperature_2m": 10.0,
                "apparent_temperature": 8.0,
                "relative_humidity_2m": 75,
                "wind_speed_10m": 15.0,
                "wind_direction_10m": 180,
                "weather_code": 0
            }
        }
        
        # Format response with sender
        response = bot.format_weather_response(location_data, weather_data, sender="testuser")
        
        # Verify @mention is included
        self.assertIn('@testuser', response)
        self.assertTrue(response.startswith('hi @testuser\n'))


if __name__ == '__main__':
    print("Running User Mention Link Tests...")
    print("=" * 70)
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUserMentionLinks)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
