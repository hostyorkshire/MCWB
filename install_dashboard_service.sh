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

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    # Not in a venv, check if one exists
    if [ -d "venv" ] && [ -f "venv/bin/python3" ]; then
        echo "📦 Virtual environment found at ./venv"
        echo "   Checking if dependencies are installed in venv..."
        if ./venv/bin/python3 -c "import flask; import flask_cors" 2>/dev/null; then
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
        if python3 -c "import flask; import flask_cors" 2>/dev/null; then
            echo "✅ Python dependencies OK (system-wide)"
            USE_VENV=false
            PYTHON_PATH="/usr/bin/python3"
        else
            echo "⚠️  Flask packages not installed"
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
    if python3 -c "import flask; import flask_cors" 2>/dev/null; then
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

# Create a customized service file
echo ""
echo "📝 Creating customized service file..."
SERVICE_FILE=$(mktemp)
sed "s|User=pi|User=$CURRENT_USER|g" mcwb-dashboard.service > "$SERVICE_FILE"
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
read -r -p "Do you want to install this service? [Y/n] " -n 1
echo ""
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "❌ Installation cancelled"
    rm "$SERVICE_FILE"
    exit 1
fi

# Install the service
echo ""
echo "🔧 Installing systemd service..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/mcwb-dashboard.service
rm "$SERVICE_FILE"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service
echo "⚡ Enabling service to start on boot..."
sudo systemctl enable mcwb-dashboard

# Configure firewall if UFW is installed
echo ""
echo "🔥 Checking firewall configuration..."
if command -v ufw >/dev/null 2>&1; then
    if sudo ufw status | grep -q "Status: active"; then
        echo "   UFW firewall is active"
        # Check if port 5000 is already allowed
        if sudo ufw status | grep -q "5000"; then
            echo "   ✅ Port 5000 already allowed"
        else
            echo "   ⚠️  Port 5000 not allowed in firewall"
            read -r -p "   Allow port 5000 through firewall? [Y/n] " -n 1
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
                sudo ufw allow 5000/tcp
                echo "   ✅ Port 5000 allowed through firewall"
            else
                echo "   ⚠️  Port 5000 NOT allowed - you may not be able to access the dashboard remotely"
            fi
        fi
    else
        echo "   ℹ️  UFW firewall is not active (no firewall config needed)"
    fi
else
    echo "   ℹ️  UFW not installed (no firewall config needed)"
fi

# Ask if user wants to start now
echo ""
read -r -p "Do you want to start the service now? [Y/n] " -n 1
echo ""
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
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
        
        # Get the IP address
        LOCAL_IP=$(hostname -I | awk '{print $1}')
        
        echo "🌐 Web Dashboard Access:"
        echo "   Local:   http://localhost:5000"
        echo "   Network: http://${LOCAL_IP}:5000"
        echo ""
        
        # Test connectivity (wait for Flask to fully initialize)
        echo "🔍 Testing connectivity..."
        # Wait 3 seconds for Flask application to fully initialize
        sleep 3
        
        # Check if curl is available
        if ! command -v curl >/dev/null 2>&1; then
            echo "   ℹ️  curl not available, skipping connectivity test"
            echo "   Try connecting manually: http://${LOCAL_IP}:5000"
        elif curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200"; then
            echo "   ✅ Dashboard is responding on http://localhost:5000"
            echo "   ✅ You should be able to connect from other devices at:"
            echo "      http://${LOCAL_IP}:5000"
        else
            echo "   ⚠️  Dashboard not responding yet (may still be starting up)"
            echo "   Wait a few seconds and try: curl http://localhost:5000"
        fi
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
