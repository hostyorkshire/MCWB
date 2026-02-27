# Quick Start: Cloudflare Tunnel for weather.example.com

This is a quick reference guide for setting up and using the Cloudflare Tunnel integration.

## Prerequisites

- Raspberry Pi with bot running at 192.168.1.100:5000
- Cloudflare account (free)
- Domain registered with Cloudflare
- Access to cPanel for weather.example.com

## Installation (5 minutes)

### On Raspberry Pi (192.168.1.100)

```bash
cd ~/MCWB
./install_cloudflare_tunnel.sh
```

**What the script does:**
1. Installs cloudflared (auto-detects your architecture)
2. Opens browser for Cloudflare authentication
3. Creates tunnel named `mcwb-dashboard-[hostname]`
4. Generates configuration file
5. Sets up systemd service for auto-start
6. Asks for domain/subdomain for DNS routing

**You'll need:**
- Cloudflare login credentials
- A subdomain choice (e.g., `mcwb-dashboard.yourdomain.com`)

**Result:**
- Tunnel URL: `https://your-subdomain.yourdomain.com`
- Service running: `cloudflared-mcwb.service`
- Auto-starts on boot

## Configuration (2 minutes)

### Update Static Website

**File to edit:** `public_html/wx/js/dashboard.js`

**Line 18:** Set your tunnel URL

```javascript
const TUNNEL_URL = 'https://your-subdomain.yourdomain.com';
```

**Example:**
```javascript
const TUNNEL_URL = 'https://mcwb-dashboard.example.com';
```

### Deploy to cPanel

**Method 1: File Manager**
1. Login to cPanel
2. Go to File Manager
3. Navigate to `public_html/wx/js/` (or wherever weather.example.com is located)
4. Upload `dashboard.js`
5. Overwrite existing file

**Method 2: FTP**
```bash
# Using your FTP client
ftp.intergalactic.it.com
Upload to: public_html/wx/js/dashboard.js
```

## Testing

### 1. Test Tunnel Directly

```bash
# From any computer/phone
curl https://your-subdomain.yourdomain.com/api/status
```

**Expected:** JSON response with bot status

### 2. Test Website

Visit: `https://weather.example.com/dashboard.html`

**Expected:** Green banner saying "Live Dashboard Connected"

### 3. Verify Data

Check that:
- Status shows "Online"
- Request counts are real (not demo data like "42")
- Active channels show actual channel names
- Logs show real bot activity

## Troubleshooting

### Issue: Website still shows demo data

**Check 1:** TUNNEL_URL is set correctly
```bash
# View your website's JS file
curl https://weather.example.com/js/dashboard.js | grep TUNNEL_URL
```

**Check 2:** Clear browser cache
- `Ctrl+Shift+Delete` (Windows/Linux)
- `Cmd+Shift+Delete` (Mac)
- Or use incognito mode

**Check 3:** Verify tunnel is running
```bash
# On Raspberry Pi
sudo systemctl status cloudflared-mcwb.service
```

### Issue: 502 Bad Gateway

Dashboard is not running:
```bash
# On Raspberry Pi
sudo systemctl status mcwb-dashboard.service
sudo systemctl start mcwb-dashboard.service
```

### Issue: CORS errors

```bash
# Restart dashboard to reload CORS config
sudo systemctl restart mcwb-dashboard.service
```

### Issue: Tunnel disconnects

```bash
# Check logs
sudo journalctl -u cloudflared-mcwb.service -n 50

# Restart tunnel
sudo systemctl restart cloudflared-mcwb.service
```

## Common Commands

### Manage Tunnel

```bash
# Status
sudo systemctl status cloudflared-mcwb.service

# Start
sudo systemctl start cloudflared-mcwb.service

# Stop
sudo systemctl stop cloudflared-mcwb.service

# Restart
sudo systemctl restart cloudflared-mcwb.service

# Logs (live)
sudo journalctl -u cloudflared-mcwb.service -f

# Logs (recent)
sudo journalctl -u cloudflared-mcwb.service -n 100
```

### Manage Dashboard

```bash
# Status
sudo systemctl status mcwb-dashboard.service

# Restart
sudo systemctl restart mcwb-dashboard.service

# Logs
sudo journalctl -u mcwb-dashboard.service -f
```

### Cloudflare Tunnel Commands

```bash
# List all tunnels
cloudflared tunnel list

# Tunnel info
cloudflared tunnel info mcwb-dashboard

# Delete tunnel (if needed)
cloudflared tunnel delete mcwb-dashboard
```

## Configuration Files

### Tunnel Config
**Location:** `~/.cloudflared/config.yml`

```yaml
tunnel: <tunnel-id>
credentials-file: ~/.cloudflared/<tunnel-id>.json

ingress:
  - service: http://localhost:5000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
  - service: http_status:404
```

### Website Config
**Location:** `public_html/wx/js/dashboard.js` (line 18)

```javascript
const TUNNEL_URL = 'https://your-tunnel-url.com';
const LOCAL_URL = 'http://192.168.1.100:5000';
```

**How it works:**
1. If TUNNEL_URL is set → use tunnel
2. Else if on local network → use LOCAL_URL
3. Else → demo mode

## Security Notes

### What's Protected
- ✅ All traffic encrypted with HTTPS
- ✅ Valid SSL certificate (Cloudflare)
- ✅ Local IP (192.168.1.100) never exposed
- ✅ No inbound firewall ports needed
- ✅ DDoS protection from Cloudflare

### What's NOT Protected
- ⚠️ Dashboard has no authentication
- ⚠️ Anyone with URL can access
- ⚠️ Consider using obscure subdomain

### Recommended: Add Authentication

**Option 1: Obscure Subdomain** (Easy)
```
✅ Good: mcwb-db-x8k2m4p.yourdomain.com
❌ Bad:  dashboard.yourdomain.com
```

**Option 2: Cloudflare Access** (Best)
1. Go to Cloudflare Dashboard
2. Zero Trust → Access → Applications
3. Add your tunnel URL
4. Configure authentication (email, Google, etc.)
5. Free for up to 50 users

## Updating Configuration

### Change Tunnel URL

**Step 1:** Create new DNS route
```bash
cloudflared tunnel route dns mcwb-dashboard new-subdomain.yourdomain.com
```

**Step 2:** Update website config
Edit `dashboard.js`, line 18:
```javascript
const TUNNEL_URL = 'https://new-subdomain.yourdomain.com';
```

**Step 3:** Upload to cPanel
Upload the updated `dashboard.js` file

**Step 4:** Clear browser cache

### Update Dashboard IP

If bot moves to different IP (not 192.168.1.100):

**File:** `public_html/wx/js/dashboard.js` (line 21)
```javascript
const LOCAL_URL = 'http://NEW_IP:5000';
```

No need to update tunnel config - it uses localhost.

## Getting Help

### Documentation
- [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md) - Full guide
- [CPANEL_DEPLOYMENT_GUIDE.md](CPANEL_DEPLOYMENT_GUIDE.md) - Detailed cPanel instructions
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical overview

### Common Questions

**Q: Do I need to renew the tunnel?**
A: No, tunnel credentials don't expire

**Q: What if my IP changes?**
A: Tunnel still works - it connects outbound from Pi

**Q: Can I use multiple subdomains?**
A: Yes, create multiple DNS routes for same tunnel

**Q: Does this work with dynamic IP?**
A: Yes! That's one of the benefits - no DDNS needed

**Q: Can others see my local IP?**
A: No, it's hidden behind Cloudflare's network

**Q: What about data usage?**
A: Minimal - only API calls, not full page loads

## Success Checklist

- [ ] Tunnel installed and running
- [ ] Service enabled for auto-start
- [ ] Tunnel URL obtained
- [ ] dashboard.js updated with tunnel URL
- [ ] File uploaded to cPanel
- [ ] Website visited and shows live data
- [ ] Browser cache cleared if needed
- [ ] Green "Live Dashboard Connected" banner visible

## That's It!

Your static website at **weather.example.com** is now displaying live data from your bot at **192.168.1.100** through a secure Cloudflare Tunnel.

**No port forwarding. No exposed IPs. Just works.** 🎉
