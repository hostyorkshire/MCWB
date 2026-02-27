#!/bin/bash
#
# Cloudflare Tunnel Installation Script for MCWB Dashboard
# This script installs and configures cloudflared to expose the local dashboard
# to the internet securely without port forwarding
#

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================"
echo "  Cloudflare Tunnel Setup for MCWB Dashboard"
echo "================================================================"
echo ""
echo "This script will install and configure Cloudflare Tunnel to"
echo "securely expose your local dashboard (192.168.1.100:5000) to"
echo "the internet without port forwarding."
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}ERROR: Do not run this script as root${NC}"
    echo "Run as a regular user: ./install_cloudflare_tunnel.sh"
    exit 1
fi

# Detect system architecture
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        CLOUDFLARED_ARCH="amd64"
        ;;
    aarch64|arm64)
        CLOUDFLARED_ARCH="arm64"
        ;;
    armv7l|armv6l)
        CLOUDFLARED_ARCH="arm"
        ;;
    *)
        echo -e "${RED}ERROR: Unsupported architecture: $ARCH${NC}"
        exit 1
        ;;
esac

echo -e "${BLUE}Detected architecture: $ARCH (using cloudflared-$CLOUDFLARED_ARCH)${NC}"
echo ""

# Check if cloudflared is already installed
if command -v cloudflared &> /dev/null; then
    CURRENT_VERSION=$(cloudflared --version | head -1)
    echo -e "${GREEN}✓ cloudflared is already installed: $CURRENT_VERSION${NC}"
    echo ""
    read -r -p "Do you want to reinstall/update cloudflared? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping cloudflared installation..."
        SKIP_INSTALL=true
    fi
fi

# Install cloudflared
if [ "$SKIP_INSTALL" != true ]; then
    echo -e "${BLUE}Installing cloudflared...${NC}"
    
    # Download and install cloudflared
    CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CLOUDFLARED_ARCH}"
    
    echo "Downloading cloudflared from: $CLOUDFLARED_URL"
    
    if ! wget -q --show-progress "$CLOUDFLARED_URL" -O /tmp/cloudflared; then
        echo -e "${RED}ERROR: Failed to download cloudflared${NC}"
        echo "Please check your internet connection and try again."
        exit 1
    fi
    
    chmod +x /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
    
    echo -e "${GREEN}✓ cloudflared installed successfully${NC}"
    cloudflared --version
    echo ""
fi

# Check if dashboard is running
echo -e "${BLUE}Checking if web dashboard is running...${NC}"
if ! pgrep -f "web_dashboard.py" > /dev/null; then
    echo -e "${YELLOW}⚠ Warning: Web dashboard is not running${NC}"
    echo ""
    echo "The dashboard should be running before setting up the tunnel."
    echo "To start the dashboard:"
    echo "  sudo systemctl start mcwb-dashboard"
    echo "  OR"
    echo "  python3 web_dashboard.py --host 0.0.0.0"
    echo ""
    read -r -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
else
    echo -e "${GREEN}✓ Web dashboard is running${NC}"
fi
echo ""

# Create config directory
TUNNEL_CONFIG_DIR="$HOME/.cloudflared"
mkdir -p "$TUNNEL_CONFIG_DIR"

echo "================================================================"
echo "  Cloudflare Tunnel Configuration"
echo "================================================================"
echo ""
echo "To set up the tunnel, you need to authenticate with Cloudflare."
echo "This will open a browser window where you can log in."
echo ""
echo -e "${YELLOW}IMPORTANT: You need a Cloudflare account (free)${NC}"
echo "If you don't have one, sign up at: https://dash.cloudflare.com/sign-up"
echo ""
read -r -p "Press Enter to start authentication..."

# Authenticate with Cloudflare
echo ""
echo -e "${BLUE}Authenticating with Cloudflare...${NC}"
if ! cloudflared tunnel login; then
    echo -e "${RED}ERROR: Authentication failed${NC}"
    echo "Please try again or check your Cloudflare account."
    exit 1
fi

echo -e "${GREEN}✓ Authentication successful${NC}"
echo ""

# Create tunnel
TUNNEL_NAME="mcwb-dashboard-$(hostname)"
echo -e "${BLUE}Creating tunnel: $TUNNEL_NAME${NC}"

# Check if tunnel already exists
if cloudflared tunnel list 2>/dev/null | grep -q "$TUNNEL_NAME"; then
    echo -e "${YELLOW}⚠ Tunnel '$TUNNEL_NAME' already exists${NC}"
    read -r -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cloudflared tunnel delete -f "$TUNNEL_NAME" || true
    else
        echo "Using existing tunnel..."
    fi
fi

# Create new tunnel if it doesn't exist
if ! cloudflared tunnel list 2>/dev/null | grep -q "$TUNNEL_NAME"; then
    if ! cloudflared tunnel create "$TUNNEL_NAME"; then
        echo -e "${RED}ERROR: Failed to create tunnel${NC}"
        exit 1
    fi
fi

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list 2>/dev/null | grep "$TUNNEL_NAME" | awk '{print $1}')

if [ -z "$TUNNEL_ID" ]; then
    echo -e "${RED}ERROR: Could not find tunnel ID${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Tunnel created: $TUNNEL_ID${NC}"
echo ""

# Create tunnel configuration
echo -e "${BLUE}Creating tunnel configuration...${NC}"

# Note: The configuration will route ALL traffic from the tunnel domain to localhost:5000
# This is appropriate for a single-service tunnel
cat > "$TUNNEL_CONFIG_DIR/config.yml" <<EOF
# Cloudflare Tunnel Configuration for MCWB Dashboard
# Generated by install_cloudflare_tunnel.sh

tunnel: $TUNNEL_ID
credentials-file: $TUNNEL_CONFIG_DIR/$TUNNEL_ID.json

ingress:
  # Route all traffic to local dashboard
  # The hostname will be configured when you run: cloudflared tunnel route dns
  - service: http://localhost:5000
    originRequest:
      # Don't verify SSL for local connections
      noTLSVerify: true
      # Connection settings
      connectTimeout: 30s
      # HTTP/2 origin support
      http2Origin: false
  # Catch-all rule (required): return 404 for any unmatched traffic
  # Since we only have one service, this shouldn't be hit
  - service: http_status:404
EOF

echo -e "${GREEN}✓ Configuration file created: $TUNNEL_CONFIG_DIR/config.yml${NC}"
echo ""

# Create systemd service
echo -e "${BLUE}Creating systemd service...${NC}"

SERVICE_FILE="/tmp/cloudflared-mcwb.service"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Cloudflare Tunnel for MCWB Dashboard
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/local/bin/cloudflared tunnel --config $TUNNEL_CONFIG_DIR/config.yml run
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo mv "$SERVICE_FILE" /etc/systemd/system/cloudflared-mcwb.service
sudo systemctl daemon-reload

echo -e "${GREEN}✓ Systemd service created${NC}"
echo ""

# Get tunnel URL
echo "================================================================"
echo "  Setting up DNS Route"
echo "================================================================"
echo ""
echo "Now you need to create a DNS route for your tunnel."
echo ""
echo -e "${YELLOW}IMPORTANT: You need a domain registered with Cloudflare${NC}"
echo ""
echo "If you don't have a domain:"
echo "  1. Register a free domain (e.g., freenom.com, afraid.org)"
echo "  2. Add it to Cloudflare (free plan works)"
echo "  3. Update your domain's nameservers to Cloudflare's"
echo ""
read -r -p "Do you have a domain ready in Cloudflare? (y/N): " -n 1 -r
echo
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Enter your domain or subdomain (e.g., dashboard.yourdomain.com):"
    read -r -p "> " TUNNEL_DOMAIN
    
    if [ -n "$TUNNEL_DOMAIN" ]; then
        echo ""
        echo -e "${BLUE}Creating DNS route...${NC}"
        
        if cloudflared tunnel route dns "$TUNNEL_NAME" "$TUNNEL_DOMAIN"; then
            echo -e "${GREEN}✓ DNS route created successfully${NC}"
            echo ""
            echo "================================================================"
            echo "  ✅ TUNNEL SETUP COMPLETE!"
            echo "================================================================"
            echo ""
            echo -e "${GREEN}Your dashboard will be accessible at:${NC}"
            echo -e "${BLUE}  https://$TUNNEL_DOMAIN${NC}"
            echo ""
            
            # Save tunnel info
            echo "$TUNNEL_DOMAIN" > "$TUNNEL_CONFIG_DIR/tunnel_url.txt"
        else
            echo -e "${RED}ERROR: Failed to create DNS route${NC}"
            echo "You can create it manually later with:"
            echo "  cloudflared tunnel route dns $TUNNEL_NAME your-domain.com"
        fi
    fi
else
    echo ""
    echo "You can set up the DNS route later with:"
    echo "  cloudflared tunnel route dns $TUNNEL_NAME your-domain.com"
fi

echo ""
echo "================================================================"
echo "  Starting the Tunnel"
echo "================================================================"
echo ""

# Start and enable service
sudo systemctl enable cloudflared-mcwb.service
sudo systemctl start cloudflared-mcwb.service

echo -e "${GREEN}✓ Tunnel service started and enabled${NC}"
echo ""

# Wait a moment for tunnel to start
sleep 3

# Check status
if sudo systemctl is-active --quiet cloudflared-mcwb.service; then
    echo -e "${GREEN}✓ Tunnel is running successfully${NC}"
else
    echo -e "${RED}⚠ Tunnel service may have issues${NC}"
    echo "Check status with: sudo systemctl status cloudflared-mcwb.service"
fi

echo ""
echo "================================================================"
echo "  Next Steps"
echo "================================================================"
echo ""

if [ -f "$TUNNEL_CONFIG_DIR/tunnel_url.txt" ]; then
    TUNNEL_URL=$(cat "$TUNNEL_CONFIG_DIR/tunnel_url.txt")
    echo "1. Update your static website (weather.example.com):"
    echo "   - Edit public_html/wx/js/dashboard.js"
    echo "   - Set: const TUNNEL_URL = 'https://$TUNNEL_URL';"
    echo "   - Upload to cPanel hosting"
    echo ""
    echo "2. Test your tunnel:"
    echo "   - Open browser: https://$TUNNEL_URL"
    echo "   - You should see the dashboard"
    echo ""
fi

echo "3. Manage the tunnel:"
echo "   - Status:  sudo systemctl status cloudflared-mcwb.service"
echo "   - Stop:    sudo systemctl stop cloudflared-mcwb.service"
echo "   - Start:   sudo systemctl start cloudflared-mcwb.service"
echo "   - Logs:    sudo journalctl -u cloudflared-mcwb.service -f"
echo ""
echo "4. View all tunnels:"
echo "   cloudflared tunnel list"
echo ""

echo "================================================================"
echo "  Troubleshooting"
echo "================================================================"
echo ""
echo "If the tunnel doesn't work:"
echo "  1. Check tunnel status: sudo systemctl status cloudflared-mcwb.service"
echo "  2. Check tunnel logs: sudo journalctl -u cloudflared-mcwb.service -n 50"
echo "  3. Verify dashboard is running: sudo systemctl status mcwb-dashboard"
echo "  4. Test local access: curl http://localhost:5000/api/status"
echo ""
echo "For more help, see: CLOUDFLARE_TUNNEL_SETUP.md"
echo ""
