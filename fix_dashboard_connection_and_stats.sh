#!/bin/bash
# Comprehensive fix script for dashboard connection and stats display issues
# Specifically targets: "Cannot connect to dashboard locally" and "stats not displaying"

echo "========================================================================"
echo "MCWB Dashboard Connection & Stats Fix Script"
echo "========================================================================"
echo ""
echo "This script will diagnose and fix:"
echo "  1. Dashboard connectivity issues (cannot connect locally)"
echo "  2. Stats not displaying on live stats page"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get current IP
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "System IP: ${LOCAL_IP}"
echo "Dashboard should be at: http://${LOCAL_IP}:5000"
echo ""

# Step 1: Check if service is installed
echo "========================================================================"
echo "STEP 1: Checking Dashboard Service Status"
echo "========================================================================"
echo ""

if ! systemctl list-unit-files | grep -q "mcwb-dashboard.service"; then
    echo -e "${RED}✗ Dashboard service is NOT installed${NC}"
    echo ""
    echo "Installing dashboard service..."
    cd ~/MCWB
    ./install_dashboard_service.sh
    echo ""
fi

# Step 2: Check if service is running
echo "Checking if service is running..."
if sudo systemctl is-active --quiet mcwb-dashboard; then
    echo -e "${GREEN}✓ Service is running${NC}"
else
    echo -e "${RED}✗ Service is NOT running${NC}"
    echo ""
    echo "Starting service..."
    sudo systemctl start mcwb-dashboard
    sleep 3
    
    if sudo systemctl is-active --quiet mcwb-dashboard; then
        echo -e "${GREEN}✓ Service started${NC}"
    else
        echo -e "${RED}✗ Service failed to start${NC}"
        echo ""
        echo "Checking logs for errors..."
        echo "----------------------------------------"
        sudo journalctl -u mcwb-dashboard -n 30 --no-pager
        echo "----------------------------------------"
        echo ""
        echo "Common issues:"
        echo "  1. Missing dependencies: pip3 install -r ~/MCWB/requirements.txt"
        echo "  2. Wrong Python path in service file"
        echo "  3. Permission issues"
        exit 1
    fi
fi
echo ""

# Step 3: Test local connectivity
echo "========================================================================"
echo "STEP 2: Testing Dashboard Connectivity"
echo "========================================================================"
echo ""

echo "Testing localhost connection..."
if command -v curl >/dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Dashboard responds on localhost (HTTP 200)${NC}"
    else
        echo -e "${RED}✗ Dashboard NOT responding (HTTP $HTTP_CODE)${NC}"
        echo ""
        echo "Possible causes:"
        echo "  1. Service crashed after starting"
        echo "  2. Port 5000 is in use by another process"
        echo "  3. Dashboard code has errors"
        echo ""
        
        # Check if port is in use
        echo "Checking if port 5000 is in use..."
        PORT_CHECK=$(sudo netstat -tlnp 2>/dev/null | grep ":5000 " || sudo ss -tlnp 2>/dev/null | grep ":5000 " || echo "")
        if [ -n "$PORT_CHECK" ]; then
            echo "Port 5000 status:"
            echo "$PORT_CHECK"
            echo ""
            
            # Check if it's our service or something else
            if echo "$PORT_CHECK" | grep -q "python"; then
                echo "Port 5000 is used by Python (likely the dashboard)"
                echo "But it's not responding. Restarting service..."
                sudo systemctl restart mcwb-dashboard
                sleep 5
                HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null || echo "000")
                if [ "$HTTP_CODE" = "200" ]; then
                    echo -e "${GREEN}✓ Dashboard now responding after restart${NC}"
                else
                    echo -e "${RED}✗ Still not responding. Check logs:${NC}"
                    echo "  sudo journalctl -u mcwb-dashboard -f"
                    exit 1
                fi
            else
                echo -e "${RED}✗ Port 5000 is used by a different process!${NC}"
                echo "Fix: Kill the process or use a different port"
                exit 1
            fi
        else
            echo "Port 5000 is not in use - service may not be listening"
            echo "Checking service status..."
            sudo systemctl status mcwb-dashboard --no-pager
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠ curl not available, skipping connectivity test${NC}"
    echo "Install curl: sudo apt-get install -y curl"
fi
echo ""

# Step 4: Test network connectivity
echo "Testing network connectivity..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${LOCAL_IP}:5000" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Dashboard accessible on network${NC}"
else
    echo -e "${RED}✗ Dashboard NOT accessible from network (HTTP $HTTP_CODE)${NC}"
    echo ""
    echo "Checking firewall..."
    
    if command -v ufw >/dev/null 2>&1; then
        UFW_STATUS=$(sudo ufw status 2>/dev/null || echo "inactive")
        if echo "$UFW_STATUS" | grep -q "Status: active"; then
            echo "Firewall is active. Checking port 5000..."
            if echo "$UFW_STATUS" | grep -q "5000"; then
                echo -e "${GREEN}✓ Port 5000 is allowed in firewall${NC}"
            else
                echo -e "${YELLOW}⚠ Port 5000 is NOT allowed in firewall${NC}"
                echo ""
                read -r -p "Allow port 5000 in firewall? [Y/n] " -n 1
                echo ""
                if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
                    sudo ufw allow 5000/tcp
                    echo -e "${GREEN}✓ Port 5000 allowed${NC}"
                fi
            fi
        else
            echo "Firewall is inactive"
        fi
    fi
fi
echo ""

# Step 5: Check and fix stats file
echo "========================================================================"
echo "STEP 3: Checking Stats Tracking"
echo "========================================================================"
echo ""

STATS_FILE="$HOME/MCWB/logs/stats.json"
CHANNELS_FILE="$HOME/MCWB/logs/channels.json"

echo "Checking stats file: $STATS_FILE"
if [ -f "$STATS_FILE" ]; then
    echo -e "${GREEN}✓ Stats file exists${NC}"
    
    # Check if file is valid JSON
    if python3 -c "import json; json.load(open('$STATS_FILE'))" 2>/dev/null; then
        echo -e "${GREEN}✓ Stats file is valid JSON${NC}"
        
        # Show current stats
        echo ""
        echo "Current stats:"
        python3 -c "
import json
with open('$STATS_FILE') as f:
    stats = json.load(f)
    print(f\"  Total requests: {stats.get('total_requests', 0)}\")
    print(f\"  Total errors: {stats.get('total_errors', 0)}\")
    print(f\"  Last updated: {stats.get('last_updated', 'Never')}\")
"
    else
        echo -e "${RED}✗ Stats file is corrupted (invalid JSON)${NC}"
        echo "Backing up and recreating..."
        mv "$STATS_FILE" "${STATS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$(dirname "$STATS_FILE")"
        echo '{"total_requests":0,"total_errors":0,"locations":{},"hourly_requests":{},"daily_requests":{},"error_types":{},"last_updated":null,"recent_users":[]}' > "$STATS_FILE"
        echo -e "${GREEN}✓ Stats file recreated${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Stats file does not exist${NC}"
    echo "Creating stats file..."
    mkdir -p "$(dirname "$STATS_FILE")"
    echo '{"total_requests":0,"total_errors":0,"locations":{},"hourly_requests":{},"daily_requests":{},"error_types":{},"last_updated":null,"recent_users":[]}' > "$STATS_FILE"
    echo -e "${GREEN}✓ Stats file created${NC}"
fi
echo ""

echo "Checking channels file: $CHANNELS_FILE"
if [ -f "$CHANNELS_FILE" ]; then
    echo -e "${GREEN}✓ Channels file exists${NC}"
    
    # Check if file is valid JSON
    if python3 -c "import json; json.load(open('$CHANNELS_FILE'))" 2>/dev/null; then
        echo -e "${GREEN}✓ Channels file is valid JSON${NC}"
    else
        echo -e "${RED}✗ Channels file is corrupted${NC}"
        echo "Backing up and recreating..."
        mv "$CHANNELS_FILE" "${CHANNELS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        echo '{"channels":[],"last_updated":"'$(date -Iseconds)'"}' > "$CHANNELS_FILE"
        echo -e "${GREEN}✓ Channels file recreated${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Channels file does not exist${NC}"
    echo "Creating channels file..."
    mkdir -p "$(dirname "$CHANNELS_FILE")"
    echo '{"channels":[],"last_updated":"'$(date -Iseconds)'"}' > "$CHANNELS_FILE"
    echo -e "${GREEN}✓ Channels file created${NC}"
fi
echo ""

# Check file permissions
echo "Checking file permissions..."
CURRENT_USER=$(whoami)
if [ -w "$STATS_FILE" ] && [ -w "$CHANNELS_FILE" ]; then
    echo -e "${GREEN}✓ Files are writable${NC}"
else
    echo -e "${RED}✗ Permission issues detected${NC}"
    echo "Fixing permissions..."
    sudo chown "$CURRENT_USER:$CURRENT_USER" "$STATS_FILE" "$CHANNELS_FILE" 2>/dev/null || true
    chmod 644 "$STATS_FILE" "$CHANNELS_FILE" 2>/dev/null || true
    echo -e "${GREEN}✓ Permissions fixed${NC}"
fi
echo ""

# Step 6: Restart service to apply fixes
echo "========================================================================"
echo "STEP 4: Applying Fixes"
echo "========================================================================"
echo ""

echo "Restarting dashboard service..."
sudo systemctl restart mcwb-dashboard
sleep 5

if sudo systemctl is-active --quiet mcwb-dashboard; then
    echo -e "${GREEN}✓ Service restarted successfully${NC}"
else
    echo -e "${RED}✗ Service failed to restart${NC}"
    echo "Check logs: sudo journalctl -u mcwb-dashboard -f"
    exit 1
fi
echo ""

# Step 7: Final connectivity test
echo "========================================================================"
echo "STEP 5: Final Verification"
echo "========================================================================"
echo ""

sleep 3
echo "Testing dashboard connectivity..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓✓✓ Dashboard is working!${NC}"
    echo ""
    echo "========================================================================"
    echo -e "${GREEN}SUCCESS: Dashboard is now accessible${NC}"
    echo "========================================================================"
    echo ""
    echo "🌐 Dashboard URLs:"
    echo "   • Local:   http://localhost:5000"
    echo "   • Network: http://${LOCAL_IP}:5000"
    echo ""
    echo "📊 Stats API endpoint:"
    echo "   http://${LOCAL_IP}:5000/api/data"
    echo ""
    echo "🧪 Test the stats API:"
    echo "   curl http://localhost:5000/api/data"
    echo ""
    echo "💡 If stats show zeros, make sure the weather bot is running and"
    echo "   processing requests. Stats will update as people use the bot."
    echo ""
    echo "To check if weather bot is running:"
    echo "   sudo systemctl status weather-bot"
    echo ""
else
    echo -e "${RED}✗ Dashboard still not responding${NC}"
    echo ""
    echo "Manual diagnostics needed:"
    echo "  1. Check service logs: sudo journalctl -u mcwb-dashboard -f"
    echo "  2. Try running manually: cd ~/MCWB && python3 web_dashboard.py"
    echo "  3. Check Python dependencies: pip3 install -r ~/MCWB/requirements.txt"
    exit 1
fi
