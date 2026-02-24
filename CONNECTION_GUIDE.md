# Simple Connection Guide

**Can't connect to your Web Dashboard?** This guide will get you connected in 5 minutes.

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
