# HTTPS Setup Guide for MCWB Dashboard

This guide explains how to set up HTTPS for the MCWB Dashboard running on a Raspberry Pi, allowing secure connections from the Netlify-hosted static website.

## Why HTTPS?

When the static website is hosted on HTTPS (like Netlify), browsers block HTTP API requests due to "mixed content" security restrictions. To connect from HTTPS to your Raspberry Pi dashboard, the dashboard must also use HTTPS.

## Quick Start

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

This installs `cryptography` needed for certificate generation.

### 2. Generate SSL Certificate

Run the certificate generation script:

```bash
python3 generate_ssl_cert.py --hostname 192.168.1.109
```

Replace `192.168.1.109` with your Raspberry Pi's actual IP address.

This creates two files:
- `cert.pem` - SSL certificate (public)
- `key.pem` - Private key (keep secure!)

### 3. Start Dashboard with HTTPS

```bash
python3 web_dashboard.py --host 0.0.0.0 --ssl
```

The dashboard will now be accessible at:
- `https://192.168.1.109:5000` (from network)
- `https://localhost:5000` (from Pi itself)

## Browser Security Warnings

Since we're using a self-signed certificate, browsers will show a security warning. This is **normal and safe** for local network use.

### How to Proceed Past the Warning

**Chrome/Edge:**
1. Click "Advanced"
2. Click "Proceed to 192.168.1.109 (unsafe)"

**Firefox:**
1. Click "Advanced"
2. Click "Accept the Risk and Continue"

**Safari:**
1. Click "Show Details"
2. Click "visit this website"

## Advanced Options

### Custom Certificate Location

```bash
python3 web_dashboard.py --ssl --cert /path/to/cert.pem --key /path/to/key.pem
```

### Different Port

```bash
python3 web_dashboard.py --ssl --port 8443
```

### Localhost Only (for testing)

```bash
python3 web_dashboard.py --ssl --host 127.0.0.1
```

## Production Alternatives

For production use or external access, consider these alternatives to self-signed certificates:

### Option 1: Cloudflare Tunnel (Recommended)
- Free, secure external access
- No port forwarding needed
- Automatic HTTPS with valid certificates
- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

### Option 2: ngrok
- Temporary external access
- Valid HTTPS certificate
- Easy setup: `ngrok http 5000`
- [ngrok Documentation](https://ngrok.com/docs)

### Option 3: Reverse Proxy with Let's Encrypt
- Use Caddy or nginx
- Free valid certificates from Let's Encrypt
- Requires domain name
- Example with Caddy:

```bash
# Install Caddy
sudo apt install caddy

# Configure Caddy (edit /etc/caddy/Caddyfile)
your-domain.com {
    reverse_proxy localhost:5000
}

# Restart Caddy
sudo systemctl restart caddy
```

## Troubleshooting

### Certificate Not Found Error

If you see "SSL certificate files not found":
1. Run `python3 generate_ssl_cert.py` first
2. Make sure `cert.pem` and `key.pem` exist in the same directory
3. Or specify custom paths with `--cert` and `--key`

### Connection Refused

- Ensure firewall allows port 5000: `sudo ufw allow 5000`
- Check the dashboard is running: `ps aux | grep web_dashboard`
- Verify the IP address: `hostname -I`

### Browser Still Shows "Not Secure"

This is normal with self-signed certificates. The connection is still encrypted, just not verified by a Certificate Authority.

### CORS Errors

The dashboard already has CORS enabled. If you still see CORS errors:
1. Make sure you're using HTTPS (not HTTP)
2. Clear browser cache
3. Try incognito/private mode

## Security Notes

**Self-Signed Certificates:**
- ✅ Encrypt traffic on your local network
- ✅ Safe for home/private network use
- ❌ Not verified by Certificate Authority
- ❌ Will show browser warnings

**Certificate Files:**
- `cert.pem` - Can be shared (public certificate)
- `key.pem` - **KEEP SECRET** (private key)
- Valid for 1 year, then regenerate

**Network Security:**
- Only run on trusted networks (home/office)
- Don't expose directly to the internet without proper security
- Consider using a VPN for remote access
- Use Cloudflare Tunnel or ngrok for external access

## Updating the Static Website

If you change your Raspberry Pi's IP address, update the hardcoded URL in `website/js/dashboard.js`:

```javascript
const HARDCODED_API_URL = 'https://YOUR_NEW_IP:5000';
```

Then commit and push the changes to update the Netlify site.
