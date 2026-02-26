# SSH Remote Access Guide for Raspberry Pi Weather Bot

This guide explains how to securely access your Raspberry Pi Weather Bot via SSH when it's deployed in a remote location.

## Overview

When the bot is running in a remote location (e.g., a field site, remote station, or another building), you'll need reliable remote access to:
- ✅ Monitor bot status and logs
- ✅ Update the bot software
- ✅ Troubleshoot issues
- ✅ Adjust configuration
- ✅ Perform system maintenance

This guide covers multiple approaches, from simple to advanced, so you can choose the solution that best fits your needs.

## Table of Contents

1. [Security First: SSH Key Authentication](#security-first-ssh-key-authentication)
2. [Method 1: Direct Access on Local Network](#method-1-direct-access-on-local-network)
3. [Method 2: Port Forwarding (Router Configuration)](#method-2-port-forwarding-router-configuration)
4. [Method 3: Dynamic DNS for Changing IP Addresses](#method-3-dynamic-dns-for-changing-ip-addresses)
5. [Method 4: VPN Solutions (Recommended)](#method-4-vpn-solutions-recommended)
6. [Method 5: Reverse SSH Tunnel](#method-5-reverse-ssh-tunnel)
7. [Mobile SSH Clients](#mobile-ssh-clients)
8. [Troubleshooting Remote SSH](#troubleshooting-remote-ssh)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Security First: SSH Key Authentication

**Before setting up remote access, secure your SSH connection with key-based authentication.**

### Why SSH Keys?

- 🔒 **More secure** than passwords (resistant to brute-force attacks)
- 🚀 **More convenient** (no password typing)
- 🛡️ **Can disable password authentication** entirely

### Step 1: Generate SSH Key Pair (On Your Computer)

```bash
# On your local computer (not the Pi)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Or if ed25519 is not supported, use RSA:
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# When prompted:
# - Press Enter to save to default location (~/.ssh/id_ed25519)
# - Enter a strong passphrase (optional but recommended)
```

### Step 2: Copy Public Key to Raspberry Pi

```bash
# Method 1: Using ssh-copy-id (easiest)
ssh-copy-id pi@raspberrypi.local

# Method 2: Manual copy
cat ~/.ssh/id_ed25519.pub | ssh pi@raspberrypi.local 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'

# Method 3: If you can't connect yet, copy to SD card
# Mount the Pi's SD card on your computer and add your public key to:
# /home/pi/.ssh/authorized_keys
```

### Step 3: Test Key-Based Login

```bash
# Try logging in - should not ask for password
ssh pi@raspberrypi.local

# If it works, you're authenticated with your key!
```

### Step 4: Disable Password Authentication (Optional but Recommended)

Once key authentication works:

```bash
# On the Raspberry Pi
sudo nano /etc/ssh/sshd_config

# Change or add these lines:
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no

# Save and restart SSH service
sudo systemctl restart ssh
```

**Warning:** Make sure key authentication works before disabling passwords, or you could lock yourself out!

### Step 5: Additional SSH Hardening

```bash
# On the Raspberry Pi, edit SSH config
sudo nano /etc/ssh/sshd_config

# Recommended changes:
PermitRootLogin no                    # Disable root login
MaxAuthTries 3                        # Limit authentication attempts
ClientAliveInterval 300               # Keep connections alive (5 minutes)
ClientAliveCountMax 2                 # Disconnect after 2 missed keepalives

# Optional: Change SSH port (reduces automated attacks)
Port 2222                             # Use a non-standard port

# Restart SSH service
sudo systemctl restart ssh
```

If you change the SSH port, remember to use it when connecting:
```bash
ssh -p 2222 pi@raspberrypi.local
```

---

## Method 1: Direct Access on Local Network

**Best for:** Bot on the same network as you.

### Finding Your Pi's IP Address

```bash
# Option 1: Use hostname (if mDNS works)
ssh pi@raspberrypi.local

# Option 2: Find IP from your router's DHCP client list
# Check your router's admin page (usually 192.168.1.1 or 192.168.0.1)

# Option 3: Scan the network (on your computer)
# Install nmap: sudo apt install nmap (Linux) or brew install nmap (Mac)
nmap -sn 192.168.1.0/24

# Option 4: Check from the Pi itself (if you have physical access)
hostname -I
```

### Setting a Static IP (Recommended)

To prevent the IP from changing:

```bash
# On the Raspberry Pi
sudo nano /etc/dhcpcd.conf

# Add at the end (adjust for your network):
interface wlan0  # or eth0 for Ethernet
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8

# Save and reboot
sudo reboot
```

After reboot:
```bash
ssh pi@192.168.1.100
```

---

## Method 2: Port Forwarding (Router Configuration)

**Best for:** Accessing from outside your network with a static public IP.

**⚠️ Security Warning:** Exposing SSH directly to the internet increases security risks. Use strong authentication and consider Method 4 (VPN) instead.

### Step 1: Configure Port Forwarding on Your Router

1. **Log into your router** (usually http://192.168.1.1 or http://192.168.0.1)
2. **Find Port Forwarding settings** (may be under "Advanced" or "NAT")
3. **Add a new port forwarding rule:**
   - **Service Name:** SSH to Pi
   - **External Port:** 2222 (use non-standard port)
   - **Internal IP:** Your Pi's static IP (e.g., 192.168.1.100)
   - **Internal Port:** 22 (or your custom SSH port)
   - **Protocol:** TCP

### Step 2: Find Your Public IP Address

```bash
# From any device on your network
curl ifconfig.me
# or visit: https://whatismyipaddress.com/
```

### Step 3: Connect from Outside

```bash
# From anywhere on the internet
ssh -p 2222 pi@YOUR_PUBLIC_IP

# Example:
ssh -p 2222 pi@203.0.113.42
```

### Security Enhancements for Port Forwarding

1. **Use a non-standard port** (not 22) to reduce automated attacks
2. **Enable fail2ban** to block repeated failed login attempts:
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

3. **Set up firewall rules:**
   ```bash
   sudo apt install ufw
   sudo ufw allow 2222/tcp  # Your SSH port
   sudo ufw enable
   ```

4. **Monitor login attempts:**
   ```bash
   # View authentication log
   sudo tail -f /var/log/auth.log
   ```

---

## Method 3: Dynamic DNS for Changing IP Addresses

**Best for:** Home internet with dynamic (changing) public IP addresses.

Most residential internet connections have dynamic IPs that change periodically. Dynamic DNS (DDNS) gives you a permanent hostname that automatically updates when your IP changes.

### Popular Free DDNS Services

- **No-IP** (noip.com) - Free tier available
- **DuckDNS** (duckdns.org) - Free, simple, privacy-focused
- **Dynu** (dynu.com) - Free tier available

### Example: Setting Up DuckDNS

**Step 1: Register for DuckDNS**
1. Go to https://www.duckdns.org/
2. Log in (via GitHub, Google, etc.)
3. Create a subdomain (e.g., `myweatherbot.duckdns.org`)
4. Note your token

**Step 2: Install DuckDNS Client on Pi**

```bash
# Create directory
mkdir -p ~/duckdns
cd ~/duckdns

# Create update script
cat > duck.sh << 'EOF'
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=YOUR_DOMAIN&token=YOUR_TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
EOF

# Make it executable
chmod +x duck.sh

# Test it
./duck.sh
cat duck.log  # Should show "OK"
```

**Step 3: Set Up Auto-Update with Cron**

```bash
# Edit crontab
crontab -e

# Add this line (updates every 5 minutes):
*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

**Step 4: Connect Using DDNS Hostname**

```bash
# Now you can use your DDNS hostname instead of IP
ssh -p 2222 pi@myweatherbot.duckdns.org
```

---

## Method 4: VPN Solutions (Recommended)

**Best for:** Most secure and reliable remote access.

A VPN creates an encrypted tunnel, making it appear as if you're on the same local network as your Pi.

### Option A: Tailscale (Easiest, Recommended)

Tailscale is a zero-configuration VPN that creates a secure mesh network.

**Advantages:**
- ✅ No port forwarding needed
- ✅ No dynamic DNS needed
- ✅ Works behind NAT and firewalls
- ✅ End-to-end encrypted
- ✅ Free for personal use (up to 100 devices)
- ✅ Cross-platform (Linux, Mac, Windows, iOS, Android)

**Setup:**

```bash
# On the Raspberry Pi
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Follow the URL to authenticate
# Note the Pi's Tailscale IP (e.g., 100.x.x.x)

# On your local computer
# Install Tailscale from https://tailscale.com/download
# Log in with the same account

# Connect to your Pi using its Tailscale IP
ssh pi@100.x.x.x
```

**No router configuration needed!** Tailscale handles NAT traversal automatically.

### Option B: WireGuard (More Control)

WireGuard is a modern, fast VPN protocol.

**Setup (Basic):**

```bash
# On the Raspberry Pi
sudo apt install wireguard

# Generate keys
wg genkey | tee privatekey | wg pubkey > publickey

# Configure WireGuard
sudo nano /etc/wireguard/wg0.conf
```

Example configuration:
```ini
[Interface]
PrivateKey = YOUR_PRIVATE_KEY
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
PublicKey = CLIENT_PUBLIC_KEY
AllowedIPs = 10.0.0.2/32
```

```bash
# Enable and start WireGuard
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
```

For detailed WireGuard setup, see: https://www.wireguard.com/quickstart/

### Option C: OpenVPN (Traditional)

OpenVPN is the classic VPN solution, very mature and well-documented.

**Quick setup using PiVPN:**
```bash
# On the Raspberry Pi
curl -L https://install.pivpn.io | bash

# Follow the interactive setup wizard
# Choose WireGuard or OpenVPN
```

PiVPN simplifies OpenVPN/WireGuard setup with a user-friendly script.

---

## Method 5: Reverse SSH Tunnel

**Best for:** Situations where you can't configure the remote network's router (e.g., locked down corporate network, restrictive ISP).

A reverse SSH tunnel connects outbound from the Pi to a server you control, then you connect to that server to reach the Pi.

**Requirements:**
- A VPS or server with a public IP that you control (e.g., DigitalOcean, AWS, Linode)

**Setup:**

**Step 1: On Your VPS (Server)**
```bash
# Edit SSH config to allow port forwarding
sudo nano /etc/ssh/sshd_config

# Add or uncomment:
GatewayPorts yes

# Restart SSH
sudo systemctl restart ssh
```

**Step 2: On Raspberry Pi**
```bash
# Create reverse SSH tunnel to your VPS
ssh -R 2222:localhost:22 user@your-vps.com -N

# Explanation:
# -R 2222:localhost:22 - Forward VPS port 2222 to Pi's SSH port 22
# -N - Don't execute commands, just forward
# user@your-vps.com - Your VPS login
```

**Step 3: Keep Tunnel Running with autossh**
```bash
# Install autossh on Raspberry Pi
sudo apt install autossh

# Create systemd service for persistent tunnel
sudo nano /etc/systemd/system/reverse-tunnel.service
```

Add:
```ini
[Unit]
Description=Reverse SSH Tunnel
After=network-online.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/autossh -M 0 -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -N -R 2222:localhost:22 user@your-vps.com
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

> **⚠️ NOTE:** When creating the service file, ensure you type or paste the content correctly. Do not copy from a web browser's rendered view, as HTML entities (like `&gt;` or `&lt;`) may corrupt the file. The section headers must be exactly `[Unit]`, `[Service]`, and `[Install]` with proper square brackets.

```bash
# Enable and start the service
sudo systemctl enable reverse-tunnel
sudo systemctl start reverse-tunnel
```

**Step 4: Connect via VPS**
```bash
# SSH to your VPS
ssh user@your-vps.com

# From VPS, SSH to Pi through the tunnel
ssh -p 2222 pi@localhost
```

---

## Mobile SSH Clients

Access your Pi from your phone or tablet:

### iOS Apps
- **Termius** (Free, feature-rich, supports key authentication)
- **Blink Shell** (Paid, professional-grade)
- **Secure ShellFish** (Free, integrates with Files app)

### Android Apps
- **Termux** (Free, full terminal emulator)
- **JuiceSSH** (Free, user-friendly)
- **Termius** (Free, cross-platform)

### Example: Setting Up Termius

1. **Install Termius** from App Store or Google Play
2. **Add Host:**
   - Alias: Weather Bot Pi
   - Hostname: Your Pi's address (IP, DDNS hostname, or Tailscale IP)
   - Username: pi
   - Port: 22 (or your custom port)
3. **Add SSH Key** (optional):
   - Import your private key or generate new key in app
4. **Connect:** Tap the host to connect

---

## Troubleshooting Remote SSH

### Connection Refused

```bash
# Check if SSH service is running on Pi
sudo systemctl status ssh

# Check if firewall is blocking
sudo ufw status

# Check if SSH is listening
sudo netstat -tlnp | grep ssh
```

### Connection Times Out

**Possible causes:**
1. **Router not forwarding:** Check port forwarding rules
2. **ISP blocking:** Some ISPs block inbound port 22
3. **Firewall blocking:** Check firewall on both sides
4. **Wrong IP/port:** Verify public IP hasn't changed

**Test connectivity:**
```bash
# From outside, test if port is open
nc -zv YOUR_PUBLIC_IP 2222

# Or use online tool: https://www.yougetsignal.com/tools/open-ports/
```

### Connection Drops Frequently

Add keepalive settings to your SSH config:

**On your local computer:**
```bash
# Edit ~/.ssh/config
nano ~/.ssh/config

# Add:
Host raspberrypi
    HostName YOUR_PI_ADDRESS
    User pi
    Port 2222
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### Can't Find Pi on Network

```bash
# Scan for Pi on network
nmap -sn 192.168.1.0/24

# Look for "Raspberry Pi Foundation" in MAC vendor
```

### Permission Denied (Public Key)

```bash
# On Pi, check file permissions
ls -la ~/.ssh/
# Should be: drwx------ (700) for .ssh directory
#           -rw------- (600) for authorized_keys

# Fix permissions if needed
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Check authorized_keys content
cat ~/.ssh/authorized_keys
# Should contain your public key
```

### SSH Key Issues

```bash
# On your computer, check which key is being used
ssh -v pi@YOUR_PI_ADDRESS
# Look for "Offering public key" messages

# Specify key explicitly
ssh -i ~/.ssh/id_ed25519 pi@YOUR_PI_ADDRESS
```

---

## Monitoring and Maintenance

### Check Bot Status Remotely

```bash
# Connect via SSH, then:

# Check service status
sudo systemctl status weather_bot

# View live logs
sudo journalctl -u weather_bot -f

# View recent logs
sudo journalctl -u weather_bot -n 100

# Check system resources
top
htop  # If installed

# Check USB device
ls -l /dev/ttyUSB* /dev/ttyACM*
```

### Remote Bot Management

```bash
# Restart the bot
sudo systemctl restart weather_bot

# Stop the bot
sudo systemctl stop weather_bot

# Start the bot
sudo systemctl start weather_bot

# Update bot code
cd /home/pi/MCWB
git pull
sudo systemctl restart weather_bot

# View logs with custom script
cd /home/pi/MCWB
python3 viewlogs.py
```

### System Updates

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Update bot dependencies
cd /home/pi/MCWB
pip3 install -r requirements.txt --upgrade

# Check disk space
df -h

# Check memory usage
free -h
```

### Setting Up Email Alerts

Get notified if the Pi goes offline:

```bash
# Install ssmtp for email alerts
sudo apt install ssmtp

# Configure with your email provider
sudo nano /etc/ssmtp/ssmtp.conf
```

Example configuration for Gmail:
```ini
root=your_email@gmail.com
mailhub=smtp.gmail.com:587
AuthUser=your_email@gmail.com
AuthPass=your_app_password
UseSTARTTLS=YES
```

Create a monitoring script:
```bash
nano ~/check_bot.sh
```

```bash
#!/bin/bash
if ! systemctl is-active --quiet weather_bot; then
    echo "Weather bot is down!" | mail -s "Alert: Bot Down" your_email@gmail.com
fi
```

```bash
chmod +x ~/check_bot.sh

# Add to crontab (check every 10 minutes)
crontab -e
# Add:
*/10 * * * * /home/pi/check_bot.sh
```

---

## Comparison of Methods

| Method | Difficulty | Security | Cost | Best For |
|--------|-----------|----------|------|----------|
| Local Network | Easy | High | Free | Same network access |
| Port Forwarding | Medium | Medium | Free | Static IP, direct access |
| Dynamic DNS | Medium | Medium | Free | Changing IP address |
| Tailscale VPN | Easy | Very High | Free | Best overall solution |
| WireGuard VPN | Hard | Very High | Free | Advanced users |
| OpenVPN | Medium | Very High | Free | Traditional VPN |
| Reverse Tunnel | Hard | High | VPS cost | Restrictive networks |

**Recommendation:** For most users, **Tailscale** offers the best combination of ease, security, and reliability.

---

## Security Best Practices Summary

✅ **Do:**
- Use SSH key authentication
- Disable password authentication
- Use non-standard SSH ports
- Keep system updated
- Use fail2ban to block attacks
- Use a VPN when possible
- Monitor logs regularly
- Use strong passphrases

❌ **Don't:**
- Use default passwords
- Expose SSH on port 22 to internet
- Share private keys
- Ignore security updates
- Use weak or reused passwords
- Trust unknown networks

---

## Quick Reference Commands

```bash
# Connect to Pi
ssh pi@raspberrypi.local              # Local network
ssh pi@YOUR_PUBLIC_IP -p 2222         # Port forwarding
ssh pi@DDNS_HOSTNAME -p 2222          # Dynamic DNS
ssh pi@TAILSCALE_IP                   # Tailscale VPN

# Check bot status
sudo systemctl status weather_bot

# View logs
sudo journalctl -u weather_bot -f

# Restart bot
sudo systemctl restart weather_bot

# Update bot
cd /home/pi/MCWB && git pull && sudo systemctl restart weather_bot

# Test SSH connectivity
nc -zv HOST PORT                      # From outside
```

---

## Additional Resources

- [Raspberry Pi Official SSH Documentation](https://www.raspberrypi.org/documentation/remote-access/ssh/)
- [SSH Key Authentication Guide](https://www.ssh.com/academy/ssh/keygen)
- [Tailscale Documentation](https://tailscale.com/kb/)
- [WireGuard Quick Start](https://www.wireguard.com/quickstart/)
- [fail2ban Documentation](https://www.fail2ban.org/wiki/index.php/Main_Page)

---

## Related Documentation

- [Raspberry Pi Setup Guide](RASPBERRY_PI_SETUP.md) - Initial Pi setup and bot installation
- [Main README](README.md) - Full bot documentation
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- [Quick Start Guide](QUICKSTART.md) - Getting started quickly

---

## Support

If you encounter issues with remote SSH access:

1. **Check this troubleshooting section first**
2. **Review your network/router configuration**
3. **Check the Pi's system logs:** `sudo journalctl -n 100`
4. **Verify SSH service status:** `sudo systemctl status ssh`
5. **Test local connectivity first** before attempting remote access
6. **Open a GitHub issue** with details about your setup and error messages

Remember: Remote access issues are often network-related rather than bot-related. Focus troubleshooting on SSH connectivity first.
