#!/usr/bin/env python3
"""
MCWB Web Dashboard
Dark-themed web interface for monitoring the MeshCore Weather Bot
"""

import sys
import socket
from pathlib import Path

# Check for required dependencies before importing
try:
    from flask import Flask, render_template, jsonify
    from flask_cors import CORS
except ImportError:
    print("=" * 70)
    print("ERROR: Required dependencies not installed")
    print("=" * 70)
    print()
    print("The web dashboard requires Flask and flask-cors.")
    print()
    print("Modern Python installations (Python 3.11+) require using a virtual")
    print("environment to install packages. Follow these steps IN ORDER:")
    print()
    print("STEP 1: Create a virtual environment")
    print("   python3 -m venv venv")
    print()
    print("STEP 2: Activate the virtual environment (IMPORTANT!)")
    print("   source venv/bin/activate")
    print()
    print("   ⚠️  You MUST activate the venv before installing packages!")
    print("   Your prompt should show '(venv)' when activated.")
    print()
    print("STEP 3: Install dependencies (only after activating venv)")
    print("   pip install -r requirements.txt")
    print()
    print("STEP 4: Run the dashboard (venv should still be activated)")
    print("   python3 web_dashboard.py --host 0.0.0.0 --ssl")
    print()
    print("If you're already in a virtual environment, install dependencies with:")
    print("   pip install -r requirements.txt")
    print()
    print("Or install manually:")
    print("   pip install flask>=2.3.2 flask-cors>=4.0.0")
    print()
    print("=" * 70)
    sys.exit(78)  # EX_CONFIG (78) - Configuration error, don't retry

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


@app.route('/api/channels')
def api_channels():
    """Get active channels from the LORA meshcore radio"""
    channels_file = Path(__file__).parent / "logs" / "channels.json"
    
    if not channels_file.exists():
        return jsonify({
            "channels": [],
            "last_updated": None
        })
    
    try:
        import json
        with open(channels_file, 'r') as f:
            data = json.load(f)
            # Format channel names with # prefix for display
            formatted_channels = []
            for ch in data.get("channels", []):
                channel_name = ch.get("channel_name")
                if channel_name:
                    # Add # prefix for display (e.g., "weather" -> "#weather")
                    formatted_channels.append(f"#{channel_name}")
                elif ch.get("channel_idx") == 0:
                    # Channel 0 is the default/public channel
                    formatted_channels.append("#public")
                else:
                    # Unknown named channel - show as index
                    formatted_channels.append(f"#channel{ch.get('channel_idx')}")
            
            return jsonify({
                "channels": formatted_channels,
                "last_updated": data.get("last_updated")
            })
    except (json.JSONDecodeError, IOError):
        return jsonify({
            "channels": [],
            "last_updated": None
        })


def calculate_success_rate(total, errors):
    """Calculate success rate percentage"""
    if total == 0:
        return 0.0
    return round(((total - errors) / total) * 100, 1)


def get_local_ip():
    """Get the local IP address for network access"""
    try:
        # Create a socket to get the local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.1)
            # Connect to a public DNS server (doesn't actually send data)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception:
        # Fallback: try to get from hostname
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return None


def main():
    """Run the web dashboard"""
    import argparse

    parser = argparse.ArgumentParser(description="MCWB Web Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0 for network access)")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--ssl", action="store_true", help="Enable HTTPS with SSL certificate")
    parser.add_argument("--cert", default="cert.pem", help="SSL certificate file (default: cert.pem)")
    parser.add_argument("--key", default="key.pem", help="SSL private key file (default: key.pem)")

    args = parser.parse_args()

    print("=" * 70)
    print("MCWB Web Dashboard")
    print("=" * 70)

    # Get local IP for network access
    local_ip = get_local_ip()
    
    # Determine protocol
    protocol = "https" if args.ssl else "http"

    print()
    print("🌐 Dashboard will be accessible at:")
    print(f"   • Local:   {protocol}://localhost:{args.port}")
    if args.host == "0.0.0.0" and local_ip:
        print(f"   • Network: {protocol}://{local_ip}:{args.port}")
        print()
        if args.ssl:
            print("🔒 HTTPS enabled with SSL certificate")
            print(f"   Certificate: {args.cert}")
            print(f"   Private Key: {args.key}")
            print()
            print("⚠️  Self-signed certificates will show browser warnings")
            print("   This is normal - click 'Advanced' and proceed")
        else:
            print("⚠️  Running in HTTP mode (not HTTPS)")
            print()
            print("   IMPORTANT: Use the HTTP URL shown above!")
            print(f"   ✅ Correct:   http://{local_ip}:{args.port}")
            print(f"   ❌ Wrong:     https://{local_ip}:{args.port}")
            print()
            print("   If your browser shows an SSL/HTTPS error, make sure you're")
            print("   using 'http://' (not 'https://') in the address bar.")
            print()
            print("   Dashboard is accessible on your local network.")
            print("   Only use on trusted networks (home/private networks).")
            print("   To restrict to localhost only: --host 127.0.0.1")
            print()
            print("💡 To enable HTTPS (secure connection), use: --ssl")
            print("   (You'll need to generate SSL certificates first)")
    elif args.host == "127.0.0.1":
        print()
        print("ℹ️  Dashboard restricted to localhost only")
        print("   For network access, use: --host 0.0.0.0")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)

    # Check SSL certificate files if SSL is enabled
    if args.ssl:
        from pathlib import Path
        cert_path = Path(args.cert)
        key_path = Path(args.key)
        
        if not cert_path.exists() or not key_path.exists():
            print()
            print("❌ ERROR: SSL certificate files not found!")
            print()
            print("Generate a self-signed certificate with:")
            print(f"   python3 generate_ssl_cert.py --hostname {local_ip or '192.168.1.109'}")
            print()
            print("Then start the dashboard with:")
            print("   python3 web_dashboard.py --ssl")
            print()
            sys.exit(1)
        
        # Run with SSL
        ssl_context = (str(cert_path), str(key_path))
        app.run(host=args.host, port=args.port, debug=args.debug, ssl_context=ssl_context)
    else:
        # Run without SSL
        app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
