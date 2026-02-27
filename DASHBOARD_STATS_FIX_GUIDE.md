# Dashboard Connection & Stats Display Fix Guide

## Your Issue

You reported:
- ✗ **Cannot connect to the dashboard locally**
- ✗ **Website stats are not displaying on live stats page**
- ✓ **SSH is working** (good - this means we can fix it!)

## Quick Fix (Run This First!)

SSH into your Raspberry Pi and run:

```bash
cd ~/MCWB
./fix_dashboard_connection_and_stats.sh
```

This automated script will:
1. ✅ Check if dashboard service is installed and running
2. ✅ Test local and network connectivity
3. ✅ Fix firewall issues (if needed)
4. ✅ Verify and repair stats files (stats.json, channels.json)
5. ✅ Check file permissions
6. ✅ Restart the service
7. ✅ Verify everything is working

**This should fix both your connection and stats issues in under 1 minute!**

---

## Understanding The Issues

### Issue 1: Cannot Connect to Dashboard Locally

**Possible Causes:**
1. Dashboard service is not running
2. Service crashed or failed to start
3. Port 5000 is blocked by firewall
4. Wrong URL (using HTTPS instead of HTTP)
5. Port 5000 is used by another process
6. Service configuration is incorrect

### Issue 2: Stats Not Displaying

**Possible Causes:**
1. Stats file (`logs/stats.json`) is missing or corrupted
2. Channels file (`logs/channels.json`) is missing or corrupted
3. File permission issues (dashboard can't write to files)
4. Weather bot is not running (so no stats to display)
5. Stats tracker initialization failed

---

## Manual Diagnostic Steps (If Script Doesn't Work)

### Step 1: Check Dashboard Service Status

```bash
# Check if service is running
sudo systemctl status mcwb-dashboard

# If not running, check logs
sudo journalctl -u mcwb-dashboard -n 50 --no-pager

# Common log errors and fixes:
# - "ModuleNotFoundError" → pip3 install -r ~/MCWB/requirements.txt
# - "Permission denied" → Check file permissions
# - "Address already in use" → Port 5000 is taken by another process
```

### Step 2: Test Local Connectivity

```bash
# Test if dashboard responds locally
curl http://localhost:5000

# Should return HTML content
# If it fails:
# - "Connection refused" → Service is not running
# - "No route to host" → Firewall blocking
# - No response → Service is hung

# Test the stats API specifically
curl http://localhost:5000/api/data

# Should return JSON like:
# {"total_requests":0,"total_errors":0,"success_rate":0.0,"last_updated":null,"status":"running"}
```

### Step 3: Check Network Connectivity

```bash
# Get your Pi's IP address
hostname -I
# Example output: 192.168.1.100

# Test from the Pi itself
curl http://192.168.1.100:5000

# Test from another computer on same network
# Open browser: http://192.168.1.100:5000
```

### Step 4: Check Firewall

```bash
# Check firewall status
sudo ufw status

# If port 5000 is not listed, add it:
sudo ufw allow 5000/tcp

# Reload firewall
sudo ufw reload
```

### Step 5: Check Stats Files

```bash
# Navigate to MCWB directory
cd ~/MCWB/logs

# Check if stats file exists
ls -lh stats.json

# View current stats
cat stats.json | python3 -m json.tool

# If file is missing or corrupted, recreate it:
cat > stats.json << 'EOF'
{
  "total_requests": 0,
  "total_errors": 0,
  "locations": {},
  "hourly_requests": {},
  "daily_requests": {},
  "error_types": {},
  "last_updated": null,
  "recent_users": []
}
EOF

# Check channels file
cat > channels.json << 'EOF'
{
  "channels": [],
  "last_updated": "2024-01-01T00:00:00"
}
EOF

# Fix permissions
chmod 644 stats.json channels.json
chown $(whoami):$(whoami) stats.json channels.json
```

### Step 6: Restart Dashboard Service

```bash
# Restart the service
sudo systemctl restart mcwb-dashboard

# Wait a few seconds, then check status
sleep 5
sudo systemctl status mcwb-dashboard

# Test connectivity
curl http://localhost:5000/api/data
```

---

## Common Issues & Solutions

### Issue: "Connection Refused" Error

**Cause:** Dashboard service is not running

**Fix:**
```bash
# Start the service
sudo systemctl start mcwb-dashboard

# Enable it to start on boot
sudo systemctl enable mcwb-dashboard

# Check status
sudo systemctl status mcwb-dashboard
```

### Issue: "SSL/HTTPS Error" in Browser

**Cause:** Trying to use HTTPS on HTTP-only dashboard

**Fix:**
- ✅ Use: `http://192.168.1.100:5000` (HTTP)
- ❌ Not: `https://192.168.1.100:5000` (HTTPS)

Or enable SSL:
```bash
cd ~/MCWB
python3 generate_ssl_cert.py --hostname $(hostname -I | awk '{print $1}')

# Update service to use SSL
sudo nano /etc/systemd/system/mcwb-dashboard.service
# Add --ssl to the ExecStart line
# Then:
sudo systemctl daemon-reload
sudo systemctl restart mcwb-dashboard
```

### Issue: Stats Show All Zeros

**Cause:** Weather bot is not processing requests yet

**Fix:**
```bash
# Check if weather bot is running
sudo systemctl status weather-bot

# If not running:
sudo systemctl start weather-bot

# Test the bot by sending a weather request via MeshCore
# Stats will update after people use the bot
```

### Issue: "Port Already in Use"

**Cause:** Another process is using port 5000

**Fix:**
```bash
# Find what's using port 5000
sudo netstat -tlnp | grep :5000
# or
sudo ss -tlnp | grep :5000

# Kill the process (replace PID with actual process ID)
sudo kill -9 <PID>

# Or use a different port for dashboard
sudo nano /etc/systemd/system/mcwb-dashboard.service
# Change --port 5000 to --port 8080
# Then:
sudo systemctl daemon-reload
sudo systemctl restart mcwb-dashboard
```

### Issue: Dashboard Works Locally But Not From Network

**Cause:** Firewall blocking or wrong IP address

**Fix:**
```bash
# Allow port in firewall
sudo ufw allow 5000/tcp

# Verify dashboard is bound to 0.0.0.0 (not 127.0.0.1)
sudo systemctl cat mcwb-dashboard | grep ExecStart
# Should show: --host 0.0.0.0

# Get correct IP address
hostname -I
# Use this IP in your browser
```

---

## Verification Steps

After applying fixes, verify everything works:

```bash
# 1. Check service is running
sudo systemctl is-active mcwb-dashboard
# Output should be: active

# 2. Test local connection
curl http://localhost:5000
# Should return HTML

# 3. Test stats API
curl http://localhost:5000/api/data
# Should return JSON with stats

# 4. Test from network
# Get IP: hostname -I
# Open browser: http://YOUR_PI_IP:5000

# 5. Check stats files are writable
ls -lh ~/MCWB/logs/*.json
# Should show your username as owner

# 6. Verify weather bot is running (for stats to populate)
sudo systemctl status weather-bot
```

---

## Expected Dashboard Behavior

### When Working Correctly:

1. **Local Access:**
   - ✅ `http://localhost:5000` → Shows dashboard
   - ✅ `http://localhost:5000/api/data` → Returns JSON stats

2. **Network Access:**
   - ✅ `http://192.168.1.100:5000` → Shows dashboard from other devices

3. **Stats Display:**
   - Shows current request count
   - Shows success rate
   - Shows recent users (if any)
   - Updates in real-time as bot processes requests

4. **Live Stats Widget:**
   - Fetches data from `/api/data` endpoint
   - Updates automatically
   - Shows "running" status

### If Stats Show Zeros:

This is **normal** if:
- Weather bot just started
- No one has used the bot yet
- Stats were recently reset

Stats will populate as people use the bot to request weather information.

---

## Advanced Troubleshooting

### Run Dashboard Manually (For Debugging)

```bash
# Stop the service first
sudo systemctl stop mcwb-dashboard

# Run manually to see errors
cd ~/MCWB
python3 web_dashboard.py --host 0.0.0.0 --port 5000 --debug

# This will show detailed error messages
# Press Ctrl+C to stop when done
# Then restart the service:
sudo systemctl start mcwb-dashboard
```

### Check Python Dependencies

```bash
# Verify all dependencies are installed
cd ~/MCWB
pip3 install -r requirements.txt

# Test imports
python3 -c "from flask import Flask; print('Flask: OK')"
python3 -c "from flask_cors import CORS; print('CORS: OK')"
python3 -c "from stats_tracker import StatsTracker; print('StatsTracker: OK')"
```

### View Live Logs

```bash
# Watch dashboard logs in real-time
sudo journalctl -u mcwb-dashboard -f

# Watch weather bot logs
sudo journalctl -u weather-bot -f
```

---

## Summary

**The quick fix script should resolve both issues:**

1. **Dashboard Connection** → Ensures service is running and accessible
2. **Stats Display** → Verifies stats files exist and are valid

**Run on your Pi:**
```bash
cd ~/MCWB
./fix_dashboard_connection_and_stats.sh
```

**After running the script, the dashboard should be accessible at:**
- Local: `http://localhost:5000`
- Network: `http://YOUR_PI_IP:5000`

**Stats API endpoint:**
- `http://YOUR_PI_IP:5000/api/data`

If the automated script doesn't work, follow the manual diagnostic steps above and check the service logs for specific error messages.

---

## Need More Help?

If you're still having issues after running the script:

1. **Capture diagnostic info:**
   ```bash
   sudo systemctl status mcwb-dashboard > ~/dashboard-status.txt
   sudo journalctl -u mcwb-dashboard -n 100 > ~/dashboard-logs.txt
   curl -v http://localhost:5000 > ~/curl-test.txt 2>&1
   ls -lah ~/MCWB/logs/ > ~/logs-status.txt
   ```

2. **Check the output files:**
   ```bash
   cat ~/dashboard-status.txt
   cat ~/dashboard-logs.txt
   cat ~/curl-test.txt
   cat ~/logs-status.txt
   ```

3. **Look for specific errors:**
   - "ModuleNotFoundError" → Install dependencies
   - "Permission denied" → Fix file permissions
   - "Address already in use" → Port conflict
   - "Connection refused" → Service not running

4. **Open a GitHub issue** with the output from the diagnostic files
