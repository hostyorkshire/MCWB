#!/bin/bash
# Master fix script for SSH and Dashboard access issues
# This script handles both "cannot SSH" and "cannot see dashboard" problems

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "MCWB - Master Access Issue Fix Script"
echo "========================================================================"
echo ""
echo -e "${YELLOW}This script fixes both SSH and Dashboard access issues${NC}"
echo ""

# Get current IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo "📍 Current System Information:"
echo "   IP Address: ${LOCAL_IP}"
echo "   Username: $(whoami)"
echo "   Expected SSH: ssh $(whoami)@${LOCAL_IP}"
echo "   Expected Dashboard: http://${LOCAL_IP}:5000"
echo ""
echo "========================================================================"
echo "Diagnostic Summary"
echo "========================================================================"
echo ""

SSH_ISSUE=false
DASHBOARD_ISSUE=false

# ============================================================================
# PART 1: Check SSH Access
# ============================================================================

echo "🔍 [1/2] Checking SSH Access..."
echo ""

# Check if UFW is installed and active
if command -v ufw >/dev/null 2>&1; then
    if sudo ufw status | grep -q "Status: active"; then
        # UFW is active, check if SSH is allowed
        if sudo ufw status | grep -q "22.*ALLOW"; then
            echo -e "${GREEN}✓${NC} SSH (port 22) is allowed in firewall"
        else
            echo -e "${RED}✗${NC} SSH (port 22) is BLOCKED by firewall"
            SSH_ISSUE=true
        fi
    else
        echo -e "${GREEN}✓${NC} Firewall is inactive (SSH not blocked)"
    fi
else
    echo -e "${BLUE}ℹ${NC} UFW firewall not installed"
fi

# Check SSH service status
if sudo systemctl is-active --quiet ssh; then
    echo -e "${GREEN}✓${NC} SSH service is running"
else
    echo -e "${RED}✗${NC} SSH service is NOT running"
    SSH_ISSUE=true
fi

echo ""

# ============================================================================
# PART 2: Check Dashboard Access
# ============================================================================

echo "🔍 [2/2] Checking Dashboard Access..."
echo ""

# Check if service is installed
if systemctl list-unit-files | grep -q "mcwb-dashboard.service"; then
    echo -e "${GREEN}✓${NC} Dashboard service is installed"
    
    # Check if service is enabled
    if sudo systemctl is-enabled --quiet mcwb-dashboard 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Dashboard service is enabled (starts on boot)"
    else
        echo -e "${YELLOW}⚠${NC} Dashboard service is NOT enabled (won't start on boot)"
    fi
    
    # Check if service is running
    if sudo systemctl is-active --quiet mcwb-dashboard; then
        echo -e "${GREEN}✓${NC} Dashboard service is running"
        
        # Test if responding
        if command -v curl >/dev/null 2>&1; then
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null || echo "000")
            if [ "$HTTP_CODE" = "200" ]; then
                echo -e "${GREEN}✓${NC} Dashboard is responding correctly"
            else
                echo -e "${RED}✗${NC} Dashboard service running but not responding (HTTP $HTTP_CODE)"
                DASHBOARD_ISSUE=true
            fi
        fi
    else
        echo -e "${RED}✗${NC} Dashboard service is NOT running"
        DASHBOARD_ISSUE=true
    fi
    
    # Check firewall for dashboard port
    if command -v ufw >/dev/null 2>&1; then
        if sudo ufw status | grep -q "Status: active"; then
            if sudo ufw status | grep -q "5000.*ALLOW"; then
                echo -e "${GREEN}✓${NC} Dashboard port 5000 is allowed in firewall"
            else
                echo -e "${YELLOW}⚠${NC} Dashboard port 5000 is not explicitly allowed"
                echo "   (This may prevent access from other devices)"
            fi
        fi
    fi
else
    echo -e "${RED}✗${NC} Dashboard service is NOT installed"
    DASHBOARD_ISSUE=true
fi

echo ""
echo "========================================================================"
echo "Summary"
echo "========================================================================"
echo ""

if [ "$SSH_ISSUE" = false ] && [ "$DASHBOARD_ISSUE" = false ]; then
    echo -e "${GREEN}✅ No issues detected!${NC}"
    echo ""
    echo "Both SSH and Dashboard should be working:"
    echo "   SSH: ssh $(whoami)@${LOCAL_IP}"
    echo "   Dashboard: http://${LOCAL_IP}:5000"
    echo ""
    echo "If you still have issues, they may be network-related:"
    echo "   - Check if you're on the same network"
    echo "   - Check router settings"
    echo "   - Check device firewall settings"
    exit 0
fi

# ============================================================================
# PART 3: Offer to Fix Issues
# ============================================================================

if [ "$SSH_ISSUE" = true ]; then
    echo -e "${RED}❌ SSH Access Issue Detected${NC}"
fi

if [ "$DASHBOARD_ISSUE" = true ]; then
    echo -e "${RED}❌ Dashboard Access Issue Detected${NC}"
fi

echo ""
read -p "Would you like to attempt automatic fixes? [Y/n] " -n 1 -r REPLY
echo ""
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
    echo "No changes made. To fix manually:"
    if [ "$SSH_ISSUE" = true ]; then
        echo "   SSH: Run ./fix_ssh_access.sh"
    fi
    if [ "$DASHBOARD_ISSUE" = true ]; then
        echo "   Dashboard: Run ./fix_dashboard.sh"
    fi
    exit 0
fi

# ============================================================================
# PART 4: Apply Fixes
# ============================================================================

FIXES_APPLIED=0

echo "========================================================================"
echo "Applying Fixes"
echo "========================================================================"
echo ""

# Fix SSH issues
if [ "$SSH_ISSUE" = true ]; then
    echo "🔧 Fixing SSH Access..."
    echo ""
    
    # Check if SSH service is not running
    if ! sudo systemctl is-active --quiet ssh; then
        echo "   Starting SSH service..."
        sudo systemctl start ssh
        if sudo systemctl is-active --quiet ssh; then
            echo -e "   ${GREEN}✓${NC} SSH service started"
            FIXES_APPLIED=$((FIXES_APPLIED + 1))
        else
            echo -e "   ${RED}✗${NC} Failed to start SSH service"
        fi
    fi
    
    # Check if SSH is blocked by firewall
    if command -v ufw >/dev/null 2>&1; then
        if sudo ufw status | grep -q "Status: active"; then
            if ! sudo ufw status | grep -q "22.*ALLOW"; then
                echo "   Allowing SSH (port 22) through firewall..."
                sudo ufw allow 22/tcp
                sudo ufw reload
                echo -e "   ${GREEN}✓${NC} SSH port allowed in firewall"
                FIXES_APPLIED=$((FIXES_APPLIED + 1))
            fi
        fi
    fi
    
    echo ""
fi

# Fix Dashboard issues
if [ "$DASHBOARD_ISSUE" = true ]; then
    echo "🔧 Fixing Dashboard Access..."
    echo ""
    
    # Check if service is not installed
    if ! systemctl list-unit-files | grep -q "mcwb-dashboard.service"; then
        echo -e "   ${RED}✗${NC} Service not installed"
        echo "   To install, run: ./install_dashboard_service.sh"
        echo ""
    else
        # Service is installed but not running or not responding
        
        # Enable service if not enabled
        if ! sudo systemctl is-enabled --quiet mcwb-dashboard 2>/dev/null; then
            echo "   Enabling dashboard service..."
            sudo systemctl enable mcwb-dashboard
            echo -e "   ${GREEN}✓${NC} Service enabled"
            FIXES_APPLIED=$((FIXES_APPLIED + 1))
        fi
        
        # Start or restart service
        if ! sudo systemctl is-active --quiet mcwb-dashboard; then
            echo "   Starting dashboard service..."
            sudo systemctl start mcwb-dashboard
        else
            echo "   Restarting dashboard service..."
            sudo systemctl restart mcwb-dashboard
        fi
        
        sleep 3
        
        # Check if it's running now
        if sudo systemctl is-active --quiet mcwb-dashboard; then
            echo -e "   ${GREEN}✓${NC} Dashboard service is now running"
            FIXES_APPLIED=$((FIXES_APPLIED + 1))
            
            # Test if responding
            if command -v curl >/dev/null 2>&1; then
                sleep 2
                HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null || echo "000")
                if [ "$HTTP_CODE" = "200" ]; then
                    echo -e "   ${GREEN}✓${NC} Dashboard is responding correctly"
                else
                    echo -e "   ${RED}✗${NC} Dashboard still not responding (HTTP $HTTP_CODE)"
                    echo "   Check logs: sudo journalctl -u mcwb-dashboard -n 50"
                fi
            fi
        else
            echo -e "   ${RED}✗${NC} Dashboard service failed to start"
            echo ""
            echo "   Recent service logs:"
            echo "   ----------------------------------------"
            sudo journalctl -u mcwb-dashboard -n 20 --no-pager | sed 's/^/   /'
            echo "   ----------------------------------------"
            echo ""
            echo "   This may require manual intervention."
            echo "   Try: ./install_dashboard_service.sh"
        fi
        
        # Optionally allow dashboard port in firewall
        if command -v ufw >/dev/null 2>&1; then
            if sudo ufw status | grep -q "Status: active"; then
                if ! sudo ufw status | grep -q "5000.*ALLOW"; then
                    echo ""
                    read -p "   Allow dashboard port 5000 in firewall? [Y/n] " -n 1 -r ALLOW_REPLY
                    echo ""
                    if [[ $ALLOW_REPLY =~ ^[Yy]$ ]] || [[ -z $ALLOW_REPLY ]]; then
                        sudo ufw allow 5000/tcp
                        sudo ufw reload
                        echo -e "   ${GREEN}✓${NC} Dashboard port allowed in firewall"
                        FIXES_APPLIED=$((FIXES_APPLIED + 1))
                    fi
                fi
            fi
        fi
    fi
    
    echo ""
fi

# ============================================================================
# PART 5: Final Summary
# ============================================================================

echo "========================================================================"
echo "Fix Complete"
echo "========================================================================"
echo ""

if [ $FIXES_APPLIED -gt 0 ]; then
    echo -e "${GREEN}✅ Applied $FIXES_APPLIED fix(es)${NC}"
    echo ""
    echo "🎉 Your system should now be accessible:"
    echo ""
    echo "   SSH: ssh $(whoami)@${LOCAL_IP}"
    echo "   Dashboard: http://${LOCAL_IP}:5000"
    echo ""
    echo "💡 Tips:"
    echo "   - If SSH still doesn't work, check: sudo systemctl status ssh"
    echo "   - If dashboard still doesn't work, check: sudo systemctl status mcwb-dashboard"
    echo "   - View dashboard logs: sudo journalctl -u mcwb-dashboard -f"
else
    echo -e "${YELLOW}⚠${NC} No fixes were applied"
    echo ""
    echo "If you still have issues:"
    echo "   - For SSH: Run ./fix_ssh_access.sh for detailed diagnostics"
    echo "   - For Dashboard: Run ./diagnose_dashboard.sh for detailed diagnostics"
fi

echo ""
