#!/bin/bash
# MCWB - Unified Service Manager
# Interactive menu for managing all MCWB services on Raspberry Pi

# Note: We don't use 'set -e' here because this is an interactive script
# that needs to gracefully handle command failures (e.g., stopping non-existent services)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display the main menu
show_menu() {
    clear
    echo "================================================"
    echo "     MCWB - Service Manager"
    echo "================================================"
    echo ""
    echo "Current Status:"
    
    # Check weather bot service status
    if systemctl is-active --quiet weather_bot 2>/dev/null; then
        echo -e "  ${GREEN}●${NC} Weather Bot:    Running"
    elif systemctl is-enabled --quiet weather_bot 2>/dev/null; then
        echo -e "  ${YELLOW}○${NC} Weather Bot:    Installed (not running)"
    else
        echo -e "  ${RED}○${NC} Weather Bot:    Not installed"
    fi
    
    # Check dashboard service status
    if systemctl is-active --quiet mcwb-dashboard 2>/dev/null; then
        echo -e "  ${GREEN}●${NC} Web Dashboard:  Running"
    elif systemctl is-enabled --quiet mcwb-dashboard 2>/dev/null; then
        echo -e "  ${YELLOW}○${NC} Web Dashboard:  Installed (not running)"
    else
        echo -e "  ${RED}○${NC} Web Dashboard:  Not installed"
    fi
    
    echo ""
    echo "================================================"
    echo "What would you like to do?"
    echo "================================================"
    echo ""
    echo "  1) Install Weather Bot service"
    echo "  2) Install Web Dashboard service"
    echo "  3) Install BOTH services (recommended)"
    echo ""
    echo "  4) Check service status"
    echo "  5) Start/Stop services"
    echo "  6) View service logs"
    echo ""
    echo "  7) Uninstall services"
    echo "  8) Configure firewall"
    echo ""
    echo "  9) Quick Start Guide"
    echo "  0) Exit"
    echo ""
    echo -n "Enter your choice [0-9]: "
}

# Function to install weather bot service
install_weather_bot() {
    clear
    echo "================================================"
    echo "Installing Weather Bot Service"
    echo "================================================"
    echo ""
    
    if [ -f "./install_service.sh" ]; then
        ./install_service.sh
    else
        echo -e "${RED}❌ Error: install_service.sh not found${NC}"
        echo "Please run this script from the MCWB directory"
        read -p "Press Enter to continue..."
        return 1
    fi
    
    echo ""
    read -p "Press Enter to return to menu..."
}

# Function to install dashboard service
install_dashboard() {
    clear
    echo "================================================"
    echo "Installing Web Dashboard Service"
    echo "================================================"
    echo ""
    
    if [ -f "./install_dashboard_service.sh" ]; then
        ./install_dashboard_service.sh
    else
        echo -e "${RED}❌ Error: install_dashboard_service.sh not found${NC}"
        echo "Please run this script from the MCWB directory"
        read -p "Press Enter to continue..."
        return 1
    fi
    
    echo ""
    read -p "Press Enter to return to menu..."
}

# Function to install both services
install_both() {
    clear
    echo "================================================"
    echo "Installing ALL Services"
    echo "================================================"
    echo ""
    echo "This will install:"
    echo "  1. Weather Bot service (main bot)"
    echo "  2. Web Dashboard service (monitoring UI)"
    echo ""
    read -p "Continue? [Y/n] " -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "Installation cancelled"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo ""
    echo "Step 1/2: Installing Weather Bot service..."
    echo "================================================"
    if [ -f "./install_service.sh" ]; then
        ./install_service.sh
    else
        echo -e "${RED}❌ Error: install_service.sh not found${NC}"
        read -p "Press Enter to continue..."
        return 1
    fi
    
    echo ""
    echo ""
    echo "Step 2/2: Installing Web Dashboard service..."
    echo "================================================"
    if [ -f "./install_dashboard_service.sh" ]; then
        ./install_dashboard_service.sh
    else
        echo -e "${RED}❌ Error: install_dashboard_service.sh not found${NC}"
        read -p "Press Enter to continue..."
        return 1
    fi
    
    echo ""
    echo "================================================"
    echo -e "${GREEN}✅ All services installed successfully!${NC}"
    echo "================================================"
    echo ""
    read -p "Press Enter to return to menu..."
}

# Function to check service status
check_status() {
    clear
    echo "================================================"
    echo "Service Status"
    echo "================================================"
    echo ""
    
    echo "Weather Bot Service:"
    echo "----------------------------------------"
    if systemctl list-unit-files | grep -q "weather_bot.service"; then
        sudo systemctl status weather_bot --no-pager || true
    else
        echo "Not installed"
    fi
    
    echo ""
    echo "Web Dashboard Service:"
    echo "----------------------------------------"
    if systemctl list-unit-files | grep -q "mcwb-dashboard.service"; then
        sudo systemctl status mcwb-dashboard --no-pager || true
    else
        echo "Not installed"
    fi
    
    echo ""
    echo "Network Information:"
    echo "----------------------------------------"
    echo "Local IP: $(hostname -I | awk '{print $1}')"
    if systemctl is-active --quiet mcwb-dashboard 2>/dev/null; then
        echo "Dashboard URL: http://$(hostname -I | awk '{print $1}'):5000"
    fi
    
    echo ""
    read -p "Press Enter to return to menu..."
}

# Function to start/stop services
start_stop_services() {
    clear
    echo "================================================"
    echo "Start/Stop Services"
    echo "================================================"
    echo ""
    echo "  1) Start Weather Bot"
    echo "  2) Stop Weather Bot"
    echo "  3) Restart Weather Bot"
    echo ""
    echo "  4) Start Web Dashboard"
    echo "  5) Stop Web Dashboard"
    echo "  6) Restart Web Dashboard"
    echo ""
    echo "  7) Start ALL services"
    echo "  8) Stop ALL services"
    echo "  9) Restart ALL services"
    echo ""
    echo "  0) Back to main menu"
    echo ""
    echo -n "Enter your choice [0-9]: "
    read -n 1 choice
    echo ""
    echo ""
    
    case $choice in
        1) sudo systemctl start weather_bot && echo -e "${GREEN}✅ Weather Bot started${NC}" ;;
        2) sudo systemctl stop weather_bot && echo -e "${YELLOW}⏸️  Weather Bot stopped${NC}" ;;
        3) sudo systemctl restart weather_bot && echo -e "${GREEN}🔄 Weather Bot restarted${NC}" ;;
        4) sudo systemctl start mcwb-dashboard && echo -e "${GREEN}✅ Web Dashboard started${NC}" ;;
        5) sudo systemctl stop mcwb-dashboard && echo -e "${YELLOW}⏸️  Web Dashboard stopped${NC}" ;;
        6) sudo systemctl restart mcwb-dashboard && echo -e "${GREEN}🔄 Web Dashboard restarted${NC}" ;;
        7) 
            sudo systemctl start weather_bot mcwb-dashboard
            echo -e "${GREEN}✅ All services started${NC}"
            ;;
        8) 
            sudo systemctl stop weather_bot mcwb-dashboard
            echo -e "${YELLOW}⏸️  All services stopped${NC}"
            ;;
        9) 
            sudo systemctl restart weather_bot mcwb-dashboard
            echo -e "${GREEN}🔄 All services restarted${NC}"
            ;;
        0) return ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

# Function to view logs
view_logs() {
    clear
    echo "================================================"
    echo "View Service Logs"
    echo "================================================"
    echo ""
    echo "  1) Weather Bot logs (recent)"
    echo "  2) Web Dashboard logs (recent)"
    echo "  3) Weather Bot logs (live/follow)"
    echo "  4) Web Dashboard logs (live/follow)"
    echo "  5) View log files directly"
    echo "  0) Back to main menu"
    echo ""
    echo -n "Enter your choice [0-5]: "
    read -n 1 choice
    echo ""
    echo ""
    
    case $choice in
        1) 
            echo "Recent Weather Bot logs:"
            echo "----------------------------------------"
            sudo journalctl -u weather_bot -n 50 --no-pager
            ;;
        2) 
            echo "Recent Web Dashboard logs:"
            echo "----------------------------------------"
            sudo journalctl -u mcwb-dashboard -n 50 --no-pager
            ;;
        3) 
            echo "Following Weather Bot logs (Press Ctrl+C to stop)..."
            echo "----------------------------------------"
            sudo journalctl -u weather_bot -f
            ;;
        4) 
            echo "Following Web Dashboard logs (Press Ctrl+C to stop)..."
            echo "----------------------------------------"
            sudo journalctl -u mcwb-dashboard -f
            ;;
        5)
            if [ -f "./viewlogs.py" ]; then
                python3 ./viewlogs.py
            else
                echo -e "${RED}❌ viewlogs.py not found${NC}"
            fi
            ;;
        0) return ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
    
    # Don't wait for Enter if user chose live log following (options 3 or 4)
    # Those commands block until Ctrl+C, so no prompt is needed
    if [ "$choice" != "0" ] && [ "$choice" != "3" ] && [ "$choice" != "4" ]; then
        echo ""
        read -p "Press Enter to continue..."
    fi
}

# Function to uninstall services
uninstall_services() {
    clear
    echo "================================================"
    echo "Uninstall Services"
    echo "================================================"
    echo ""
    echo -e "${YELLOW}⚠️  This will remove the systemd services${NC}"
    echo ""
    echo "  1) Uninstall Weather Bot service"
    echo "  2) Uninstall Web Dashboard service"
    echo "  3) Uninstall BOTH services"
    echo "  0) Back to main menu"
    echo ""
    echo -n "Enter your choice [0-3]: "
    read -n 1 choice
    echo ""
    echo ""
    
    case $choice in
        1)
            echo "Uninstalling Weather Bot service..."
            sudo systemctl stop weather_bot 2>/dev/null || true
            sudo systemctl disable weather_bot 2>/dev/null || true
            sudo rm -f /etc/systemd/system/weather_bot.service
            sudo systemctl daemon-reload
            echo -e "${GREEN}✅ Weather Bot service uninstalled${NC}"
            ;;
        2)
            echo "Uninstalling Web Dashboard service..."
            sudo systemctl stop mcwb-dashboard 2>/dev/null || true
            sudo systemctl disable mcwb-dashboard 2>/dev/null || true
            sudo rm -f /etc/systemd/system/mcwb-dashboard.service
            sudo systemctl daemon-reload
            echo -e "${GREEN}✅ Web Dashboard service uninstalled${NC}"
            ;;
        3)
            echo "Uninstalling all services..."
            sudo systemctl stop weather_bot mcwb-dashboard 2>/dev/null || true
            sudo systemctl disable weather_bot mcwb-dashboard 2>/dev/null || true
            sudo rm -f /etc/systemd/system/weather_bot.service
            sudo rm -f /etc/systemd/system/mcwb-dashboard.service
            sudo systemctl daemon-reload
            echo -e "${GREEN}✅ All services uninstalled${NC}"
            ;;
        0) return ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

# Function to configure firewall
configure_firewall() {
    clear
    echo "================================================"
    echo "Firewall Configuration"
    echo "================================================"
    echo ""
    
    if ! command -v ufw >/dev/null 2>&1; then
        echo -e "${YELLOW}ℹ️  UFW (firewall) is not installed${NC}"
        echo ""
        read -p "Would you like to install UFW? [y/N] " -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt-get update
            sudo apt-get install -y ufw
            echo -e "${GREEN}✅ UFW installed${NC}"
        else
            echo "Skipping firewall configuration"
            read -p "Press Enter to continue..."
            return
        fi
    fi
    
    echo "Current firewall status:"
    sudo ufw status
    echo ""
    
    echo "  1) Allow Web Dashboard port (5000/tcp)"
    echo "  2) Allow SSH (22/tcp) - Important!"
    echo "  3) Enable firewall"
    echo "  4) Disable firewall"
    echo "  5) Show firewall status"
    echo "  0) Back to main menu"
    echo ""
    echo -n "Enter your choice [0-5]: "
    read -n 1 choice
    echo ""
    echo ""
    
    case $choice in
        1)
            sudo ufw allow 5000/tcp
            echo -e "${GREEN}✅ Port 5000 (Web Dashboard) allowed${NC}"
            ;;
        2)
            sudo ufw allow 22/tcp
            echo -e "${GREEN}✅ Port 22 (SSH) allowed${NC}"
            echo -e "${YELLOW}⚠️  Make sure SSH is allowed BEFORE enabling firewall!${NC}"
            ;;
        3)
            echo -e "${RED}⚠️  CRITICAL: Enabling the firewall can lock you out!${NC}"
            echo -e "${YELLOW}   You MUST have SSH (port 22) allowed BEFORE enabling!${NC}"
            echo ""
            echo "Current firewall rules:"
            sudo ufw status numbered
            echo ""
            echo -e "${YELLOW}Is SSH (port 22) shown above?${NC}"
            read -p "Confirm you want to enable the firewall [y/N] " -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                # Let UFW ask for its own confirmation (don't use --force)
                echo ""
                echo "UFW will ask for final confirmation..."
                sudo ufw enable
                echo -e "${GREEN}✅ Firewall enabled${NC}"
            else
                echo "Firewall not enabled (safe choice)"
            fi
            ;;
        4)
            sudo ufw disable
            echo -e "${YELLOW}⚠️  Firewall disabled${NC}"
            ;;
        5)
            sudo ufw status verbose
            ;;
        0) return ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

# Function to show quick start guide
show_quick_start() {
    clear
    echo "================================================"
    echo "Quick Start Guide"
    echo "================================================"
    echo ""
    echo "🚀 For first-time setup, we recommend:"
    echo ""
    echo "  1. Install BOTH services (option 3 from main menu)"
    echo "  2. The installer will:"
    echo "     • Configure services for your username/paths"
    echo "     • Set up firewall if needed"
    echo "     • Start the services"
    echo "     • Show connection URLs"
    echo ""
    echo "📡 After installation:"
    echo "  • Weather Bot will respond to 'wx [location]' commands"
    echo "  • Web Dashboard accessible at http://[your-ip]:5000"
    echo "  • Both services start automatically on reboot"
    echo ""
    echo "📚 Documentation:"
    echo "  • QUICKSTART_SIMPLE.md - Quick start for weather bot"
    echo "  • CONNECTION_GUIDE.md - Dashboard connection help"
    echo "  • WEB_DASHBOARD.md - Full dashboard documentation"
    echo "  • RASPBERRY_PI_SETUP.md - Complete Pi setup guide"
    echo ""
    read -p "Press Enter to return to menu..."
}

# Main loop
main() {
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        echo -e "${RED}❌ Error: Do not run this script as root (don't use sudo)${NC}"
        echo "   The script will ask for sudo password when needed"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "weather_bot.py" ]; then
        echo -e "${RED}❌ Error: weather_bot.py not found in current directory${NC}"
        echo "   Please run this script from the MCWB directory"
        exit 1
    fi
    
    while true; do
        show_menu
        read -n 1 choice
        echo ""
        
        case $choice in
            1) install_weather_bot ;;
            2) install_dashboard ;;
            3) install_both ;;
            4) check_status ;;
            5) start_stop_services ;;
            6) view_logs ;;
            7) uninstall_services ;;
            8) configure_firewall ;;
            9) show_quick_start ;;
            0) 
                clear
                echo "Goodbye!"
                exit 0
                ;;
            *)
                echo ""
                echo -e "${RED}Invalid option. Please try again.${NC}"
                sleep 1
                ;;
        esac
    done
}

# Run main function
main
