#!/bin/bash
# Diagnostic script to identify and fix dashboard connectivity issues
# Run this if you cannot access the dashboard at http://192.168.1.109:5000

# Note: No 'set -e' here - we want to continue through all checks even if some fail

echo "========================================================================"
echo "MCWB Dashboard Connectivity Diagnostic"
echo "========================================================================"
echo ""
echo "This script will check why you cannot access the dashboard and attempt"
echo "to fix common issues."
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES_FOUND=0
FIXES_APPLIED=0

# Get current IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo "Current system IP: ${LOCAL_IP}"
echo "Expected dashboard URL: http://${LOCAL_IP}:5000"
echo ""
echo "========================================================================"
echo "Running Diagnostics..."
echo "========================================================================"
echo ""

# Check 1: Is the service installed?
echo "[1/8] Checking if mcwb-dashboard service is installed..."
if systemctl list-unit-files | grep -q "mcwb-dashboard.service"; then
    echo -e "${GREEN}✓${NC} Service is installed"
else
    echo -e "${RED}✗${NC} Service is NOT installed"
    echo ""
    echo "FIX: Install the service by running:"
    echo "  cd ~/MCWB && ./install_dashboard_service.sh"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
    exit 1
fi
echo ""

# Check 2: Is the service enabled?
echo "[2/8] Checking if service is enabled to start on boot..."
if sudo systemctl is-enabled --quiet mcwb-dashboard 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Service is enabled"
else
    echo -e "${YELLOW}⚠${NC} Service is NOT enabled (won't start on boot)"
    read -r -p "Enable service to start on boot? [Y/n] " -n 1
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        sudo systemctl enable mcwb-dashboard
        echo -e "${GREEN}✓${NC} Service enabled"
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
    fi
fi
echo ""

# Check 3: Is the service running?
echo "[3/8] Checking if service is running..."
if sudo systemctl is-active --quiet mcwb-dashboard; then
    echo -e "${GREEN}✓${NC} Service is running"
else
    echo -e "${RED}✗${NC} Service is NOT running"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
    
    # Try to start it
    echo ""
    echo "Attempting to start the service..."
    sudo systemctl start mcwb-dashboard
    sleep 3
    
    if sudo systemctl is-active --quiet mcwb-dashboard; then
        echo -e "${GREEN}✓${NC} Service started successfully"
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
    else
        echo -e "${RED}✗${NC} Service failed to start"
        echo ""
        echo "Recent service logs:"
        echo "----------------------------------------"
        sudo journalctl -u mcwb-dashboard -n 20 --no-pager
        echo "----------------------------------------"
        echo ""
        echo "Common causes:"
        echo "  1. Dependencies not installed (see above logs for 'ModuleNotFoundError')"
        echo "  2. Path/user mismatch in service file"
        echo "  3. Python version incompatibility"
        echo ""
        echo "FIX: Reinstall the service:"
        echo "  cd ~/MCWB && ./install_dashboard_service.sh"
        exit 1
    fi
fi
echo ""

# Check 4: Can we connect locally?
echo "[4/8] Testing local connectivity (localhost:5000)..."
sleep 2  # Give Flask time to fully initialize
if command -v curl >/dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓${NC} Dashboard responds on localhost (HTTP 200)"
    else
        echo -e "${RED}✗${NC} Dashboard not responding on localhost (HTTP $HTTP_CODE)"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        echo ""
        echo "The service is running but not responding. Check logs:"
        echo "  sudo journalctl -u mcwb-dashboard -n 50"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC} curl not installed, skipping local connectivity test"
fi
echo ""

# Check 5: Is the dashboard listening on all interfaces?
echo "[5/8] Checking if dashboard is accessible on network..."
if command -v netstat >/dev/null 2>&1; then
    if sudo netstat -tlnp 2>/dev/null | grep ":5000" | grep -q "0.0.0.0:5000"; then
        echo -e "${GREEN}✓${NC} Dashboard is listening on all interfaces (0.0.0.0:5000)"
    elif sudo netstat -tlnp 2>/dev/null | grep ":5000" | grep -q "127.0.0.1:5000"; then
        echo -e "${RED}✗${NC} Dashboard is only listening on localhost (127.0.0.1:5000)"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        echo ""
        echo "FIX: Update service to bind to 0.0.0.0"
        echo "  sudo nano /etc/systemd/system/mcwb-dashboard.service"
        echo "  Change: --host 127.0.0.1  to  --host 0.0.0.0"
        echo "  Then: sudo systemctl daemon-reload && sudo systemctl restart mcwb-dashboard"
        exit 1
    else
        echo -e "${YELLOW}⚠${NC} Could not determine listening address"
    fi
elif command -v ss >/dev/null 2>&1; then
    if sudo ss -tlnp 2>/dev/null | grep ":5000" | grep -q "0.0.0.0:5000"; then
        echo -e "${GREEN}✓${NC} Dashboard is listening on all interfaces (0.0.0.0:5000)"
    elif sudo ss -tlnp 2>/dev/null | grep ":5000" | grep -q "127.0.0.1:5000"; then
        echo -e "${RED}✗${NC} Dashboard is only listening on localhost (127.0.0.1:5000)"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        echo ""
        echo "FIX: Update service to bind to 0.0.0.0"
        echo "  sudo nano /etc/systemd/system/mcwb-dashboard.service"
        echo "  Change: --host 127.0.0.1  to  --host 0.0.0.0"
        echo "  Then: sudo systemctl daemon-reload && sudo systemctl restart mcwb-dashboard"
        exit 1
    else
        echo -e "${YELLOW}⚠${NC} Could not determine listening address"
    fi
else
    echo -e "${YELLOW}⚠${NC} Neither netstat nor ss available, skipping"
fi
echo ""

# Check 6: Is the firewall blocking?
echo "[6/8] Checking firewall configuration..."
if command -v ufw >/dev/null 2>&1; then
    if sudo ufw status 2>/dev/null | grep -q "Status: active"; then
        if sudo ufw status | grep -q "5000"; then
            echo -e "${GREEN}✓${NC} Firewall allows port 5000"
        else
            echo -e "${RED}✗${NC} Firewall is blocking port 5000"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            echo ""
            read -r -p "Allow port 5000 through firewall? [Y/n] " -n 1
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
                sudo ufw allow 5000/tcp
                echo -e "${GREEN}✓${NC} Port 5000 allowed"
                FIXES_APPLIED=$((FIXES_APPLIED + 1))
            fi
        fi
    else
        echo -e "${GREEN}✓${NC} UFW firewall is not active"
    fi
else
    echo -e "${GREEN}✓${NC} UFW firewall not installed"
fi
echo ""

# Check 7: Are Python dependencies installed?
echo "[7/8] Checking Python dependencies..."
if python3 -c "import flask, flask_cors" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Required Python packages are installed"
else
    echo -e "${RED}✗${NC} Required Python packages are missing"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
    echo ""
    read -r -p "Install Python dependencies? [Y/n] "
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        # Get script directory to find requirements.txt
        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        cd "$SCRIPT_DIR" || exit 1
        
        # Check if venv exists, if not create it
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            if ! python3 -m venv venv; then
                echo -e "${RED}✗${NC} Failed to create virtual environment"
                echo "   You may need to install python3-venv:"
                echo "   sudo apt-get install python3-venv"
                exit 1
            fi
        fi
        
        # Install dependencies in venv
        echo "Installing dependencies in virtual environment..."
        if ! ./venv/bin/pip install -r requirements.txt; then
            echo -e "${RED}✗${NC} Failed to install dependencies"
            exit 1
        fi
        echo -e "${GREEN}✓${NC} Dependencies installed"
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
        echo ""
        echo "Restarting service to use new dependencies..."
        sudo systemctl restart mcwb-dashboard
        sleep 3
    fi
fi
echo ""

# Check 8: Final connectivity test from network perspective
echo "[8/8] Final connectivity test..."
sleep 2
if command -v curl >/dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://${LOCAL_IP}:5000 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓${NC} Dashboard is accessible from network (HTTP 200)"
    else
        echo -e "${YELLOW}⚠${NC} Could not confirm network access (HTTP $HTTP_CODE)"
        echo "   This might be a routing/network issue"
    fi
fi
echo ""

echo "========================================================================"
echo "Diagnostic Summary"
echo "========================================================================"
echo ""
echo "Issues found: $ISSUES_FOUND"
echo "Fixes applied: $FIXES_APPLIED"
echo ""

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "🌐 Your dashboard should be accessible at:"
    echo "   http://${LOCAL_IP}:5000"
    echo ""
    echo "If you still cannot access it from your browser:"
    echo "  1. Make sure you're using HTTP (not HTTPS)"
    echo "  2. Check that both devices are on the same network"
    echo "  3. Try accessing from the Raspberry Pi itself first:"
    echo "     Open a browser on the Pi and go to http://localhost:5000"
    echo "  4. Check for any network-level restrictions (VLANs, client isolation)"
else
    echo -e "${YELLOW}⚠️  Some issues remain${NC}"
    echo ""
    echo "Please address the issues mentioned above and run this script again."
fi
echo ""
echo "For more help, see:"
echo "  - CONNECTION_GUIDE.md"
echo "  - DASHBOARD_CONNECTIVITY_TROUBLESHOOTING.md"
echo ""
