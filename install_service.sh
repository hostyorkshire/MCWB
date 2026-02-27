#!/bin/bash
# Installation script for MCWB systemd service on Raspberry Pi
# This script sets up the weather bot to run automatically on boot

set -e  # Exit on error

echo "================================================"
echo "MCWB - MeshCore Weather Bot Service Installer"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Error: Do not run this script as root (don't use sudo)"
    echo "   The script will ask for sudo password when needed"
    exit 1
fi

# Get current user and directory
CURRENT_USER=$(whoami)
INSTALL_DIR=$(pwd)

echo "📋 Installation Summary:"
echo "   User: $CURRENT_USER"
echo "   Installation Directory: $INSTALL_DIR"
echo ""

# Check if we're in the right directory
if [ ! -f "weather_bot.py" ]; then
    echo "❌ Error: weather_bot.py not found in current directory"
    echo "   Please run this script from the MCWB directory"
    exit 1
fi

if [ ! -f "weather_bot.service" ]; then
    echo "❌ Error: weather_bot.service not found in current directory"
    exit 1
fi

# Check if Python dependencies are installed
echo "🔍 Checking Python dependencies..."

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    # Not in a venv, check if one exists
    if [ -d "venv" ] && [ -f "venv/bin/python3" ]; then
        echo "📦 Virtual environment found at ./venv"
        echo "   Checking if dependencies are installed in venv..."
        if ./venv/bin/python3 -c "import serial" 2>/dev/null; then
            echo "✅ Python dependencies OK in virtual environment"
            USE_VENV=true
            PYTHON_PATH="$INSTALL_DIR/venv/bin/python3"
        else
            echo "⚠️  Dependencies not installed in venv"
            echo "   Installing dependencies in virtual environment..."
            ./venv/bin/pip install -r requirements.txt
            USE_VENV=true
            PYTHON_PATH="$INSTALL_DIR/venv/bin/python3"
        fi
    else
        # No venv, try system python
        if python3 -c "import serial" 2>/dev/null; then
            echo "✅ Python dependencies OK (system-wide)"
            USE_VENV=false
            PYTHON_PATH="/usr/bin/python3"
        else
            echo "⚠️  pyserial not installed"
            echo ""
            echo "📦 Creating virtual environment (recommended for newer systems)..."
            if ! python3 -m venv venv; then
                echo "❌ Failed to create virtual environment"
                echo "   You may need to install python3-venv:"
                echo "   sudo apt-get install python3-venv"
                exit 1
            fi
            echo "   Installing dependencies in virtual environment..."
            if ! ./venv/bin/pip install -r requirements.txt; then
                echo "❌ Failed to install dependencies"
                exit 1
            fi
            USE_VENV=true
            PYTHON_PATH="$INSTALL_DIR/venv/bin/python3"
            echo "✅ Virtual environment created and dependencies installed"
        fi
    fi
else
    # Already in a venv
    echo "✅ Running in virtual environment: $VIRTUAL_ENV"
    if python3 -c "import serial" 2>/dev/null; then
        echo "✅ Python dependencies OK"
        USE_VENV=true
        PYTHON_PATH="$VIRTUAL_ENV/bin/python3"
    else
        echo "⚠️  Dependencies not installed"
        echo "   Installing dependencies..."
        pip install -r requirements.txt
        USE_VENV=true
        PYTHON_PATH="$VIRTUAL_ENV/bin/python3"
    fi
fi

# Check if user is in dialout group
if ! groups "$CURRENT_USER" | grep -q dialout; then
    echo ""
    echo "⚠️  Adding user to 'dialout' group for USB access..."
    sudo usermod -a -G dialout "$CURRENT_USER"
    echo "✅ User added to dialout group"
    echo "   ⚠️  You will need to log out and log back in (or reboot) for this to take effect"
    NEEDS_RELOGIN=true
fi

# Create a customized service file
echo ""
echo "📝 Creating customized service file..."
SERVICE_FILE=$(mktemp)
sed "s|User=pi|User=$CURRENT_USER|g" weather_bot.service > "$SERVICE_FILE"
sed -i "s|/home/pi/MCWB|$INSTALL_DIR|g" "$SERVICE_FILE"

# Update Python path if using venv
if [ "$USE_VENV" = true ]; then
    echo "   Using virtual environment Python: $PYTHON_PATH"
    sed -i "s|/usr/bin/python3|$PYTHON_PATH|g" "$SERVICE_FILE"
fi

echo "📄 Service file contents:"
echo "----------------------------------------"
cat "$SERVICE_FILE"
echo "----------------------------------------"
echo ""

# Ask for confirmation
read -r -p "Do you want to install this service? (y/n) " -n 1
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Installation cancelled"
    rm "$SERVICE_FILE"
    exit 1
fi

# Install the service
echo ""
echo "🔧 Installing systemd service..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/weather_bot.service
rm "$SERVICE_FILE"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service
echo "⚡ Enabling service to start on boot..."
sudo systemctl enable weather_bot

# Ask if user wants to start now
echo ""
read -r -p "Do you want to start the service now? (y/n) " -n 1
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting weather_bot service..."
    sudo systemctl start weather_bot
    
    # Wait a moment for service to start
    sleep 2
    
    # Check status
    echo ""
    echo "📊 Service Status:"
    echo "----------------------------------------"
    sudo systemctl status weather_bot --no-pager
    echo "----------------------------------------"
    echo ""
    
    if sudo systemctl is-active --quiet weather_bot; then
        echo "✅ Service is running!"
    else
        echo "⚠️  Service may have failed to start. Check logs with:"
        echo "   sudo journalctl -u weather_bot -n 50"
    fi
else
    echo "⏸️  Service not started. Start it later with:"
    echo "   sudo systemctl start weather_bot"
fi

echo ""
echo "================================================"
echo "✅ Installation Complete!"
echo "================================================"
echo ""
echo "📚 Useful Commands:"
echo "   Start service:   sudo systemctl start weather_bot"
echo "   Stop service:    sudo systemctl stop weather_bot"
echo "   Restart service: sudo systemctl restart weather_bot"
echo "   Check status:    sudo systemctl status weather_bot"
echo "   View logs:       sudo journalctl -u weather_bot -f"
echo "   Disable service: sudo systemctl disable weather_bot"
echo ""

if [ "$NEEDS_RELOGIN" = true ]; then
    echo "⚠️  IMPORTANT: You were added to the 'dialout' group."
    echo "   Please log out and log back in (or reboot) for USB access to work."
    echo ""
fi

echo "📖 For more information, see RASPBERRY_PI_SETUP.md"
echo ""
