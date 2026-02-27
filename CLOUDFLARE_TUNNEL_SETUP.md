# Cloudflare Tunnel Setup Guide

Connect your locally-running MCWB Dashboard (on 192.168.1.109) to your static website hosted on cPanel without port forwarding or exposing your local IP address.

## 🎯 What is Cloudflare Tunnel?

Cloudflare Tunnel creates a secure, encrypted connection from your Raspberry Pi to Cloudflare's network without opening any inbound ports on your firewall. Your static website can then connect to the dashboard through Cloudflare's global network.

### Benefits

- ✅ **No Port Forwarding** - Works without router configuration
- ✅ **No Dynamic DNS** - No need to track your changing IP address
- ✅ **Free SSL/TLS** - Automatic HTTPS with valid certificates
- ✅ **DDoS Protection** - Cloudflare's network protects your dashboard
- ✅ **Global CDN** - Fast access from anywhere in the world
- ✅ **Private Network** - Your local IP (192.168.1.109) stays private

### How It Works

```
Static Website (cPanel)  →  Cloudflare Network  →  Cloudflared Daemon  →  Dashboard (192.168.1.109:5000)
```

1. **cloudflared** daemon runs on your Raspberry Pi and creates an outbound tunnel to Cloudflare
2. Cloudflare assigns you a public URL (e.g., `dashboard.yourdomain.com`)
3. Your static website makes API calls to this public URL
4. Cloudflare routes requests through the tunnel to your local dashboard
5. Responses travel back through the same secure tunnel

## 📋 Prerequisites

### Required

1. **Cloudflare Account** (free)
   - Sign up at: https://dash.cloudflare.com/sign-up
   - No credit card required for free plan

2. **Domain Name** registered with Cloudflare
   - Option A: Use an existing domain (transfer to Cloudflare)
   - Option B: Register a new domain and add to Cloudflare
   - Option C: Use a free subdomain service like FreeDNS.afraid.org

3. **Running Dashboard** on your Raspberry Pi
   - Dashboard should be accessible at `http://192.168.1.109:5000`
   - See [WEB_DASHBOARD.md](WEB_DASHBOARD.md) for setup

### Recommended

- Static IP reservation for your Raspberry Pi (192.168.1.109)
- Dashboard running as a systemd service for auto-start

## 🚀 Quick Start (Automated Installation)

The easiest way to set up Cloudflare Tunnel:

```bash
cd ~/MCWB
./install_cloudflare_tunnel.sh
```

The script will:
1. Download and install `cloudflared` for your system architecture
2. Authenticate with your Cloudflare account (opens browser)
3. Create a tunnel named `mcwb-dashboard-[hostname]`
4. Generate tunnel configuration
5. Set up systemd service for auto-start on boot
6. Create DNS route (optional)
7. Start the tunnel

### What You'll Need During Installation

- **Cloudflare Account** - Have your login credentials ready
- **Domain Name** - Know your domain (e.g., `yourdomain.com`)
- **Subdomain Choice** - Pick a subdomain (e.g., `dashboard.yourdomain.com`)

## 📖 Manual Installation (Step-by-Step)

If you prefer to install manually or the script doesn't work for your system:

### Step 1: Install cloudflared

#### Raspberry Pi (ARM64/ARM)

```bash
# For Raspberry Pi 4/5 (64-bit)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
sudo mv cloudflared-linux-arm64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared

# For older Raspberry Pi (32-bit ARM)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm
sudo mv cloudflared-linux-arm /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared
```

#### Other Linux Systems

```bash
# AMD64/x86_64
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared
```

#### Verify Installation

```bash
cloudflared --version
```

### Step 2: Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This will:
1. Open your browser
2. Prompt you to log in to Cloudflare
3. Ask you to select a domain
4. Save authentication credentials to `~/.cloudflared/cert.pem`

### Step 3: Create a Tunnel

```bash
cloudflared tunnel create mcwb-dashboard
```

This creates a tunnel and saves its credentials to `~/.cloudflared/[tunnel-id].json`

**Note the Tunnel ID** displayed - you'll need it for configuration.

### Step 4: Create Configuration File

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: YOUR_TUNNEL_ID_HERE
credentials-file: /home/pi/.cloudflared/YOUR_TUNNEL_ID_HERE.json

ingress:
  # Route all traffic to local dashboard
  - service: http://localhost:5000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
  # Required catch-all rule
  - service: http_status:404
```

**Important:** Replace:
- `YOUR_TUNNEL_ID_HERE` with your actual tunnel ID
- `/home/pi/` with your actual home directory if different

### Step 5: Create DNS Route

Route a subdomain to your tunnel:

```bash
cloudflared tunnel route dns mcwb-dashboard dashboard.yourdomain.com
```

Replace `dashboard.yourdomain.com` with your chosen subdomain.

### Step 6: Run the Tunnel (Testing)

Test the tunnel before setting up the service:

```bash
cloudflared tunnel run mcwb-dashboard
```

Open your browser and visit: `https://dashboard.yourdomain.com`

You should see your dashboard! Press `Ctrl+C` to stop when testing is done.

### Step 7: Set Up Systemd Service

Create `/etc/systemd/system/cloudflared-mcwb.service`:

```ini
[Unit]
Description=Cloudflare Tunnel for MCWB Dashboard
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/local/bin/cloudflared tunnel --config /home/pi/.cloudflared/config.yml run
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Important:** Update the `User=` and config path if needed.

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudflared-mcwb.service
sudo systemctl start cloudflared-mcwb.service
sudo systemctl status cloudflared-mcwb.service
```

### Step 8: Verify It's Working

1. **Check tunnel status:**
   ```bash
   cloudflared tunnel list
   cloudflared tunnel info mcwb-dashboard
   ```

2. **Check service status:**
   ```bash
   sudo systemctl status cloudflared-mcwb.service
   ```

3. **Test the URL:**
   ```bash
   curl https://dashboard.yourdomain.com/api/status
   ```

4. **Open in browser:**
   ```
   https://dashboard.yourdomain.com
   ```

## 🌐 Update Your Static Website

Once your tunnel is running, update your static website to use the new URL.

### For Your cPanel-Hosted Site (wx.intergalactic.it.com)

Your static website is hosted at **wx.intergalactic.it.com** on cPanel. After setting up the Cloudflare Tunnel, you need to update the website to point to your tunnel URL.

### Option 1: Hardcode the URL (Simple)

Edit `public_html/wx/js/dashboard.js`:

```javascript
// Configuration for Cloudflare Tunnel
// Replace with your actual tunnel URL after setup
const TUNNEL_URL = 'https://mcwb-dashboard.yourdomain.com';

// Remove or comment out the local URL
// const LOCAL_URL = 'http://192.168.1.109:5000';
```

**Example tunnel URLs you might use:**
- `https://mcwb.yourdomain.com`
- `https://dashboard.yourdomain.com`
- `https://weather-bot-api.yourdomain.com`

**Note:** The domain must be registered with Cloudflare (free account works).

### Option 2: Auto-Detect with Fallback (Recommended)

This allows your site to work both locally and remotely:

```javascript
// Try Cloudflare Tunnel first, fallback to local
const TUNNEL_URL = 'https://mcwb-dashboard.yourdomain.com';  // Your tunnel URL
const LOCAL_URL = 'http://192.168.1.109:5000';

/**
 * Get the API URL to use for dashboard connections
 * Priority: Tunnel URL > Local URL > Demo Mode
 */
function getApiUrl() {
    // If tunnel URL is configured, use it
    if (TUNNEL_URL && TUNNEL_URL.trim() !== '') {
        return TUNNEL_URL;
    }
    
    // If we're on local network, try local URL
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || 
        hostname.startsWith('192.168.') || 
        hostname.startsWith('10.') ||
        hostname.startsWith('172.')) {
        return LOCAL_URL;
    }
    
    // No live URL configured - demo mode
    return null;
}

const API_URL = getApiUrl();
```

### Deploy Changes to cPanel

After updating the configuration:

1. **Upload to cPanel:**
   - Log in to your cPanel account
   - Navigate to File Manager
   - Go to the directory where wx.intergalactic.it.com is hosted
   - Upload the modified `js/dashboard.js` file
   - Overwrite the existing file

2. **Verify the upload:**
   - Visit https://wx.intergalactic.it.com/dashboard.html
   - Open browser console (F12) and check for connection messages
   - You should see "Connected to live dashboard" if successful

3. **Clear browser cache:**
   ```
   Ctrl+Shift+Delete (Windows/Linux)
   Cmd+Shift+Delete (Mac)
   ```
   Or use incognito/private mode to test

### Deploy Changes via FTP (Alternative)

If you prefer FTP:

```bash
# Example using lftp
lftp -u your-username ftp.intergalactic.it.com
cd public_html/wx  # Or wherever wx.intergalactic.it.com is hosted
put public_html/wx/js/dashboard.js
quit
```

## 🔧 Managing Your Tunnel

### Check Tunnel Status

```bash
# List all tunnels
cloudflared tunnel list

# Get tunnel details
cloudflared tunnel info mcwb-dashboard

# Check service status
sudo systemctl status cloudflared-mcwb.service

# View live logs
sudo journalctl -u cloudflared-mcwb.service -f
```

### Control the Service

```bash
# Start tunnel
sudo systemctl start cloudflared-mcwb.service

# Stop tunnel
sudo systemctl stop cloudflared-mcwb.service

# Restart tunnel
sudo systemctl restart cloudflared-mcwb.service

# Disable auto-start
sudo systemctl disable cloudflared-mcwb.service

# Enable auto-start
sudo systemctl enable cloudflared-mcwb.service
```

### Update cloudflared

```bash
# Download latest version
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
sudo mv cloudflared-linux-arm64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared

# Restart service
sudo systemctl restart cloudflared-mcwb.service

# Verify new version
cloudflared --version
```

## 🔒 Security Considerations

### What's Protected

- ✅ Your local IP address (192.168.1.109) is never exposed
- ✅ All traffic is encrypted with TLS
- ✅ No inbound firewall ports needed
- ✅ Cloudflare provides DDoS protection
- ✅ Invalid certificates are rejected

### What's NOT Protected

- ⚠️ The dashboard itself has no authentication
- ⚠️ Anyone with the URL can access your dashboard
- ⚠️ API endpoints are publicly accessible

### Recommended Security Measures

1. **Use a Hard-to-Guess Subdomain**
   ```
   ✅ Good: mcwb-db-8x9k2m4p.yourdomain.com
   ❌ Bad:  dashboard.yourdomain.com
   ```

2. **Add Cloudflare Access (Optional)**
   
   Cloudflare Access can add authentication to your tunnel:
   
   - Go to Cloudflare Dashboard
   - Navigate to Zero Trust → Access → Applications
   - Create a new application for your dashboard URL
   - Configure authentication (email OTP, Google, etc.)
   - Free for up to 50 users

3. **Limit Exposure**
   
   Only share the URL with people who need it. Consider:
   - Using a password manager to store the URL securely
   - Rotating the subdomain periodically
   - Setting up Cloudflare Access for team access

4. **Monitor Access**
   
   Check tunnel logs regularly:
   ```bash
   sudo journalctl -u cloudflared-mcwb.service -n 100
   ```

5. **Dashboard Security Settings**
   
   The dashboard already implements:
   - CORS headers to restrict API access
   - Input validation on all endpoints
   - No sensitive data exposure in logs

## 🐛 Troubleshooting

### Tunnel Won't Start

**Problem:** Service fails to start

```bash
sudo systemctl status cloudflared-mcwb.service
sudo journalctl -u cloudflared-mcwb.service -n 50
```

**Common causes:**
1. **Wrong tunnel ID** - Check config.yml has correct tunnel ID
2. **Wrong credentials path** - Verify credentials-file path exists
3. **Dashboard not running** - Start dashboard first
4. **Port conflict** - Check nothing else using port 5000

### DNS Not Resolving

**Problem:** `dashboard.yourdomain.com` doesn't resolve

**Solution:**
```bash
# Check DNS route exists
cloudflared tunnel route dns list

# If missing, add it
cloudflared tunnel route dns mcwb-dashboard dashboard.yourdomain.com

# Wait 5-10 minutes for DNS propagation
```

### 502 Bad Gateway Error

**Problem:** Tunnel works but shows 502 error

**Causes:**
1. **Dashboard not running**
   ```bash
   sudo systemctl status mcwb-dashboard.service
   sudo systemctl start mcwb-dashboard.service
   ```

2. **Wrong port in config**
   - Check config.yml has `http://localhost:5000`
   - Verify dashboard is on port 5000: `netstat -tlnp | grep 5000`

3. **Firewall blocking localhost**
   ```bash
   # Should not be needed, but try:
   sudo ufw allow from 127.0.0.1 to any port 5000
   ```

### CORS Errors from Website

**Problem:** Browser console shows CORS errors

**Solution:**

The dashboard already has CORS enabled. If you still see errors:

1. **Check browser console** for exact error
2. **Verify URL is HTTPS** (not HTTP)
3. **Clear browser cache** and try incognito mode
4. **Check dashboard CORS config** in web_dashboard.py (line 58)

If problems persist, you may need to update the CORS config:

```python
# In web_dashboard.py, update line 58:
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://yourdomain.com",
            "https://dashboard.yourdomain.com",
            "*"  # Allow all (less secure but simpler)
        ]
    }
})
```

### Tunnel Disconnects Frequently

**Problem:** Tunnel keeps disconnecting

**Causes:**
1. **Network instability** - Check internet connection
2. **Resource constraints** - Raspberry Pi running out of memory
3. **Cloudflare issues** - Check status.cloudflare.com

**Solutions:**
```bash
# Increase restart delay in service file
sudo nano /etc/systemd/system/cloudflared-mcwb.service

# Change RestartSec=10 to RestartSec=30
RestartSec=30

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart cloudflared-mcwb.service
```

### Can't Authenticate with Cloudflare

**Problem:** `cloudflared tunnel login` fails

**Solutions:**
1. **Check internet connection**
2. **Try different browser** - Firefox/Chrome/Safari
3. **Disable VPN** temporarily during authentication
4. **Check Cloudflare status** at status.cloudflare.com

### Dashboard Loads But Shows Demo Data

**Problem:** Website shows "Demo Dashboard" warning

This means the website is not connecting to your tunnel.

**Solutions:**
1. **Verify tunnel URL** in public_html/wx/js/dashboard.js
2. **Check tunnel is running**
   ```bash
   sudo systemctl status cloudflared-mcwb.service
   ```
3. **Test API directly**
   ```bash
   curl https://dashboard.yourdomain.com/api/status
   ```
4. **Check browser console** for errors (F12)

## 📚 Additional Resources

### Cloudflare Documentation
- [Cloudflare Tunnel Overview](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Tunnel Configuration Reference](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/configuration/)
- [Tunnel Commands](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/)

### Related Guides
- [WEB_DASHBOARD.md](WEB_DASHBOARD.md) - Dashboard setup and features
- [HTTPS_SETUP.md](HTTPS_SETUP.md) - Alternative: Self-signed certificates
- [SSH_REMOTE_ACCESS.md](SSH_REMOTE_ACCESS.md) - SSH access methods

### Alternative Solutions

If Cloudflare Tunnel doesn't work for you:

1. **ngrok** - Similar to Cloudflare Tunnel, easier setup but less features
2. **DDNS + Port Forwarding** - Traditional approach, requires router access
3. **VPN** - Most secure but more complex setup
4. **Reverse SSH Tunnel** - Good for SSH access, less good for web services

## 🆘 Getting Help

If you're stuck:

1. **Check the logs**
   ```bash
   sudo journalctl -u cloudflared-mcwb.service -n 100
   sudo journalctl -u mcwb-dashboard.service -n 100
   ```

2. **Test each component**
   ```bash
   # Test dashboard locally
   curl http://localhost:5000/api/status
   
   # Test tunnel connectivity
   cloudflared tunnel info mcwb-dashboard
   
   # Test DNS resolution
   nslookup dashboard.yourdomain.com
   ```

3. **Open an issue** on GitHub with:
   - Your system info (Pi model, OS version)
   - cloudflared version
   - Service logs
   - Error messages

## 📝 Summary

**What we accomplished:**
- ✅ Installed cloudflared on your Raspberry Pi
- ✅ Created a secure tunnel to Cloudflare
- ✅ Configured DNS to point to your tunnel
- ✅ Set up auto-start on boot
- ✅ Updated static website to use tunnel URL

**Your dashboard is now accessible:**
- 🌍 From anywhere in the world
- 🔒 With valid HTTPS certificate
- 🛡️ Behind Cloudflare's DDoS protection
- 🚫 Without exposing your local network

**Next steps:**
- Share the URL with your team
- Consider adding Cloudflare Access for authentication
- Monitor the tunnel logs periodically
- Keep cloudflared updated
