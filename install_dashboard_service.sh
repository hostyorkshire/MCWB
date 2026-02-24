#!/bin/bash
# Installation script for MCWB Web Dashboard systemd service
# This script sets up the web dashboard to run automatically on boot

set -e  # Exit on error

echo "================================================"
echo "MCWB - Web Dashboard Service Installer"
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
if [ ! -f "web_dashboard.py" ]; then
    echo "❌ Error: web_dashboard.py not found in current directory"
    echo "   Please run this script from the MCWB directory"
    exit 1
fi

if [ ! -f "mcwb-dashboard.service" ]; then
    echo "❌ Error: mcwb-dashboard.service not found in current directory"
    exit 1
fi

# Check if Python dependencies are installed
echo "🔍 Checking Python dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Warning: Flask not installed"
    echo "   Installing dependencies..."
    pip3 install -r requirements.txt
else
    echo "✅ Python dependencies OK"
fi

# Create a customized service file
echo ""
echo "📝 Creating customized service file..."
SERVICE_FILE=$(mktemp)
sed "s|User=pi|User=$CURRENT_USER|g" mcwb-dashboard.service > $SERVICE_FILE
sed -i "s|/home/pi/MCWB|$INSTALL_DIR|g" $SERVICE_FILE

echo "📄 Service file contents:"
echo "----------------------------------------"
cat $SERVICE_FILE
echo "----------------------------------------"
echo ""

# Ask for confirmation
read -p "Do you want to install this service? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Installation cancelled"
    rm $SERVICE_FILE
    exit 1
fi

# Install the service
echo ""
echo "🔧 Installing systemd service..."
sudo cp $SERVICE_FILE /etc/systemd/system/mcwb-dashboard.service
rm $SERVICE_FILE

# Reload systemd
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service
echo "⚡ Enabling service to start on boot..."
sudo systemctl enable mcwb-dashboard

# Ask if user wants to start now
echo ""
read -p "Do you want to start the service now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting mcwb-dashboard service..."
    sudo systemctl start mcwb-dashboard
    
    # Wait a moment for service to start
    sleep 2
    
    # Check status
    echo ""
    echo "📊 Service Status:"
    echo "----------------------------------------"
    sudo systemctl status mcwb-dashboard --no-pager
    echo "----------------------------------------"
    echo ""
    
    if sudo systemctl is-active --quiet mcwb-dashboard; then
        echo "✅ Service is running!"
        echo ""
        echo "🌐 Web Dashboard Access:"
        echo "   Local:   http://localhost:5000"
        echo "   Network: http://$(hostname -I | awk '{print $1}'):5000"
        echo ""
    else
        echo "⚠️  Service may have failed to start. Check logs with:"
        echo "   sudo journalctl -u mcwb-dashboard -n 50"
    fi
else
    echo "⏸️  Service not started. Start it later with:"
    echo "   sudo systemctl start mcwb-dashboard"
    echo ""
    echo "🌐 When started, access the dashboard at:"
    echo "   Local:   http://localhost:5000"
    echo "   Network: http://$(hostname -I | awk '{print $1}'):5000"
fi

echo ""
echo "================================================"
echo "✅ Installation Complete!"
echo "================================================"
echo ""
echo "📚 Useful Commands:"
echo "   Start service:   sudo systemctl start mcwb-dashboard"
echo "   Stop service:    sudo systemctl stop mcwb-dashboard"
echo "   Restart service: sudo systemctl restart mcwb-dashboard"
echo "   Check status:    sudo systemctl status mcwb-dashboard"
echo "   View logs:       sudo journalctl -u mcwb-dashboard -f"
echo "   Disable service: sudo systemctl disable mcwb-dashboard"
echo ""
echo "📖 For more information, see WEB_DASHBOARD.md"
echo ""
