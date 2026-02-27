# QUICK FIX GUIDE

This guide provides fast solutions for the most common issues.

## 🚨 EMERGENCY: Can't SSH Into Pi AND/OR Can't See Dashboard

### Symptoms
- Cannot SSH into your Raspberry Pi
- Cannot access dashboard at http://[your-pi-ip]:5000
- One or both services not working

### Ultra-Quick Fix (Handles Both Issues)
```bash
cd ~/MCWB
./fix_access_issues.sh
```

This master script will:
- ✅ Diagnose SSH access issues (firewall, service status)
- ✅ Diagnose dashboard issues (service, firewall, dependencies)
- ✅ Automatically fix both problems with one command
- ✅ Provide clear status and next steps

**This is the fastest way to restore access!** It runs comprehensive checks and fixes everything automatically.

### Individual Issue Scripts

If you only have one specific issue, you can use these targeted scripts:

---

## Issue 1: Dashboard URL Not Working (e.g., http://192.168.1.100:5000)

### Symptom
- Dashboard **was working** before on that IP and port
- Now the URL doesn't open in browser
- You just get "can't connect" or similar error

**Note:** The IP address 192.168.1.100 is just an example. Your dashboard may be on a different IP address.

### Quick Fix
```bash
cd ~/MCWB
./fix_dashboard.sh
```

This script will:
- ✅ Check if service is running and restart if needed
- ✅ Fix missing dependencies automatically
- ✅ Detect permission problems
- ✅ Identify port conflicts
- ✅ Get you back online in under 30 seconds

### If Quick Fix Doesn't Work
```bash
cd ~/MCWB
./diagnose_dashboard.sh
```

This runs comprehensive diagnostics and offers fixes for:
- Service not installed/enabled
- Firewall blocking port 5000
- Service bound to localhost only (not network)
- Python packages missing
- And more...

---

## Issue 2: Weather Bot Not Announcing on Boot

### Symptom
- Weather bot service is running
- But no announcement message sent when it starts
- You expect to see "Hello this is the WX Bot..." on startup

### Root Cause
The weather_bot.service file was missing the `ExecStart` line with announcement flags.

### Fix

**Step 1: Reinstall the weather bot service**
```bash
cd ~/MCWB
./install_service.sh
```

The service file now includes:
- `--announce` - Sends announcement on every startup + every 6 hours
- `--reboot-notify` - Sends notification when bot restarts after reboot/crash

**Step 2: Verify it worked**
```bash
# Restart the service to test
sudo systemctl restart weather_bot

# Wait 5 seconds, then check logs
sudo journalctl -u weather_bot -n 30

# Look for: "Sent startup announcement to channel_idx=..."
```

You should see the announcement message in your MeshCore app!

### What Changed
Updated `weather_bot.service` file now contains:
```ini
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --announce --reboot-notify
```

---

## Quick Command Reference

### Dashboard Issues
```bash
# Quick fix (if it worked before)
./fix_dashboard.sh

# Full diagnostics
./diagnose_dashboard.sh

# Manual checks
sudo systemctl status mcwb-dashboard
sudo systemctl restart mcwb-dashboard
curl http://localhost:5000
```

### Weather Bot Issues
```bash
# Reinstall with announcements
./install_service.sh

# Check if running
sudo systemctl status weather_bot

# Restart and test
sudo systemctl restart weather_bot
sudo journalctl -u weather_bot -n 30

# View live logs
sudo journalctl -u weather_bot -f
```

### Both Services
```bash
# Unified menu for managing both
./setup_mcwb.sh

# Check both services at once
sudo systemctl status mcwb-dashboard weather_bot
```

---

## Prevention Tips

### For Dashboard
1. **Reserve static IP** in your router (e.g., 192.168.1.100)
   - Prevents IP changes after router reboots
   - See CONNECTION_GUIDE.md Step 1.5

2. **Verify service is enabled**
   ```bash
   sudo systemctl is-enabled mcwb-dashboard
   # Should show: enabled
   ```

3. **Check firewall allows port 5000**
   ```bash
   sudo ufw allow 5000/tcp
   ```

### For Weather Bot Announcements
1. **Verify service file has --announce flag**
   ```bash
   grep "announce" /etc/systemd/system/weather_bot.service
   # Should show: --announce --reboot-notify
   ```

2. **Ensure service starts after network is online**
   ```bash
   grep "network-online" /etc/systemd/system/weather_bot.service
   # Should show: After=network-online.target
   ```

3. **Check the bot detects your weather channel**
   - Service logs will show: "Sent startup announcement to channel_idx=X"
   - If channel_idx=0, the bot is using the default channel
   - The bot auto-detects #weather channel from incoming messages

---

## Still Having Issues?

### Dashboard
1. Run diagnostics and save output:
   ```bash
   ./diagnose_dashboard.sh > ~/dashboard_diagnostics.txt
   ```

2. Capture service logs:
   ```bash
   sudo journalctl -u mcwb-dashboard -n 100 > ~/dashboard_logs.txt
   ```

3. Open issue at https://github.com/hostyorkshire/MCWB/issues
   - Attach both files
   - Include your Raspberry Pi model and OS version

### Weather Bot Announcements
1. Capture service startup:
   ```bash
   sudo systemctl restart weather_bot
   sleep 10
   sudo journalctl -u weather_bot -n 50 > ~/weatherbot_startup.txt
   ```

2. Check if radio is connected:
   ```bash
   ls -l /dev/ttyUSB* /dev/ttyACM*
   ```

3. Open issue with:
   - Service logs (weatherbot_startup.txt)
   - Radio connection status
   - Your MeshCore firmware version

---

## See Also

- [TROUBLESHOOTING_SCRIPTS.md](TROUBLESHOOTING_SCRIPTS.md) - Detailed script documentation
- [CONNECTION_GUIDE.md](CONNECTION_GUIDE.md) - Simple connection guide
- [DASHBOARD_CONNECTIVITY_TROUBLESHOOTING.md](DASHBOARD_CONNECTIVITY_TROUBLESHOOTING.md) - Comprehensive troubleshooting
- [README.md](README.md) - Full project documentation
