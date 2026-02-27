# Dashboard Connectivity Troubleshooting

## 🔓 First: Understand There's NO Login System

**The dashboard does NOT have any login, username, or password!** You simply open the URL in your browser and it loads instantly.

When people say "I cannot login," they actually mean "I cannot connect to" or "I cannot access" the dashboard. This is a **connectivity issue**, not a login issue.

---

## ⚡ Quick Fix: Dashboard Was Working Before But Stopped

**If your dashboard was working before (e.g., at http://192.168.1.100:5000) and suddenly stopped:**

### Option 1: Quick Fix Script (Fastest)
```bash
cd ~/MCWB
./fix_dashboard.sh
```

This script automatically:
- Checks if service is running and restarts if needed
- Detects common failures (dependencies, permissions, port conflicts)
- Gets you back online in under 30 seconds

### Option 2: Full Diagnostic (Comprehensive)
```bash
cd ~/MCWB
./diagnose_dashboard.sh
```

Runs 8 comprehensive checks:
1. Service installation status
2. Service enabled for boot
3. Service currently running
4. Local connectivity test
5. Network interface binding
6. Firewall configuration
7. Python dependencies
8. End-to-end connectivity test

Both scripts will automatically offer to fix issues they find.

---

## Issue: Cannot Access Dashboard at 192.168.1.100:5000

If you're unable to connect to your web dashboard, follow these diagnostic steps **in order**:

## 🚨 SSL/HTTPS Error in Browser

### Error: "SSL received a record that exceeded the maximum permissible length"

**This error means you're trying to use HTTPS to connect to an HTTP server!**

**Quick Fix:** Change your URL from `https://` to `http://`

❌ **Wrong:**  `https://192.168.1.100:5000`  
✅ **Correct:** `http://192.168.1.100:5000`

**Why this happens:**
- The dashboard runs in **HTTP mode** by default (not HTTPS/SSL)
- Some browsers may auto-complete or remember `https://` for an address
- If you previously visited the URL with HTTPS, the browser might cache it

**Solutions:**
1. **Use HTTP** - Type `http://192.168.1.100:5000` explicitly in the address bar
2. **Clear browser cache** - Clear cache/cookies for the IP address
3. **Try incognito/private mode** - This bypasses cached HTTPS redirects
4. **Enable HTTPS on server** - If you need HTTPS, see below

### To Enable HTTPS/SSL on the Dashboard

If you need HTTPS (for example, to connect from a Netlify-hosted website), follow these steps:

```bash
# 1. Generate SSL certificate (replace IP with yours)
cd ~/MCWB
python3 generate_ssl_cert.py --hostname 192.168.1.100

# 2. Update the service to use SSL
sudo nano /etc/systemd/system/mcwb-dashboard.service

# 3. Change the ExecStart line to add --ssl:
# From: ExecStart=... web_dashboard.py --host 0.0.0.0 --port 5000
# To:   ExecStart=... web_dashboard.py --host 0.0.0.0 --port 5000 --ssl

# 4. Reload and restart service
sudo systemctl daemon-reload
sudo systemctl restart mcwb-dashboard

# 5. Now connect with HTTPS
# https://192.168.1.100:5000
```

**Note:** Self-signed certificates will show a browser warning. Click "Advanced" → "Proceed" to continue.

---

## Quick Diagnostics (Run on Your Raspberry Pi)

```bash
# 1. Is the service running?
sudo systemctl status mcwb-dashboard

# 2. Can you connect locally on the Pi?
curl http://localhost:5000

# 3. What's your actual IP address?
hostname -I

# 4. Is the dashboard listening on the network?
sudo netstat -tlnp | grep :5000

# 5. Is the firewall blocking?
sudo ufw status

# 6. Check service logs for errors
sudo journalctl -u mcwb-dashboard -n 50
```

## Detailed Troubleshooting

### Problem 1: Service Not Running

**Check:**
```bash
sudo systemctl status mcwb-dashboard
```

**If NOT active (running):**
```bash
# Start the service
sudo systemctl start mcwb-dashboard

# If it still won't start, check logs
sudo journalctl -u mcwb-dashboard -n 100
```

**Common errors in logs:**
- `ModuleNotFoundError: No module named 'flask'` → Dependencies not installed
- `Permission denied` → User/path mismatch in service file
- `Address already in use` → Port 5000 is occupied

**Solution:**
```bash
cd ~/MCWB
# The automated installer handles dependencies and venv setup
./install_dashboard_service.sh
```

### Problem 2: Dependencies Not Installed

**Check:**
```bash
python3 -c "import flask, flask_cors; print('✅ OK')"
```

**If fails:**
```bash
cd ~/MCWB
# Create virtual environment if needed and install dependencies
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
./venv/bin/pip install -r requirements.txt
# Reinstall service to use the venv
./install_dashboard_service.sh
```

### Problem 3: Service Only Listening on Localhost

**Check:**
```bash
sudo netstat -tlnp | grep :5000
```

**Good:** `0.0.0.0:5000` - Accessible from network
**Bad:** `127.0.0.1:5000` - Localhost only

**Fix:**
```bash
# Check service configuration
cat /etc/systemd/system/mcwb-dashboard.service | grep ExecStart

# Should have: --host 0.0.0.0
# If it has: --host 127.0.0.1, then fix it:
sudo nano /etc/systemd/system/mcwb-dashboard.service
# Change to: --host 0.0.0.0
sudo systemctl daemon-reload
sudo systemctl restart mcwb-dashboard
```

Or reinstall:
```bash
cd ~/MCWB
./install_dashboard_service.sh
```

### Problem 4: IP Address Changed

**Check:**
```bash
hostname -I
```

Use the **first IP address** shown (e.g., `192.168.1.100`) in your browser.

**⭐ HIGHLY RECOMMENDED: Reserve a Static IP**

Prevent IP address changes by reserving a static IP in your router:

1. Access router admin panel (usually http://192.168.1.1 or http://192.168.0.1)
2. Navigate to DHCP Settings (look for "DHCP Reservation" or "Static DHCP")
3. Find your Raspberry Pi in the connected devices list
4. Reserve/assign the current IP address to this device permanently
5. Save and optionally reboot your Pi

**Common router locations:**
- **TP-Link:** Advanced → Network → DHCP Server → Address Reservation
- **Netgear:** Advanced → Setup → LAN Setup → Address Reservation
- **Asus:** LAN → DHCP Server → Manual Assignment
- **Linksys:** Connectivity → Local Network → DHCP Reservations

**Why reserve an IP:**
- Dashboard URL never changes - bookmark it once!
- Essential for website integration - set API URL once and forget
- Simplifies remote access, troubleshooting, and management
- No hunting for IP after router reboots

### Problem 5: Firewall Blocking Port

**Check:**
```bash
sudo ufw status
```

**If active and port 5000 not listed:**
```bash
sudo ufw allow 5000/tcp
sudo ufw reload
```

### Problem 6: Port Already in Use

**Check:**
```bash
sudo lsof -i :5000
```

**If another process is using port 5000:**
- Option A: Stop that process
- Option B: Change dashboard to different port:
  ```bash
  sudo nano /etc/systemd/system/mcwb-dashboard.service
  # Change --port 5000 to --port 5001
  sudo systemctl daemon-reload
  sudo systemctl restart mcwb-dashboard
  ```

### Problem 7: Service Configuration Mismatch

**Check:**
```bash
cat /etc/systemd/system/mcwb-dashboard.service
```

Verify:
- `User=` matches your username (check with `whoami`)
- `WorkingDirectory=` points to your MCWB directory (check with `pwd` from MCWB folder)
- `ExecStart=` has correct paths

**If mismatch:** Reinstall to auto-fix:
```bash
cd ~/MCWB
./install_dashboard_service.sh
```

## Nuclear Option: Complete Reset

If nothing above works, do a complete fresh install:

```bash
# 1. Stop and remove service
sudo systemctl stop mcwb-dashboard
sudo systemctl disable mcwb-dashboard
sudo rm /etc/systemd/system/mcwb-dashboard.service
sudo systemctl daemon-reload

# 2. Reinstall service (handles dependencies and venv automatically)
cd ~/MCWB
./install_dashboard_service.sh

# 4. Wait 5 seconds, then test
sleep 5
curl http://localhost:5000
```

## Manual Test (Bypass Service)

To test if the dashboard works at all, run it manually:

```bash
cd ~/MCWB
python3 web_dashboard.py --host 0.0.0.0 --port 5000
```

**If this works:** The problem is with the service configuration
**If this fails:** Check the error message for clues (likely dependencies)

## Verification Steps

After fixing, verify everything works:

```bash
# 1. Service is running
sudo systemctl status mcwb-dashboard | grep "Active: active"

# 2. Can connect locally
curl -s http://localhost:5000 | head -5

# 3. Listening on network
sudo netstat -tlnp | grep "0.0.0.0:5000"

# 4. IP address is correct
hostname -I

# 5. Test from another device (replace with your IP)
curl http://192.168.1.100:5000
```

## Still Not Working?

Check service logs for detailed error messages:

```bash
# View last 100 log entries
sudo journalctl -u mcwb-dashboard -n 100

# Or watch in real-time
sudo journalctl -u mcwb-dashboard -f
```

Look for:
- Python tracebacks
- Import errors
- Permission errors
- Network binding errors

## Getting Help

If you're still stuck, open an issue at https://github.com/hostyorkshire/MCWB/issues with:

1. Output of `sudo systemctl status mcwb-dashboard`
2. Output of `sudo journalctl -u mcwb-dashboard -n 100`
3. Output of `hostname -I`
4. Output of `python3 -c "import flask, flask_cors; print('OK')"`
5. Your Raspberry Pi model and OS version

---

## Frequently Asked Questions

### Q: Do I need to activate the virtual environment after each reboot?

**A: No!** If you installed the dashboard as a service (using `install_dashboard_service.sh`), the service is configured to use the virtual environment's Python interpreter automatically. 

The service runs on boot without any manual intervention. You never need to:
- Activate the venv manually
- Run `source venv/bin/activate`
- Restart the dashboard manually

**How it works:**
- The install script detects or creates a virtual environment
- It configures the systemd service to use the absolute path to the venv's Python (e.g., `/home/pi/MCWB/venv/bin/python3`)
- The service uses this path directly, so it always uses the venv's packages
- On every reboot, systemd starts the service automatically using the venv

**To verify your service is using the venv:**
```bash
# Check the service configuration
sudo systemctl cat mcwb-dashboard | grep ExecStart

# You should see something like:
# ExecStart=/home/pi/MCWB/venv/bin/python3 /home/pi/MCWB/web_dashboard.py ...
# (Not /usr/bin/python3)
```

### Q: What if I'm running manually (not as a service)?

If you start the dashboard manually with `python3 web_dashboard.py`, then yes, you need to activate the venv first:

```bash
cd ~/MCWB
source venv/bin/activate
python3 web_dashboard.py
```

**But for production use, install as a service instead** - it handles everything automatically.
