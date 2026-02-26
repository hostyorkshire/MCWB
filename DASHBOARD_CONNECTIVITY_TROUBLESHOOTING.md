# Dashboard Connectivity Troubleshooting

## Issue: Cannot Access Dashboard at 192.168.1.109:5000

If you're unable to connect to your web dashboard, follow these diagnostic steps **in order**:

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
pip3 install --user -r requirements.txt
sudo systemctl restart mcwb-dashboard
```

### Problem 2: Dependencies Not Installed

**Check:**
```bash
python3 -c "import flask, flask_cors; print('✅ OK')"
```

**If fails:**
```bash
pip3 install --user -r requirements.txt
sudo systemctl restart mcwb-dashboard
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

Use the **first IP address** shown (e.g., `192.168.1.109`) in your browser.

**Pro Tip:** Set a static IP in your router's DHCP settings to prevent this.

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

# 2. Reinstall dependencies
cd ~/MCWB
pip3 install --user -r requirements.txt

# 3. Reinstall service
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
curl http://192.168.1.109:5000
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
