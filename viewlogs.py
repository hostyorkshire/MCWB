#!/usr/bin/env python3
"""
Log viewer utility for MCWB Weather Bot
Provides easy command-line access to view logs
"""

import sys
import os
import argparse
from pathlib import Path
import subprocess

# Get the logs directory
LOGS_DIR = Path(__file__).parent / "logs"

# Available log files
LOG_FILES = {
    "bot": "weather_bot.log",
    "bot-error": "weather_bot_error.log",
    "meshcore": "meshcore.log",
    "meshcore-error": "meshcore_error.log"
}


def list_logs():
    """List all available log files"""
    print("=" * 70)
    print("Available Log Files")
    print("=" * 70)
    
    if not LOGS_DIR.exists():
        print("No logs directory found!")
        return
    
    for log_type, filename in LOG_FILES.items():
        log_path = LOGS_DIR / filename
        if log_path.exists():
            size = log_path.stat().st_size
            size_str = format_size(size)
            print(f"  {log_type:20s} -> {filename:30s} ({size_str})")
        else:
            print(f"  {log_type:20s} -> {filename:30s} (not found)")
    
    # List any other log files
    print("\nOther files in logs/:")
    for file in LOGS_DIR.glob("*"):
        if file.name not in LOG_FILES.values() and file.is_file():
            size = file.stat().st_size
            size_str = format_size(size)
            print(f"  {file.name:50s} ({size_str})")


def format_size(bytes_size):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def view_log(log_type, lines=None, follow=False, errors_only=False, grep=None):
    """View a log file"""
    if log_type not in LOG_FILES:
        print(f"Error: Unknown log type '{log_type}'")
        print(f"Available types: {', '.join(LOG_FILES.keys())}")
        return 1
    
    log_path = LOGS_DIR / LOG_FILES[log_type]
    
    if not log_path.exists():
        print(f"Error: Log file not found: {log_path}")
        print("The log file will be created when the bot runs.")
        return 1
    
    try:
        if follow:
            # Use tail -f to follow the log
            cmd = ["tail", "-f", str(log_path)]
            if lines:
                cmd = ["tail", "-f", "-n", str(lines), str(log_path)]
            print(f"Following log: {log_path}")
            print("Press Ctrl+C to stop")
            print("-" * 70)
            subprocess.run(cmd)
        else:
            # Read and display the log
            with open(log_path, 'r') as f:
                log_lines = f.readlines()
            
            # Filter if requested
            if errors_only:
                log_lines = [line for line in log_lines if 'ERROR' in line or 'CRITICAL' in line]
            
            if grep:
                log_lines = [line for line in log_lines if grep.lower() in line.lower()]
            
            # Show last N lines if specified
            if lines:
                log_lines = log_lines[-lines:]
            
            # Display
            if not log_lines:
                print("No matching log entries found.")
            else:
                print(f"Log: {log_path}")
                print("-" * 70)
                for line in log_lines:
                    print(line, end='')
    
    except KeyboardInterrupt:
        print("\n\nStopped viewing log.")
        return 0
    except Exception as e:
        print(f"Error reading log: {e}")
        return 1
    
    return 0


def clear_logs(confirm=False):
    """Clear all log files"""
    if not confirm:
        response = input("Are you sure you want to delete all log files? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
    
    deleted = 0
    for log_file in LOGS_DIR.glob("*.log*"):
        if log_file.is_file():
            log_file.unlink()
            print(f"Deleted: {log_file.name}")
            deleted += 1
    
    print(f"\nDeleted {deleted} log file(s).")


def main():
    parser = argparse.ArgumentParser(
        description="View MCWB Weather Bot logs",
        epilog="""
Examples:
  # List all available logs
  ./viewlogs.py list

  # View last 50 lines of bot log
  ./viewlogs.py bot -n 50

  # Follow bot log (like tail -f)
  ./viewlogs.py bot -f

  # View only errors
  ./viewlogs.py bot --errors

  # Search for specific text
  ./viewlogs.py bot --grep "weather"

  # View all error logs
  ./viewlogs.py bot-error

  # Clear all logs
  ./viewlogs.py clear
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "command",
        choices=["list", "bot", "bot-error", "meshcore", "meshcore-error", "clear"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "-n", "--lines",
        type=int,
        help="Number of lines to show (from end of log)"
    )
    
    parser.add_argument(
        "-f", "--follow",
        action="store_true",
        help="Follow log in real-time (like tail -f)"
    )
    
    parser.add_argument(
        "--errors",
        action="store_true",
        help="Show only ERROR and CRITICAL messages"
    )
    
    parser.add_argument(
        "--grep",
        help="Search for specific text in log"
    )
    
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation (for clear command)"
    )
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_logs()
        return 0
    elif args.command == "clear":
        clear_logs(confirm=args.yes)
        return 0
    else:
        return view_log(
            args.command,
            lines=args.lines,
            follow=args.follow,
            errors_only=args.errors,
            grep=args.grep
        )


if __name__ == "__main__":
    sys.exit(main())
