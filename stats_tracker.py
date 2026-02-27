#!/usr/bin/env python3
"""
Statistics tracker for MCWB
Tracks usage metrics for the dashboard
"""

import json
import os
import threading
from datetime import datetime, timedelta


class StatsTracker:
    """Track and persist usage statistics for the weather bot"""

    # Maximum number of recent users to track
    MAX_RECENT_USERS = 50

    def __init__(self, stats_file="logs/stats.json"):
        self.stats_file = stats_file
        self.lock = threading.Lock()
        self.stats = self._load_stats()

    def _load_stats(self):
        """Load stats from file or create default structure"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        return {
            "total_requests": 0,
            "total_errors": 0,
            "locations": {},
            "hourly_requests": {},
            "daily_requests": {},
            "error_types": {},
            "last_updated": None,
            "recent_users": [],
        }

    def _save_stats(self):
        """Save stats to file"""
        try:
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            with open(self.stats_file, "w") as f:
                json.dump(self.stats, f, indent=2)
        except IOError:
            pass

    def record_request(self, location=None, user=None):
        """Record a weather request"""
        with self.lock:
            self.stats["total_requests"] += 1

            # Track location
            if location:
                if location not in self.stats["locations"]:
                    self.stats["locations"][location] = 0
                self.stats["locations"][location] += 1

            # Track hourly requests
            now = datetime.now()
            hour_key = now.strftime("%Y-%m-%d %H:00")
            if hour_key not in self.stats["hourly_requests"]:
                self.stats["hourly_requests"][hour_key] = 0
            self.stats["hourly_requests"][hour_key] += 1

            # Track daily requests
            day_key = now.strftime("%Y-%m-%d")
            if day_key not in self.stats["daily_requests"]:
                self.stats["daily_requests"][day_key] = 0
            self.stats["daily_requests"][day_key] += 1

            # Track recent users
            if user:
                # Initialize recent_users list if it doesn't exist (for backward compatibility)
                if "recent_users" not in self.stats:
                    self.stats["recent_users"] = []
                
                # Add user with timestamp
                user_entry = {
                    "user": user,
                    "timestamp": now.isoformat(),
                }
                
                # Add to beginning of list
                self.stats["recent_users"].insert(0, user_entry)
                
                # Keep only last MAX_RECENT_USERS users
                self.stats["recent_users"] = self.stats["recent_users"][:self.MAX_RECENT_USERS]

            self.stats["last_updated"] = now.isoformat()
            self._save_stats()

    def record_error(self, error_type="unknown"):
        """Record an error"""
        with self.lock:
            self.stats["total_errors"] += 1

            if error_type not in self.stats["error_types"]:
                self.stats["error_types"][error_type] = 0
            self.stats["error_types"][error_type] += 1

            self.stats["last_updated"] = datetime.now().isoformat()
            self._save_stats()

    def get_stats(self):
        """Get current stats"""
        with self.lock:
            return self.stats.copy()

    def get_recent_hourly(self, hours=24):
        """Get requests for the last N hours"""
        with self.lock:
            now = datetime.now()
            result = []

            for i in range(hours):
                hour = now - timedelta(hours=i)
                hour_key = hour.strftime("%Y-%m-%d %H:00")
                count = self.stats["hourly_requests"].get(hour_key, 0)
                result.append({"hour": hour_key, "count": count})

            # Return in chronological order (oldest first)
            return list(reversed(result))

    def get_recent_daily(self, days=7):
        """Get requests for the last N days"""
        with self.lock:
            now = datetime.now()
            result = []

            for i in range(days):
                day = now - timedelta(days=i)
                day_key = day.strftime("%Y-%m-%d")
                count = self.stats["daily_requests"].get(day_key, 0)
                result.append({"date": day_key, "count": count})

            # Return in chronological order (oldest first)
            return list(reversed(result))

    def get_top_locations(self, limit=10):
        """Get top N requested locations"""
        with self.lock:
            sorted_locs = sorted(self.stats["locations"].items(), key=lambda x: x[1], reverse=True)
            return [{"location": loc, "count": count} for loc, count in sorted_locs[:limit]]

    def get_recent_users(self, limit=10):
        """Get last N recent users"""
        with self.lock:
            # Initialize recent_users if it doesn't exist (for backward compatibility)
            if "recent_users" not in self.stats:
                self.stats["recent_users"] = []
            
            return self.stats["recent_users"][:limit]

    def reset_stats(self):
        """Reset all statistics to zero"""
        with self.lock:
            self.stats = {
                "total_requests": 0,
                "total_errors": 0,
                "locations": {},
                "hourly_requests": {},
                "daily_requests": {},
                "error_types": {},
                "last_updated": None,
                "recent_users": [],
            }
            self._save_stats()
