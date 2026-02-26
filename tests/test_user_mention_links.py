#!/usr/bin/env python3
"""
Test that @user mentions in bot replies are converted to clickable links.

This test verifies:
1. Bot formats @mentions as markdown-style links: [@username](meshcore://user/username)
2. Markdown-style mention links are made clickable by MeshCore mobile/desktop app
3. JavaScript dashboard function converts both plain @mentions and markdown-style mentions to HTML links with proper href attributes
4. Username patterns are correctly detected and sanitized

Note: Markdown-style link format is used for mentions in bot responses for universal compatibility.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import unittest


class TestUserMentionLinks(unittest.TestCase):
    """Test user mention link conversion logic"""

    def test_mention_pattern_detection(self):
        """Test that the regex pattern can detect @username mentions"""
        # This is the pattern used in the JavaScript: /@([a-zA-Z0-9_.-]+)/g
        pattern = r"@([a-zA-Z0-9_.-]+)"

        # Test cases
        test_cases = [
            ("hi @john_doe", ["john_doe"]),
            ("hi @alice and @bob", ["alice", "bob"]),
            ("@user_node-123", ["user_node-123"]),
            ("hello @test.user", ["test.user"]),
            ("hi @user_node-123.test", ["user_node-123.test"]),
            ("no mentions here", []),
            ("@", []),  # @ without username should not match
        ]

        for text, expected_usernames in test_cases:
            matches = re.findall(pattern, text)
            self.assertEqual(matches, expected_usernames, f"Failed for text: {text}")

    def test_markdown_link_pattern_detection(self):
        """Test that the regex pattern can detect markdown-style @username mention links"""
        # This is the pattern used in the JavaScript for markdown links:
        # /\[@([a-zA-Z0-9_.-]+)\]\(meshcore:\/\/user\/([a-zA-Z0-9_.-]+)\)/g
        pattern = r"\[@([a-zA-Z0-9_.-]+)\]\(meshcore://user/([a-zA-Z0-9_.-]+)\)"

        # Test cases - should extract both the display name and the URL username
        test_cases = [
            ("hi [@john_doe](meshcore://user/john_doe)", [("john_doe", "john_doe")]),
            ("[@alice](meshcore://user/alice) and [@bob](meshcore://user/bob)", [("alice", "alice"), ("bob", "bob")]),
            ("no markdown links here", []),
            ("hi @user", []),  # Plain @mention should not match markdown pattern
        ]

        for text, expected_matches in test_cases:
            matches = re.findall(pattern, text)
            self.assertEqual(matches, expected_matches, f"Failed for text: {text}")

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
        self.assertIn("&lt;script&gt;", escaped)
        self.assertIn("&lt;/script&gt;", escaped)
        self.assertIn("@user", escaped)  # @mention should still be present

    def test_weather_bot_sends_mentions(self):
        """Test that the weather bot no longer includes @username mentions in responses"""
        from unittest.mock import MagicMock

        from weather_bot import WeatherBot

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
                "weather_code": 0,
            }
        }

        # Format response - sender parameter no longer used
        response = bot.format_weather_response(location_data, weather_data)

        # Verify @mention is NOT included
        self.assertNotIn("[@testuser](meshcore://user/testuser)", response)
        self.assertNotIn("hi @", response.lower())
        # Response should start with location
        self.assertTrue(response.startswith("York, GB\n"))


if __name__ == "__main__":
    print("Running User Mention Link Tests...")
    print("=" * 70)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUserMentionLinks)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
