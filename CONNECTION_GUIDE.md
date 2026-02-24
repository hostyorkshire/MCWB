# Simple Connection Guide

**Can't connect to your Web Dashboard?** This guide will get you connected in 5 minutes.

## 🎛️ NEW: Unified Service Manager

**The easiest way to set up everything:**

```bash
cd ~/MCWB
./setup_mcwb.sh
```

Choose option **2** (Install Web Dashboard) or **3** (Install BOTH services).

The menu will:
- ✅ Guide you through installation
- ✅ Configure firewall if needed
- ✅ Show you the connection URL
- ✅ Start services automatically

---

## Alternative: Direct Installation

If you prefer to use the installation script directly:

## Step 1: Install the Dashboard Service

Open a terminal on your Raspberry Pi and run:

```bash
cd ~/MCWB
./install_dashboard_service.sh
```

**What does this do?**
- Configures the dashboard to start automatically when your Pi boots
- Configures your firewall (if you have one)
- Shows you the connection URL

**Example output:**
```
✅ Service is running!

🌐 Web Dashboard Access:
   Network: http://192.168.1.109:5000
```

Write down that URL! That's where you'll connect.

## Step 2: Open the Dashboard

On any device connected to the same network (laptop, phone, tablet):

1. Open a web browser
2. Type the URL from Step 1 (e.g., `http://192.168.1.109:5000`)
3. Done! You should see the dashboard

### Bonus: Connect Your Static Website

If you've deployed the MCWB static website (from the `website/` folder), you can connect it to your live dashboard:

1. Go to your static website's Live Dashboard page
2. Look for "Configure Custom API URL"
3. Enter the URL from Step 1 (e.g., `http://192.168.1.109:5000`)
4. Click "Connect"

Now your website will show **real-time live data** from your Raspberry Pi! 🎉

## Still Can't Connect?

### Common Issue: Dashboard Not Starting After Reboot

If your dashboard was working before but stopped working after rebooting your Pi, the service might be starting before the network is fully online.

**Quick Fix:**
```bash
cd ~/MCWB
./install_dashboard_service.sh
```

This will reinstall the service with the correct network timing configuration.

**What this fixes:** The updated service waits for the network to be fully online before starting the dashboard, ensuring it can bind to your network IP address properly.

### Check 1: Is the Service Running?

```bash
sudo systemctl status mcwb-dashboard
```

**Expected:** You should see `Active: active (running)` in green.

**If not active:** The service isn't running. Check the error message and logs:
```bash
sudo journalctl -u mcwb-dashboard -n 50
```

Common fix: Reinstall with `./install_dashboard_service.sh`

### Check 2: Can You Connect Locally?

On the Raspberry Pi, test if the dashboard responds:

```bash
curl http://localhost:5000
```

**Expected:** You should see HTML output starting with `<!DOCTYPE html>`

**If connection refused:** The dashboard isn't listening. Check service status (Check 1).

### Check 3: Is Your Firewall Blocking?

```bash
sudo ufw status
```

**If port 5000 is not listed:** Allow it through:
```bash
sudo ufw allow 5000/tcp
```

### Check 4: Do You Have the Right IP Address?

Your Pi's IP address might have changed. Check it:

```bash
hostname -I
```

Use the first IP address shown (e.g., `192.168.1.109`) in your browser.

**💡 Pro Tip:** Reserve a static IP for your Raspberry Pi in your router's DHCP settings. This way, the IP address won't change and you can always use the same URL (e.g., `http://192.168.1.109:5000`). This also makes the website integration more stable!

### Check 5: Are You on the Same Network?

The device you're connecting from (laptop/phone) must be on the **same local network** as the Raspberry Pi.

**Example:**
- ✅ Pi: 192.168.1.109, Laptop: 192.168.1.50 → Same network (192.168.1.x)
- ❌ Pi: 192.168.1.109, Laptop: 192.168.2.50 → Different networks

### Check 6: Verify Network Binding

Ensure the dashboard is bound to `0.0.0.0` (network accessible) not just `127.0.0.1` (localhost only):

```bash
sudo netstat -tlnp | grep :5000
```

**Expected:** You should see something like:
```
tcp        0      0 0.0.0.0:5000            0.0.0.0:*               LISTEN      1234/python3
```

**If you see 127.0.0.1:5000** instead of **0.0.0.0:5000**, the service is only listening locally.

**Fix:** Edit the service file to use `--host 0.0.0.0`:
```bash
sudo nano /etc/systemd/system/mcwb-dashboard.service
# Find the ExecStart line and ensure it has: --host 0.0.0.0
sudo systemctl daemon-reload
sudo systemctl restart mcwb-dashboard
```

Or reinstall:
```bash
cd ~/MCWB
./install_dashboard_service.sh
```

### Check 7: Test Python Dependencies

Verify Flask and dependencies are installed:

```bash
python3 -c "import flask, flask_cors; print('Dependencies OK')"
```

**If this fails:**
```bash
pip3 install --user -r requirements.txt
sudo systemctl restart mcwb-dashboard
```

### Check 8: Port Already in Use

Check if another process is using port 5000:

```bash
sudo lsof -i :5000
```

**If port is busy:** Either stop the other process or change the dashboard to use a different port.

### Check 9: View Service Logs in Real-Time

Watch the service logs to see what's happening:

```bash
sudo journalctl -u mcwb-dashboard -f
```

Look for error messages like:
- "ModuleNotFoundError" → Dependencies not installed
- "Permission denied" → User/directory mismatch
- "Address already in use" → Port conflict
- Any Python tracebacks or exceptions

Press Ctrl+C to stop viewing logs.

## Quick Reset (If All Else Fails)

Complete fresh install of the dashboard service:

```bash
# Stop and remove existing service
sudo systemctl stop mcwb-dashboard
sudo systemctl disable mcwb-dashboard
sudo rm /etc/systemd/system/mcwb-dashboard.service
sudo systemctl daemon-reload

# Reinstall dependencies
cd ~/MCWB
pip3 install --user -r requirements.txt

# Reinstall service (this will configure everything correctly)
./install_dashboard_service.sh
```

After installation, the script will show your connection URL. Wait 5 seconds after it starts, then test:
```bash
curl http://localhost:5000
```

You should see HTML output. If you do, try connecting from your browser again.

## Advanced: Manual Start (For Testing)

If you want to test the dashboard without installing the service:

```bash
cd ~/MCWB
python3 web_dashboard.py
```

The dashboard will display the connection URL when it starts. Press Ctrl+C to stop.

## Need More Help?

- Full documentation: [WEB_DASHBOARD.md](WEB_DASHBOARD.md)
- General troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Open an issue: https://github.com/hostyorkshire/MCWB/issues
