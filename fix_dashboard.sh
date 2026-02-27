#!/bin/bash
# Quick fix script for dashboard that was working before but stopped
# This script attempts to restore dashboard functionality quickly

echo "========================================================================"
echo "MCWB Dashboard Quick Fix"
echo "========================================================================"
echo ""
echo "This script will attempt to restore your dashboard that was working before."
echo ""

# Get current IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo "Your current IP: ${LOCAL_IP}"
echo "Expected dashboard URL: http://${LOCAL_IP}:5000"
echo ""

# Quick Check: Is service running?
echo "Checking if dashboard service is running..."
if sudo systemctl is-active --quiet mcwb-dashboard 2>/dev/null; then
    echo "✓ Service is already running"
    echo ""
    echo "Testing if it's responding..."
    sleep 2
    if command -v curl >/dev/null 2>&1; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null || echo "000")
        if [ "$HTTP_CODE" = "200" ]; then
            echo "✓ Dashboard is responding correctly!"
            echo ""
            echo "🌐 Dashboard URL: http://${LOCAL_IP}:5000"
            echo ""
            echo "If you still can't access it:"
            echo "  1. Check firewall: sudo ufw status"
            echo "  2. Run full diagnostics: ./diagnose_dashboard.sh"
            exit 0
        else
            echo "✗ Service is running but not responding (HTTP $HTTP_CODE)"
            echo "  Attempting restart..."
            sudo systemctl restart mcwb-dashboard
            sleep 5
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null || echo "000")
            if [ "$HTTP_CODE" = "200" ]; then
                echo "✓ Dashboard restored after restart!"
                echo ""
                echo "🌐 Dashboard URL: http://${LOCAL_IP}:5000"
                exit 0
            else
                echo "✗ Still not responding. Running full diagnostics..."
                ./diagnose_dashboard.sh
                exit 1
            fi
        fi
    fi
else
    echo "✗ Service is NOT running"
    echo ""
    
    # Check if service exists
    if systemctl list-unit-files | grep -q "mcwb-dashboard.service"; then
        echo "Service is installed. Attempting to start..."
        sudo systemctl start mcwb-dashboard
        sleep 5
        
        if sudo systemctl is-active --quiet mcwb-dashboard; then
            echo "✓ Service started successfully!"
            echo ""
            
            # Test if responding
            if command -v curl >/dev/null 2>&1; then
                sleep 2
                HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null || echo "000")
                if [ "$HTTP_CODE" = "200" ]; then
                    echo "✓ Dashboard is now responding!"
                    echo ""
                    echo "🌐 Dashboard URL: http://${LOCAL_IP}:5000"
                    echo ""
                    echo "💡 To prevent this from happening again:"
                    echo "   Make sure the service is enabled: sudo systemctl enable mcwb-dashboard"
                    exit 0
                fi
            fi
        else
            echo "✗ Service failed to start"
            echo ""
            echo "Checking service logs for errors..."
            echo "========================================="
            sudo journalctl -u mcwb-dashboard -n 30 --no-pager
            echo "========================================="
            echo ""
            
            # Check for common issues
            if sudo journalctl -u mcwb-dashboard -n 30 | grep -qi "ModuleNotFoundError\|No module named"; then
                echo "❌ ISSUE FOUND: Missing Python dependencies"
                echo ""
                echo "FIX: Install dependencies and restart:"
                read -r -p "Install dependencies now? [Y/n] "
                echo ""
                if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
                    # Get script directory to find requirements.txt
                    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
                    cd "$SCRIPT_DIR" || exit 1
                    
                    # Check if venv exists, if not create it
                    if [ ! -d "venv" ]; then
                        echo "Creating virtual environment..."
                        if ! python3 -m venv venv; then
                            echo "✗ Failed to create virtual environment"
                            echo "  You may need to install python3-venv:"
                            echo "  sudo apt-get install python3-venv"
                            exit 1
                        fi
                    fi
                    
                    # Install dependencies in venv
                    echo "Installing dependencies in virtual environment..."
                    if ! ./venv/bin/pip install -r requirements.txt; then
                        echo "✗ Failed to install dependencies"
                        exit 1
                    fi
                    echo "✓ Dependencies installed"
                    echo ""
                    echo "Restarting service..."
                    sudo systemctl restart mcwb-dashboard
                    sleep 5
                    
                    if sudo systemctl is-active --quiet mcwb-dashboard; then
                        echo "✓ Service started successfully after fixing dependencies!"
                        echo ""
                        echo "🌐 Dashboard URL: http://${LOCAL_IP}:5000"
                        exit 0
                    else
                        echo "✗ Service still failed. Run: ./diagnose_dashboard.sh"
                        exit 1
                    fi
                fi
            elif sudo journalctl -u mcwb-dashboard -n 30 | grep -qi "Permission denied\|code=217"; then
                echo "❌ ISSUE FOUND: Permission/user mismatch"
                echo ""
                echo "FIX: Reinstall the service with correct paths:"
                echo "  cd ~/MCWB && ./install_dashboard_service.sh"
                exit 1
            elif sudo journalctl -u mcwb-dashboard -n 30 | grep -qi "Address already in use"; then
                echo "❌ ISSUE FOUND: Port 5000 is already in use"
                echo ""
                echo "Finding what's using port 5000..."
                sudo lsof -i :5000 2>/dev/null || sudo netstat -tlnp | grep :5000
                echo ""
                echo "You may need to stop the other process or use a different port"
                exit 1
            else
                echo "Could not identify specific issue."
                echo "Run full diagnostics: ./diagnose_dashboard.sh"
                exit 1
            fi
        fi
    else
        echo "✗ Service is not installed!"
        echo ""
        echo "FIX: Install the dashboard service:"
        echo "  cd ~/MCWB && ./install_dashboard_service.sh"
        exit 1
    fi
fi
