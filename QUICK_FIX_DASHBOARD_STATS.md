# Quick Start: Fix Your Dashboard Issues

## What This PR Includes

### 1. Code Quality Fixes ✅
- Fixed duplicate imports and whitespace in web_dashboard.py
- All code passes linting and security scans
- Repository is healthy

### 2. Dashboard Connection & Stats Fix 🔧

**Your Issues:**
- ❌ Cannot connect to dashboard locally  
- ❌ Stats not displaying on live stats page
- ✅ SSH is working

**Solution:**

SSH into your Raspberry Pi and run ONE command:

```bash
cd ~/MCWB && ./fix_dashboard_connection_and_stats.sh
```

This script will automatically:
1. Check if dashboard service is running
2. Fix connectivity issues
3. Repair or create missing stats files
4. Fix file permissions
5. Configure firewall if needed
6. Restart the service
7. Verify everything works

**Expected Result:**
- ✅ Dashboard accessible at `http://YOUR_PI_IP:5000`
- ✅ Stats displaying correctly
- ✅ Live stats widget working

---

## What The Script Does

The automated fix script (`fix_dashboard_connection_and_stats.sh`) performs:

### Step 1: Service Check
- Verifies dashboard service is installed
- Checks if service is running
- Starts service if not running
- Shows logs if service fails to start

### Step 2: Connectivity Tests
- Tests localhost connection (`http://localhost:5000`)
- Tests network connection (`http://YOUR_IP:5000`)
- Identifies connection failures
- Suggests fixes for each issue type

### Step 3: Firewall Check
- Checks if firewall is blocking port 5000
- Offers to automatically allow port 5000
- Verifies firewall configuration

### Step 4: Stats Files Validation
- Checks if `logs/stats.json` exists
- Validates JSON format
- Creates/repairs file if missing or corrupted
- Checks if `logs/channels.json` exists
- Validates and repairs channels file
- Fixes file permissions

### Step 5: Service Restart
- Restarts dashboard with all fixes applied
- Waits for service to stabilize
- Verifies service is responding

### Step 6: Final Verification
- Tests complete connectivity
- Shows all access URLs
- Provides stats API endpoint
- Confirms everything is working

---

## If The Script Doesn't Work

See the comprehensive guide: `DASHBOARD_STATS_FIX_GUIDE.md`

It includes:
- Manual diagnostic steps
- Common issues and solutions
- Advanced troubleshooting
- How to check logs
- How to run dashboard manually for debugging

---

## Quick Verification

After running the script, verify it worked:

```bash
# Check service is running
sudo systemctl status mcwb-dashboard

# Test local connection
curl http://localhost:5000/api/data

# Get your IP
hostname -I

# Open in browser (replace with your IP)
http://192.168.1.100:5000
```

---

## Common Issues The Script Fixes

✅ **Service not running** → Starts the service  
✅ **Service crashed** → Restarts with fixes  
✅ **Port blocked by firewall** → Opens port 5000  
✅ **Missing stats.json** → Creates with proper structure  
✅ **Corrupted stats.json** → Backs up and recreates  
✅ **Missing channels.json** → Creates with proper structure  
✅ **Permission errors** → Fixes file ownership and permissions  
✅ **Network access blocked** → Verifies 0.0.0.0 binding  

---

## Why Stats Might Show Zeros

Stats showing zero is **normal** if:
- Dashboard just started
- No one has used the weather bot yet
- Stats were recently reset

Stats will populate as people use the bot to request weather.

To verify the bot is running:
```bash
sudo systemctl status weather-bot
```

---

## Files Added in This PR

1. **fix_dashboard_connection_and_stats.sh** - Automated fix script
2. **DASHBOARD_STATS_FIX_GUIDE.md** - Comprehensive troubleshooting guide  
3. **GIT_CORRUPTION_FIX.md** - Guide to fix Git corruption on Pi
4. **THIS_FILE.md** - Quick start summary

Plus code quality improvements in `web_dashboard.py`

---

## Support

If you still have issues after running the script:

1. Capture diagnostic info:
```bash
sudo systemctl status mcwb-dashboard > ~/dashboard-status.txt
sudo journalctl -u mcwb-dashboard -n 100 > ~/dashboard-logs.txt
cat ~/dashboard-logs.txt
```

2. Check for specific errors in the logs
3. Refer to `DASHBOARD_STATS_FIX_GUIDE.md` for solutions
4. Open a GitHub issue with the diagnostic output

---

## Bottom Line

**To fix your dashboard connection and stats display issues:**

```bash
cd ~/MCWB
./fix_dashboard_connection_and_stats.sh
```

**That's it!** The script handles everything automatically.

Dashboard will be accessible at: `http://YOUR_PI_IP:5000`
