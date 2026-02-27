# Deploying Live Dashboard to wx.intergalactic.it.com

Quick guide for connecting the static website at **wx.intergalactic.it.com** to your bot running on **192.168.1.109**.

## Overview

```
Static Website                Cloudflare            Raspberry Pi
(wx.intergalactic.it.com) →  (Tunnel) →  (192.168.1.109:5000)
[cPanel Hosting]                          [Local Bot Dashboard]
```

## Step 1: Set Up Cloudflare Tunnel (One Time)

On your Raspberry Pi where the bot runs:

```bash
cd ~/MCWB
./install_cloudflare_tunnel.sh
```

**During setup:**
1. You'll authenticate with Cloudflare (free account)
2. Choose a subdomain for your tunnel (e.g., `mcwb-dashboard.yourdomain.com`)
3. The script will give you a tunnel URL

**Save this URL** - you'll need it for the next step!

Example tunnel URL: `https://mcwb-dashboard.yourdomain.com`

## Step 2: Update Website Configuration

### Edit the JavaScript Configuration

1. **Download the file from your repository:**
   ```bash
   # On your development machine
   # Adjust path if your repo is installed elsewhere
   cd ~/MCWB/public_html/wx/js
   nano dashboard.js  # or use your preferred editor
   ```

2. **Find this line (around line 15):**
   ```javascript
   const TUNNEL_URL = ''; // Set your Cloudflare Tunnel URL here
   ```

3. **Update it with your tunnel URL:**
   ```javascript
   const TUNNEL_URL = 'https://mcwb-dashboard.yourdomain.com';
   ```

4. **Save the file**

### Upload to cPanel

**Option A: Using cPanel File Manager**

1. Log in to cPanel: https://intergalactic.it.com/cpanel (or your cPanel URL)
2. Navigate to **File Manager**
3. Go to the directory where `wx.intergalactic.it.com` is hosted
   - Usually `public_html/wx/` or `public_html/wx.intergalactic.it.com/`
4. Navigate to `js/` folder
5. Click **Upload**
6. Upload the modified `dashboard.js` file
7. When prompted, choose to **overwrite** the existing file

**Option B: Using FTP/SFTP**

```bash
# Using FileZilla, Cyberduck, or command-line FTP
# Connect to: ftp.intergalactic.it.com
# Username: your-cpanel-username
# Password: your-cpanel-password

# Upload to: public_html/wx/js/dashboard.js
```

**Option C: Using Git (if cPanel has Git integration)**

```bash
# Commit your changes
git add public_html/wx/js/dashboard.js
git commit -m "Configure Cloudflare Tunnel URL for live dashboard"
git push

# Then deploy via cPanel's Git integration
# (if you have this set up)
```

## Step 3: Test the Connection

1. **Clear your browser cache:**
   - Chrome/Edge: `Ctrl+Shift+Delete` → Clear cached images and files
   - Firefox: `Ctrl+Shift+Delete` → Cache
   - Safari: `Cmd+Option+E`

2. **Visit your dashboard:**
   ```
   https://wx.intergalactic.it.com/dashboard.html
   ```

3. **Check for live connection:**
   - You should see a **green banner** saying "Live Dashboard Connected"
   - The banner will show your API URL
   - Data should be real (not demo data)

4. **If still showing demo mode:**
   - Open browser console (F12)
   - Look for error messages
   - Common issues:
     - CORS errors → Check CORS config in web_dashboard.py
     - Connection refused → Verify tunnel is running
     - Wrong URL → Double-check the TUNNEL_URL in dashboard.js

## Troubleshooting

### Problem: Still Shows Demo Data

**Check 1: Verify tunnel is running**
```bash
# On Raspberry Pi
sudo systemctl status cloudflared-mcwb.service

# Should show "active (running)"
```

**Check 2: Test tunnel directly**
```bash
# From any computer
curl https://mcwb-dashboard.yourdomain.com/api/status

# Should return JSON with bot status
```

**Check 3: Verify dashboard.js was uploaded**
```bash
# From browser, visit:
https://wx.intergalactic.it.com/js/dashboard.js

# Press Ctrl+F and search for your tunnel URL
# It should be there on line 15
```

**Check 4: Clear cache again**
- Use incognito/private browsing mode
- Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)

### Problem: CORS Errors in Browser Console

The web dashboard is already configured to allow requests from `wx.intergalactic.it.com`.

If you see CORS errors:

1. **Check the error message** - it will tell you which origin is being blocked

2. **Verify dashboard is using HTTPS tunnel URL:**
   ```javascript
   // Should be HTTPS, not HTTP
   const TUNNEL_URL = 'https://mcwb-dashboard.yourdomain.com';
   ```

3. **Restart the dashboard** (if you modified CORS settings):
   ```bash
   sudo systemctl restart mcwb-dashboard.service
   ```

### Problem: 502 Bad Gateway

This means the tunnel is working but can't reach the dashboard.

```bash
# Check dashboard is running
sudo systemctl status mcwb-dashboard.service
sudo systemctl start mcwb-dashboard.service

# Check it's on port 5000
netstat -tlnp | grep 5000
```

### Problem: Tunnel Won't Start

```bash
# Check tunnel logs
sudo journalctl -u cloudflared-mcwb.service -n 50

# Common issues:
# - Wrong tunnel ID in config.yml
# - Dashboard not running
# - Network connectivity issues
```

## Maintenance

### Restarting Services

```bash
# Restart dashboard
sudo systemctl restart mcwb-dashboard.service

# Restart tunnel
sudo systemctl restart cloudflared-mcwb.service

# Check both are running
sudo systemctl status mcwb-dashboard.service
sudo systemctl status cloudflared-mcwb.service
```

### Updating the Tunnel URL

If you need to change the tunnel URL:

1. **On Raspberry Pi:** Reconfigure the tunnel
   ```bash
   cloudflared tunnel route dns mcwb-dashboard new-subdomain.yourdomain.com
   ```

2. **In cPanel:** Update `dashboard.js` with new URL

3. **Clear cache** and reload website

### Monitoring

**Check tunnel status:**
```bash
cloudflared tunnel list
cloudflared tunnel info mcwb-dashboard
```

**View live logs:**
```bash
# Dashboard logs
sudo journalctl -u mcwb-dashboard.service -f

# Tunnel logs
sudo journalctl -u cloudflared-mcwb.service -f
```

## Security Notes

### Current Setup
- ✅ Traffic encrypted via HTTPS (Cloudflare provides valid SSL certificate)
- ✅ Local IP (192.168.1.109) never exposed publicly
- ✅ No inbound ports opened on your router
- ✅ CORS configured to allow wx.intergalactic.it.com
- ⚠️ Dashboard has no authentication (anyone with URL can access)

### Recommendations

1. **Use a non-obvious tunnel URL:**
   ```
   ✅ Good: mcwb-db-x8k2m4p.yourdomain.com
   ❌ Bad:  dashboard.yourdomain.com
   ```

2. **Add Cloudflare Access** (optional, for authentication):
   - Go to Cloudflare Dashboard → Zero Trust → Access
   - Create application for your tunnel URL
   - Add authentication (email, Google, etc.)
   - Free for up to 50 users

3. **Monitor access logs regularly:**
   ```bash
   sudo journalctl -u cloudflared-mcwb.service | grep -i "request"
   ```

4. **Keep software updated:**
   ```bash
   # Update cloudflared
   cd ~/MCWB
   ./install_cloudflare_tunnel.sh  # Reinstall latest version
   ```

## Quick Reference

| Task | Command |
|------|---------|
| Check tunnel status | `sudo systemctl status cloudflared-mcwb.service` |
| Check dashboard status | `sudo systemctl status mcwb-dashboard.service` |
| View tunnel logs | `sudo journalctl -u cloudflared-mcwb.service -f` |
| View dashboard logs | `sudo journalctl -u mcwb-dashboard.service -f` |
| Restart tunnel | `sudo systemctl restart cloudflared-mcwb.service` |
| Restart dashboard | `sudo systemctl restart mcwb-dashboard.service` |
| Test tunnel URL | `curl https://your-tunnel-url/api/status` |
| List all tunnels | `cloudflared tunnel list` |

## Getting Help

If you're still having issues:

1. **Gather information:**
   ```bash
   # System info
   uname -a
   cloudflared --version
   
   # Service status
   sudo systemctl status cloudflared-mcwb.service
   sudo systemctl status mcwb-dashboard.service
   
   # Recent logs
   sudo journalctl -u cloudflared-mcwb.service -n 50
   sudo journalctl -u mcwb-dashboard.service -n 50
   ```

2. **Check documentation:**
   - [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md) - Full tunnel guide
   - [WEB_DASHBOARD.md](WEB_DASHBOARD.md) - Dashboard setup
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General troubleshooting

3. **Open an issue** on GitHub with the information above

## Summary

✅ **What we accomplished:**
- Installed Cloudflare Tunnel on Raspberry Pi (192.168.1.109)
- Created secure HTTPS endpoint for your bot dashboard
- Updated wx.intergalactic.it.com to display live data
- No port forwarding or router configuration needed

✅ **Your users can now:**
- Visit https://wx.intergalactic.it.com/dashboard.html
- See real-time bot data from anywhere in the world
- View statistics, logs, and active channels
- Access securely via HTTPS with valid certificate

🎉 **Your static website is now connected to your local bot!**
