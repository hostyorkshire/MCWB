#!/bin/bash
# WiFi Connectivity Diagnostic and Troubleshooting Script
# This script helps diagnose and fix WiFi connectivity issues on Raspberry Pi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "MCWB - WiFi Connectivity Diagnostic Tool"
echo "========================================================================"
echo ""
echo -e "${YELLOW}This script checks WiFi connection and internet connectivity${NC}"
echo ""

# Track if we found any issues
ISSUES_FOUND=0

# ============================================================================
# Check 1: WiFi Adapter Status
# ============================================================================

echo "🔍 [1/7] Checking WiFi Adapter Status..."
echo ""

# Get wireless interface name
WIFI_INTERFACE=$(iw dev 2>/dev/null | grep Interface | awk '{print $2}' | head -1)

if [ -z "$WIFI_INTERFACE" ]; then
    echo -e "${RED}✗${NC} No WiFi adapter found"
    echo "   Your system may not have a wireless adapter or drivers are not loaded"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
    
    # Check if wlan0 exists but isn't detected by iw
    if ip link show wlan0 >/dev/null 2>&1; then
        WIFI_INTERFACE="wlan0"
        echo -e "${YELLOW}⚠${NC} Found wlan0 interface, but iw command not available"
        echo "   Install wireless-tools: sudo apt install wireless-tools iw"
    fi
else
    echo -e "${GREEN}✓${NC} WiFi adapter found: ${WIFI_INTERFACE}"
    
    # Check if interface is up
    if ip link show "$WIFI_INTERFACE" | grep -q "state UP"; then
        echo -e "${GREEN}✓${NC} WiFi interface is UP"
    else
        echo -e "${RED}✗${NC} WiFi interface is DOWN"
        echo "   Try: sudo ip link set ${WIFI_INTERFACE} up"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
fi

echo ""

# ============================================================================
# Check 2: WiFi Connection Status
# ============================================================================

echo "🔍 [2/7] Checking WiFi Connection Status..."
echo ""

if [ -n "$WIFI_INTERFACE" ]; then
    # Try to get connection info using iwconfig
    if command -v iwconfig >/dev/null 2>&1; then
        ESSID=$(iwconfig "$WIFI_INTERFACE" 2>/dev/null | grep ESSID | sed 's/.*ESSID:"\(.*\)".*/\1/')
        
        if [ -n "$ESSID" ] && [ "$ESSID" != "off/any" ]; then
            echo -e "${GREEN}✓${NC} Connected to network: ${ESSID}"
            
            # Get signal strength
            SIGNAL=$(iwconfig "$WIFI_INTERFACE" 2>/dev/null | grep "Signal level" | sed 's/.*Signal level=\(.*\) dBm.*/\1/')
            if [ -n "$SIGNAL" ]; then
                # Convert to quality (rough approximation)
                if [ "$SIGNAL" -gt -50 ]; then
                    echo -e "${GREEN}✓${NC} Signal strength: Excellent (${SIGNAL} dBm)"
                elif [ "$SIGNAL" -gt -60 ]; then
                    echo -e "${GREEN}✓${NC} Signal strength: Good (${SIGNAL} dBm)"
                elif [ "$SIGNAL" -gt -70 ]; then
                    echo -e "${YELLOW}⚠${NC} Signal strength: Fair (${SIGNAL} dBm)"
                    echo "   Consider moving closer to the router"
                else
                    echo -e "${RED}✗${NC} Signal strength: Poor (${SIGNAL} dBm)"
                    echo "   Move closer to the router or check for interference"
                    ISSUES_FOUND=$((ISSUES_FOUND + 1))
                fi
            fi
        else
            echo -e "${RED}✗${NC} Not connected to any WiFi network"
            echo "   Run: sudo raspi-config (select Wireless LAN)"
            echo "   Or: sudo nmtui (if NetworkManager is installed)"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    elif command -v iw >/dev/null 2>&1; then
        # Try using iw if iwconfig is not available
        SSID=$(iw dev "$WIFI_INTERFACE" link 2>/dev/null | grep SSID | awk '{print $2}')
        if [ -n "$SSID" ]; then
            echo -e "${GREEN}✓${NC} Connected to network: ${SSID}"
        else
            echo -e "${RED}✗${NC} Not connected to any WiFi network"
            echo "   Run: sudo raspi-config (select Wireless LAN)"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    else
        echo -e "${YELLOW}⚠${NC} Cannot determine connection status (tools not available)"
        echo "   Install tools: sudo apt install wireless-tools iw"
    fi
else
    echo -e "${RED}✗${NC} No WiFi interface available to check"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""

# ============================================================================
# Check 3: IP Address Assignment
# ============================================================================

echo "🔍 [3/7] Checking IP Address..."
echo ""

if [ -n "$WIFI_INTERFACE" ]; then
    # Get IP address
    IP_ADDR=$(ip addr show "$WIFI_INTERFACE" 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
    
    if [ -n "$IP_ADDR" ]; then
        echo -e "${GREEN}✓${NC} IP Address assigned: ${IP_ADDR}"
    else
        echo -e "${RED}✗${NC} No IP address assigned"
        echo "   WiFi may be connected but DHCP failed"
        echo "   Try: sudo dhclient ${WIFI_INTERFACE}"
        echo "   Or restart networking: sudo systemctl restart networking"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
else
    echo -e "${RED}✗${NC} No WiFi interface to check"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""

# ============================================================================
# Check 4: Gateway/Router Connectivity
# ============================================================================

echo "🔍 [4/7] Checking Gateway (Router) Connectivity..."
echo ""

# Get default gateway
GATEWAY=$(ip route | grep default | awk '{print $3}' | head -1)

if [ -n "$GATEWAY" ]; then
    echo "   Gateway: ${GATEWAY}"
    
    # Ping gateway
    if ping -c 2 -W 2 "$GATEWAY" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Can reach gateway (router)"
    else
        echo -e "${RED}✗${NC} Cannot reach gateway (router)"
        echo "   Your device has an IP but can't communicate with the router"
        echo "   Check: Router is powered on, WiFi signal strength"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
else
    echo -e "${RED}✗${NC} No default gateway configured"
    echo "   Your device may not have received network configuration from DHCP"
    echo "   Try: sudo dhclient ${WIFI_INTERFACE:-wlan0}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""

# ============================================================================
# Check 5: Internet Connectivity
# ============================================================================

echo "🔍 [5/7] Checking Internet Connectivity..."
echo ""

# Test with multiple reliable servers
PING_TARGETS=("8.8.8.8" "1.1.1.1")
PING_SUCCESS=false

for target in "${PING_TARGETS[@]}"; do
    if ping -c 2 -W 3 "$target" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Internet connectivity working (reached ${target})"
        PING_SUCCESS=true
        break
    fi
done

if [ "$PING_SUCCESS" = false ]; then
    echo -e "${RED}✗${NC} Cannot reach the internet"
    echo "   Possible causes:"
    echo "   - Router has no internet connection"
    echo "   - ISP outage"
    echo "   - Firewall blocking outbound connections"
    echo "   Try: Check if other devices on your network can access the internet"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""

# ============================================================================
# Check 6: DNS Resolution
# ============================================================================

echo "🔍 [6/7] Checking DNS Resolution..."
echo ""

# Check DNS servers
DNS_SERVERS=$(grep "^nameserver" /etc/resolv.conf 2>/dev/null | awk '{print $2}')

if [ -n "$DNS_SERVERS" ]; then
    echo "   Configured DNS servers:"
    echo "$DNS_SERVERS" | sed 's/^/   - /'
    echo ""
    
    # Test DNS resolution
    if host github.com >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} DNS resolution working (resolved github.com)"
    elif nslookup github.com >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} DNS resolution working (resolved github.com)"
    elif ping -c 1 -W 2 github.com >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} DNS resolution working (resolved github.com)"
    else
        echo -e "${RED}✗${NC} DNS resolution failed"
        echo "   This is why 'git pull' shows 'could not resolve host'"
        echo "   Your internet works but domain names cannot be resolved"
        echo ""
        echo "   Quick fix:"
        echo "   sudo bash -c 'echo \"nameserver 8.8.8.8\" > /etc/resolv.conf'"
        echo "   sudo bash -c 'echo \"nameserver 1.1.1.1\" >> /etc/resolv.conf'"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
else
    echo -e "${RED}✗${NC} No DNS servers configured"
    echo "   This is why 'git pull' shows 'could not resolve host'"
    echo ""
    echo "   Quick fix:"
    echo "   sudo bash -c 'echo \"nameserver 8.8.8.8\" > /etc/resolv.conf'"
    echo "   sudo bash -c 'echo \"nameserver 1.1.1.1\" >> /etc/resolv.conf'"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""

# ============================================================================
# Check 7: Network Configuration Files
# ============================================================================

echo "🔍 [7/7] Checking Network Configuration..."
echo ""

# Check for common configuration files
if [ -f /etc/wpa_supplicant/wpa_supplicant.conf ]; then
    echo -e "${GREEN}✓${NC} WiFi configuration file exists: /etc/wpa_supplicant/wpa_supplicant.conf"
    
    # Check if it has any networks configured
    NETWORK_COUNT=$(grep -c "^network=" /etc/wpa_supplicant/wpa_supplicant.conf 2>/dev/null || echo 0)
    if [ "$NETWORK_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} ${NETWORK_COUNT} network(s) configured"
    else
        echo -e "${YELLOW}⚠${NC} No networks configured in wpa_supplicant.conf"
    fi
else
    echo -e "${YELLOW}⚠${NC} wpa_supplicant.conf not found"
    echo "   This file may not be used on your system"
fi

# Check if NetworkManager is being used
if systemctl is-active --quiet NetworkManager; then
    echo -e "${BLUE}ℹ${NC} NetworkManager is active (alternative to wpa_supplicant)"
fi

# Check if systemd-networkd is being used
if systemctl is-active --quiet systemd-networkd; then
    echo -e "${BLUE}ℹ${NC} systemd-networkd is active"
fi

echo ""

# ============================================================================
# Summary and Recommendations
# ============================================================================

echo "========================================================================"
echo "Summary"
echo "========================================================================"
echo ""

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ No issues detected!${NC}"
    echo ""
    echo "Your WiFi and internet connection appear to be working correctly."
    echo ""
    if [ -n "$IP_ADDR" ]; then
        echo "Current IP Address: ${IP_ADDR}"
    fi
    echo ""
    echo "If you're still having issues with git pull or other network operations,"
    echo "the problem may be:"
    echo "  - Temporary network interruption (try again)"
    echo "  - Specific firewall rules blocking certain ports"
    echo "  - GitHub.com accessibility issues"
    echo ""
    echo "Try: ping github.com"
    echo "Try: curl -I https://github.com"
else
    echo -e "${RED}❌ Found ${ISSUES_FOUND} issue(s) with your network configuration${NC}"
    echo ""
    echo "📋 Quick Troubleshooting Steps:"
    echo ""
    echo "1. Restart WiFi interface:"
    echo "   sudo ip link set ${WIFI_INTERFACE:-wlan0} down"
    echo "   sudo ip link set ${WIFI_INTERFACE:-wlan0} up"
    echo ""
    echo "2. Restart networking service:"
    echo "   sudo systemctl restart networking"
    echo "   (or: sudo systemctl restart NetworkManager)"
    echo ""
    echo "3. Reconfigure WiFi:"
    echo "   sudo raspi-config"
    echo "   → Select 'System Options' → 'Wireless LAN'"
    echo "   → Enter SSID and password"
    echo ""
    echo "4. Reboot the system:"
    echo "   sudo reboot"
    echo ""
    echo "5. Check router settings:"
    echo "   - Ensure WiFi is enabled"
    echo "   - Check MAC address filtering"
    echo "   - Verify DHCP is enabled"
    echo ""
    echo "📖 For more help, see:"
    echo "   - TROUBLESHOOTING.md"
    echo "   - API_CONNECTIVITY_TROUBLESHOOTING.md"
fi

echo ""
echo "========================================================================"
echo ""
