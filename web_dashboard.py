#!/usr/bin/env python3
"""
MCWB Web Dashboard
Dark-themed web interface for monitoring the MeshCore Weather Bot
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
import json
from datetime import datetime
from stats_tracker import StatsTracker

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Enable CORS for all routes to allow static website to fetch data
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Get the logs directory
LOGS_DIR = Path(__file__).parent / "logs"

# Initialize stats tracker
stats = StatsTracker()


def read_log_file(filename, lines=100):
    """Read last N lines from a log file"""
    log_path = LOGS_DIR / filename
    if not log_path.exists():
        return []
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return all_lines[-lines:] if lines else all_lines
    except Exception as e:
        return [f"Error reading log: {str(e)}"]


def get_log_info(filename):
    """Get log file information"""
    log_path = LOGS_DIR / filename
    if not log_path.exists():
        return {"exists": False, "size": 0, "modified": None}
    
    stat = log_path.stat()
    return {
        "exists": True,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    }


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get bot status"""
    log_files = {
        "bot": get_log_info("weather_bot.log"),
        "bot_error": get_log_info("weather_bot_error.log"),
        "meshcore": get_log_info("meshcore.log"),
        "meshcore_error": get_log_info("meshcore_error.log")
    }
    
    return jsonify({
        "status": "running" if any(f["exists"] for f in log_files.values()) else "stopped",
        "logs": log_files,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/logs/<log_type>')
def api_logs(log_type):
    """Get log content
    
    Security: log_type is validated against a whitelist to prevent
    path traversal attacks. Only predefined log files can be accessed.
    """
    # Whitelist of allowed log files - prevents path traversal
    log_map = {
        "bot": "weather_bot.log",
        "bot_error": "weather_bot_error.log",
        "meshcore": "meshcore.log",
        "meshcore_error": "meshcore_error.log"
    }
    
    if log_type not in log_map:
        return jsonify({"error": "Invalid log type"}), 400
    
    lines = read_log_file(log_map[log_type], lines=100)
    return jsonify({
        "log_type": log_type,
        "lines": lines,
        "count": len(lines)
    })


@app.route('/api/stats')
def api_stats():
    """Get usage statistics"""
    stats_data = stats.get_stats()
    
    return jsonify({
        "total_requests": stats_data.get("total_requests", 0),
        "total_errors": stats_data.get("total_errors", 0),
        "last_updated": stats_data.get("last_updated"),
        "success_rate": calculate_success_rate(
            stats_data.get("total_requests", 0),
            stats_data.get("total_errors", 0)
        )
    })


@app.route('/api/stats/hourly')
def api_stats_hourly():
    """Get hourly request statistics"""
    hourly_data = stats.get_recent_hourly(hours=24)
    return jsonify(hourly_data)


@app.route('/api/stats/daily')
def api_stats_daily():
    """Get daily request statistics"""
    daily_data = stats.get_recent_daily(days=7)
    return jsonify(daily_data)


@app.route('/api/stats/locations')
def api_stats_locations():
    """Get top requested locations"""
    top_locs = stats.get_top_locations(limit=10)
    return jsonify(top_locs)


def calculate_success_rate(total, errors):
    """Calculate success rate percentage"""
    if total == 0:
        return 0.0
    return round(((total - errors) / total) * 100, 1)


def main():
    """Run the web dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCWB Web Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1 for localhost only)")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    print(f"=" * 70)
    print(f"MCWB Web Dashboard")
    print(f"=" * 70)
    print(f"Starting web server on http://{args.host}:{args.port}")
    print(f"Press Ctrl+C to stop")
    print(f"=" * 70)
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
