#!/bin/bash
# Fix SSH Access Script for MCWB
# This script helps restore SSH access when it's been blocked by firewall

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================"
echo "MCWB - SSH Access Troubleshooting & Fix"
echo "================================================"
echo ""
echo -e "${YELLOW}⚠️  This script helps fix SSH access issues${NC}"
echo ""

# Check if running with physical access (directly on the Pi)
echo "🔍 Checking environment..."
echo ""

# Check if UFW is installed
if ! command -v ufw >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  UFW (Uncomplicated Firewall) is not installed${NC}"
    echo ""
    echo "UFW is the recommended firewall tool for Ubuntu/Debian systems."
    echo ""
    echo "Would you like to install UFW now? (y/n)"
    read -p "> " -n 1 -r
    echo ""
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Installing UFW..."
        if sudo apt-get update && sudo apt-get install -y ufw; then
            echo ""
            echo -e "${GREEN}✅ UFW installed successfully${NC}"
            echo ""
            echo "🔧 Configuring UFW to allow SSH..."
            # Allow SSH before enabling to prevent lockout
            sudo ufw allow 22/tcp
            echo ""
            echo "Would you like to enable UFW now? (y/n)"
            read -p "> " -n 1 -r
            echo ""
            echo ""
            
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo ufw --force enable
                echo ""
                echo -e "${GREEN}✅ UFW enabled with SSH allowed${NC}"
                echo ""
                echo "📊 Firewall Status:"
                echo "----------------------------------------"
                sudo ufw status verbose
                echo "----------------------------------------"
                echo ""
            else
                echo "UFW installed but not enabled."
                echo "To enable later, run: sudo ufw enable"
                echo ""
            fi
            exit 0
        else
            echo ""
            echo -e "${RED}❌ Failed to install UFW${NC}"
            echo ""
            echo "You can try installing manually with:"
            echo "   sudo apt-get update"
            echo "   sudo apt-get install ufw"
            echo ""
        fi
    fi
    
    # Check for alternative firewall solutions
    echo "Checking for other firewall solutions..."
    echo ""
    
    if command -v iptables >/dev/null 2>&1; then
        echo -e "${BLUE}ℹ️  iptables is available${NC}"
        echo ""
        echo "Checking if SSH (port 22) is allowed in iptables..."
        if sudo iptables -L INPUT -n | grep -q "dpt:22"; then
            echo -e "${GREEN}✅ SSH appears to be allowed in iptables${NC}"
        else
            echo -e "${YELLOW}⚠️  SSH may not be explicitly allowed in iptables${NC}"
            echo ""
            echo "To allow SSH in iptables, run:"
            echo "   sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT"
            echo "   sudo iptables-save | sudo tee /etc/iptables/rules.v4"
        fi
        echo ""
    fi
    
    if command -v firewall-cmd >/dev/null 2>&1; then
        echo -e "${BLUE}ℹ️  firewalld is available${NC}"
        echo ""
        echo "To allow SSH in firewalld, run:"
        echo "   sudo firewall-cmd --permanent --add-service=ssh"
        echo "   sudo firewall-cmd --reload"
        echo ""
    fi
    
    echo "Other possible causes of SSH issues:"
    echo "  - SSH service not running (check with: sudo systemctl status ssh)"
    echo "  - Network configuration issue"
    echo "  - Wrong IP address"
    echo "  - Router port forwarding not configured"
    echo ""
    exit 0
fi

echo "📊 Firewall Status:"
echo "----------------------------------------"
sudo ufw status verbose
echo "----------------------------------------"
echo ""

# Check if UFW is active
if sudo ufw status | grep -q "Status: inactive"; then
    echo -e "${GREEN}✅ Firewall is inactive${NC}"
    echo "   SSH access issue is not firewall-related."
    echo ""
    exit 0
fi

# UFW is active, check if SSH is allowed
if sudo ufw status | grep -q "22.*ALLOW"; then
    echo -e "${GREEN}✅ SSH (port 22) is already allowed${NC}"
    echo "   Firewall is not blocking SSH."
    echo ""
    echo "Other possible causes:"
    echo "  - SSH service not running (check with: sudo systemctl status ssh)"
    echo "  - Network configuration issue"
    echo "  - Wrong IP address"
    echo ""
    exit 0
fi

# SSH is not allowed - this is the problem!
echo -e "${RED}❌ PROBLEM FOUND: SSH port 22 is NOT allowed in firewall${NC}"
echo ""
echo "This is why you cannot SSH into the Pi."
echo "ICMP (ping) works because it's not blocked, but SSH is blocked."
echo ""
echo "================================================"
echo "FIX OPTIONS"
echo "================================================"
echo ""
echo "Option 1: Allow SSH through firewall (RECOMMENDED)"
echo "   This will keep the firewall enabled but allow SSH."
echo ""
echo "Option 2: Disable firewall completely"
echo "   This will disable all firewall protection."
echo ""

echo "Would you like to fix this now? (y/n) " -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "No changes made."
    echo ""
    echo "To fix manually, run:"
    echo "   sudo ufw allow 22/tcp"
    echo "   sudo ufw reload"
    echo ""
    exit 0
fi

echo "Choose fix method:"
echo "  1) Allow SSH (port 22) - RECOMMENDED"
echo "  2) Disable firewall completely"
echo "  0) Cancel (no changes)"
echo ""
read -p "Enter choice (0, 1, or 2): " -n 1 choice
echo ""
echo ""

case $choice in
    1)
        echo "🔧 Allowing SSH (port 22) through firewall..."
        sudo ufw allow 22/tcp
        sudo ufw reload
        echo ""
        echo -e "${GREEN}✅ SSH access enabled!${NC}"
        echo ""
        echo "📊 New firewall status:"
        echo "----------------------------------------"
        sudo ufw status verbose
        echo "----------------------------------------"
        echo ""
        echo -e "${GREEN}✅ You should now be able to SSH into the Pi${NC}"
        ;;
    2)
        echo -e "${YELLOW}⚠️  Disabling firewall completely...${NC}"
        sudo ufw disable
        echo ""
        echo -e "${YELLOW}⚠️  Firewall disabled${NC}"
        echo "   SSH access should now work."
        echo ""
        echo -e "${RED}WARNING: Your Pi is now less protected.${NC}"
        echo "   Consider re-enabling the firewall with SSH allowed:"
        echo "   sudo ufw allow 22/tcp"
        echo "   sudo ufw enable"
        ;;
    0)
        echo "Cancelled. No changes made."
        echo ""
        echo "To fix manually, run:"
        echo "   sudo ufw allow 22/tcp"
        echo "   sudo ufw reload"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice. No changes made.${NC}"
        echo ""
        echo "To fix manually, run:"
        echo "   sudo ufw allow 22/tcp"
        echo "   sudo ufw reload"
        exit 1
        ;;
esac

echo ""
echo "================================================"
echo "✅ Fix Applied"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Try SSH connection: ssh $(whoami)@$(hostname -I | awk '{print $1}')"
echo "  2. If still not working, check SSH service: sudo systemctl status ssh"
echo ""
