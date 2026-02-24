#!/usr/bin/env python3
"""
Test web dashboard functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from pathlib import Path
import tempfile
import shutil

# Import the Flask app
from web_dashboard import app, read_log_file, get_log_info


class TestWebDashboard(unittest.TestCase):
    """Test web dashboard functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create a temporary logs directory for testing
        self.test_logs_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_logs_dir.exists():
            shutil.rmtree(self.test_logs_dir)
    
    def test_index_page_loads(self):
        """Test that the index page loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MCWB Dashboard', response.data)
        self.assertIn(b'MeshCore Weather Bot', response.data)
    
    def test_status_api(self):
        """Test the status API endpoint"""
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        data = response.get_json()
        self.assertIn('status', data)
        self.assertIn('logs', data)
        self.assertIn('timestamp', data)
        
        # Check log file keys
        self.assertIn('bot', data['logs'])
        self.assertIn('bot_error', data['logs'])
        self.assertIn('meshcore', data['logs'])
        self.assertIn('meshcore_error', data['logs'])
    
    def test_logs_api(self):
        """Test the logs API endpoint"""
        response = self.client.get('/api/logs/bot')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        data = response.get_json()
        self.assertIn('log_type', data)
        self.assertIn('lines', data)
        self.assertIn('count', data)
        self.assertEqual(data['log_type'], 'bot')
    
    def test_invalid_log_type(self):
        """Test that invalid log types return 400"""
        response = self.client.get('/api/logs/invalid')
        self.assertEqual(response.status_code, 400)
    
    def test_read_log_file(self):
        """Test reading log files"""
        # Use the actual logs directory since functions are hardcoded
        from web_dashboard import LOGS_DIR
        
        # Create a test log file in the real logs directory
        test_log = LOGS_DIR / "test_dashboard.log"
        test_log.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        
        try:
            # Read last 3 lines
            lines = read_log_file("test_dashboard.log", lines=3)
            self.assertEqual(len(lines), 3)
            self.assertEqual(lines[0], "Line 3\n")
            self.assertEqual(lines[2], "Line 5\n")
        finally:
            # Clean up
            if test_log.exists():
                test_log.unlink()
    
    def test_get_log_info_existing(self):
        """Test getting info for existing log file"""
        from web_dashboard import LOGS_DIR
        
        # Create a test log file in the real logs directory
        test_log = LOGS_DIR / "test_dashboard_info.log"
        test_log.write_text("Test content")
        
        try:
            info = get_log_info("test_dashboard_info.log")
            self.assertTrue(info['exists'])
            self.assertGreater(info['size'], 0)
            self.assertIsNotNone(info['modified'])
        finally:
            # Clean up
            if test_log.exists():
                test_log.unlink()
    
    def test_get_log_info_nonexisting(self):
        """Test getting info for non-existing log file"""
        info = get_log_info("nonexistent.log")
        self.assertFalse(info['exists'])
        self.assertEqual(info['size'], 0)
        self.assertIsNone(info['modified'])
    
    def test_dark_theme_css(self):
        """Test that theme CSS variables are present"""
        response = self.client.get('/')
        self.assertIn(b'data-theme', response.data)
        self.assertIn(b'--bg-gradient-start', response.data)  # CSS variables
        self.assertIn(b'--text-color', response.data)  # CSS variables
        self.assertIn(b'#000000', response.data)  # Dark background color
        self.assertIn(b'#ffffff', response.data)  # White text color in dark mode


if __name__ == '__main__':
    print("Running Web Dashboard Tests...")
    print("=" * 70)
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWebDashboard)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
