#!/bin/bash
# Quick log viewer for MCWB Weather Bot
# Usage: ./logs [command] [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/viewlogs.py" "$@"
