# MCWB Unified Service Manager

## Overview

The `setup_mcwb.sh` script provides an interactive menu for managing all MCWB services on your Raspberry Pi. No need to remember multiple installation scripts!

## Usage

```bash
cd ~/MCWB
./setup_mcwb.sh
```

## Main Menu

```
================================================
     MCWB - Service Manager
================================================

Current Status:
  ○ Weather Bot:    Not installed
  ○ Web Dashboard:  Not installed

================================================
What would you like to do?
================================================

  1) Install Weather Bot service
  2) Install Web Dashboard service
  3) Install BOTH services (recommended)

  4) Check service status
  5) Start/Stop services
  6) View service logs

  7) Uninstall services
  8) Configure firewall

  9) Quick Start Guide
  0) Exit

Enter your choice [0-9]:
```

## Features

### Installation (Options 1-3)
- **Option 1:** Install only the Weather Bot service
- **Option 2:** Install only the Web Dashboard service
- **Option 3:** Install BOTH services at once (recommended for new setups)

The installer automatically:
- Detects your username and paths
- Configures services correctly
- Sets up firewall if needed
- Shows connection URLs
- Enables auto-start on reboot

### Service Management (Options 4-6)

**Option 4: Check Status**
- Shows detailed status of both services
- Displays your local IP address
- Shows dashboard connection URL if running

**Option 5: Start/Stop Services**
- Submenu with 9 options:
  - Start/Stop/Restart Weather Bot individually
  - Start/Stop/Restart Web Dashboard individually
  - Start/Stop/Restart ALL services at once

**Option 6: View Logs**
- Recent logs (last 50 lines)
- Live logs (follow mode with Ctrl+C to exit)
- Access to viewlogs.py for file-based viewing

### Maintenance (Options 7-8)

**Option 7: Uninstall Services**
- Remove Weather Bot service
- Remove Web Dashboard service
- Remove BOTH services

**Option 8: Configure Firewall**
- Install UFW if not present
- Allow Web Dashboard port (5000)
- Allow SSH port (22) - Important!
- Enable/Disable firewall
- View firewall status

### Help (Option 9)

Shows quick start guidance and points to documentation files.

## Status Indicators

The menu shows real-time service status:
- 🟢 **Green ●** - Service is running
- 🟡 **Yellow ○** - Service installed but not running
- 🔴 **Red ○** - Service not installed

## Backwards Compatibility

The individual installation scripts still work if you prefer:
- `./install_service.sh` - Weather bot only
- `./install_dashboard_service.sh` - Dashboard only

## Quick Start Example

For a brand new Raspberry Pi setup:

```bash
cd ~/MCWB
./setup_mcwb.sh
# Choose option 3 (Install BOTH services)
# Answer prompts for firewall configuration
# Note the connection URL displayed
# Exit menu (option 0)
```

Then from any device on your network:
- Access dashboard at: http://192.168.1.109:5000 (or your Pi's IP)
- Send weather commands via mesh: "wx London"

## Documentation

- **CONNECTION_GUIDE.md** - Dashboard connection troubleshooting
- **QUICKSTART_SIMPLE.md** - Quick start for weather bot
- **WEB_DASHBOARD.md** - Full dashboard documentation
- **RASPBERRY_PI_SETUP.md** - Complete Pi setup guide
