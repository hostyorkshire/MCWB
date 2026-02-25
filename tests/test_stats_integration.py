#!/usr/bin/env python3
"""
Test statistics tracking integration
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil
import tempfile
import unittest
from pathlib import Path

from stats_tracker import StatsTracker


class TestStatsIntegration(unittest.TestCase):
    """Test statistics tracking functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary stats file for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.stats_file = self.temp_dir / "test_stats.json"
        self.tracker = StatsTracker(str(self.stats_file))

    def tearDown(self):
        """Clean up test fixtures"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_initial_stats(self):
        """Test initial stats are zero"""
        stats = self.tracker.get_stats()
        self.assertEqual(stats["total_requests"], 0)
        self.assertEqual(stats["total_errors"], 0)
        self.assertIsNone(stats["last_updated"])

    def test_record_request(self):
        """Test recording a request"""
        self.tracker.record_request("London")
        stats = self.tracker.get_stats()

        self.assertEqual(stats["total_requests"], 1)
        self.assertEqual(stats["locations"]["London"], 1)
        self.assertIsNotNone(stats["last_updated"])

    def test_record_multiple_requests(self):
        """Test recording multiple requests"""
        self.tracker.record_request("London")
        self.tracker.record_request("York")
        self.tracker.record_request("London")

        stats = self.tracker.get_stats()
        self.assertEqual(stats["total_requests"], 3)
        self.assertEqual(stats["locations"]["London"], 2)
        self.assertEqual(stats["locations"]["York"], 1)

    def test_record_error(self):
        """Test recording errors"""
        self.tracker.record_error("location_not_found")
        self.tracker.record_error("api_error")

        stats = self.tracker.get_stats()
        self.assertEqual(stats["total_errors"], 2)
        self.assertEqual(stats["error_types"]["location_not_found"], 1)
        self.assertEqual(stats["error_types"]["api_error"], 1)

    def test_get_top_locations(self):
        """Test getting top locations"""
        self.tracker.record_request("London")
        self.tracker.record_request("York")
        self.tracker.record_request("London")
        self.tracker.record_request("Manchester")
        self.tracker.record_request("London")

        top = self.tracker.get_top_locations(limit=2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0]["location"], "London")
        self.assertEqual(top[0]["count"], 3)
        self.assertEqual(top[1]["location"], "York")
        self.assertEqual(top[1]["count"], 1)

    def test_persistence(self):
        """Test that stats persist to file"""
        self.tracker.record_request("London")
        self.tracker.record_error("test_error")

        # Create new tracker instance with same file
        new_tracker = StatsTracker(str(self.stats_file))
        stats = new_tracker.get_stats()

        self.assertEqual(stats["total_requests"], 1)
        self.assertEqual(stats["total_errors"], 1)
        self.assertEqual(stats["locations"]["London"], 1)

    def test_get_recent_hourly(self):
        """Test getting recent hourly data"""
        self.tracker.record_request("London")
        hourly = self.tracker.get_recent_hourly(hours=24)

        self.assertEqual(len(hourly), 24)
        self.assertIn("hour", hourly[0])
        self.assertIn("count", hourly[0])

    def test_get_recent_daily(self):
        """Test getting recent daily data"""
        self.tracker.record_request("London")
        daily = self.tracker.get_recent_daily(days=7)

        self.assertEqual(len(daily), 7)
        self.assertIn("date", daily[0])
        self.assertIn("count", daily[0])


if __name__ == "__main__":
    print("Running Stats Integration Tests...")
    print("=" * 70)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStatsIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
