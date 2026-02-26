# SSH Connection Troubleshooting Guide

## Problem: Cannot SSH into Raspberry Pi (But Ping Works)

If you can **ping** your Raspberry Pi but **cannot SSH** into it, this guide will help you diagnose and fix the issue.

### Symptoms

```bash
# Ping works:
$ ping 192.168.1.109
64 bytes from 192.168.1.109: icmp_seq=1 ttl=64 time=124 ms
^C

# But SSH fails:
$ ssh weatherbot@192.168.1.109
ssh: connect to host 192.168.1.109 port 22: Connection refused
# OR
ssh: connect to host 192.168.1.109 port 22: Connection timed out
# OR
ssh: connect to host 192.168.1.109 port 22: No route to host
```

---

## Quick Diagnosis

The fact that **ping works but SSH doesn't** typically means one of these issues:

| Issue | Likelihood | Fix Complexity |
|-------|-----------|---------------|
| **Firewall blocking SSH** | ⭐⭐⭐⭐⭐ Very High | ⭐ Easy |
| SSH service not running | ⭐⭐ Low | ⭐ Easy |
| SSH service misconfigured | ⭐⭐ Low | ⭐⭐ Medium |
| Wrong SSH port | ⭐ Very Low | ⭐ Easy |

---

## Fix #1: Firewall Blocking SSH (Most Common)

### Understanding the Problem

**Why does ping work but SSH doesn't?**

- **Ping** uses ICMP protocol which is typically NOT blocked by firewalls
- **SSH** uses TCP port 22 which MUST be explicitly allowed in firewall rules
- When UFW (Uncomplicated Firewall) is enabled without allowing SSH first, you get locked out

### How This Happens

This commonly occurs when following these steps **in the wrong order**:

```bash
# ❌ WRONG ORDER (locks you out):
sudo apt-get install ufw
sudo ufw enable              # Enables firewall first
sudo ufw allow 22/tcp        # Too late! You're already locked out

# ✅ CORRECT ORDER:
sudo apt-get install ufw
sudo ufw allow 22/tcp        # Allow SSH FIRST
sudo ufw enable              # Then enable firewall
```

### Solution: Fix from Physical Access

**If you have physical access to the Raspberry Pi** (keyboard and monitor connected):

#### Option A: Use the Fix Script (Easiest)

```bash
# Connect keyboard/monitor to your Pi, log in locally, then run:
cd ~/MCWB
./fix_ssh_access.sh
```

The script will:
- Check if firewall is blocking SSH
- Offer to fix it automatically
- Verify the fix

#### Option B: Manual Fix

```bash
# Check firewall status
sudo ufw status

# If it shows "Status: active" and SSH is not in the list:
sudo ufw allow 22/tcp
sudo ufw reload

# Verify SSH is now allowed:
sudo ufw status
# Should show: "22/tcp    ALLOW    Anywhere"
```

#### Option C: Disable Firewall (Quick but less secure)

```bash
# Temporarily disable the firewall to regain SSH access
sudo ufw disable

# Then SSH in remotely and properly configure it:
ssh user@192.168.1.109
sudo ufw allow 22/tcp
sudo ufw enable
```

### Solution: Fix Without Physical Access

If you **cannot physically access the Pi**, you have limited options:

1. **Use Alternative Access Methods:**
   - Serial console (if enabled)
   - VNC (if enabled)
   - Reverse SSH tunnel (if previously set up)
   - Tailscale or other VPN (if previously configured)

2. **Wait for Physical Access:**
   - The Pi will continue running normally
   - Once you have physical access, use the solutions above

3. **Reset the Pi** (last resort):
   - Remove SD card
   - Disable firewall by editing `/etc/ufw/ufw.conf` on the SD card
   - Change `ENABLED=yes` to `ENABLED=no`
   - Reinsert SD card and boot

---

## Fix #2: SSH Service Not Running

### Check SSH Service Status

If you have physical access:

```bash
# Check if SSH service is running
sudo systemctl status ssh

# If it's not running, start it:
sudo systemctl start ssh

# Enable it to start on boot:
sudo systemctl enable ssh
```

### Enable SSH on Raspberry Pi

If SSH was never enabled:

```bash
# Enable SSH using raspi-config
sudo raspi-config
# Navigate to: Interface Options -> SSH -> Enable

# Or enable directly:
sudo systemctl enable ssh
sudo systemctl start ssh
```

---

## Fix #3: Wrong SSH Port

If SSH is configured to use a non-standard port:

```bash
# Check SSH configuration
sudo grep "^Port" /etc/ssh/sshd_config

# If it shows a different port (e.g., 2222), connect with:
ssh -p 2222 user@192.168.1.109
```

---

## Fix #4: SSH Configuration Issues

### Check SSH Configuration

```bash
# Review SSH config
sudo nano /etc/ssh/sshd_config

# Ensure these settings allow connections:
PermitRootLogin no                    # For security (use your user account)
PubkeyAuthentication yes              # Allow SSH keys
PasswordAuthentication yes            # Allow passwords
ChallengeResponseAuthentication no

# After any changes, restart SSH:
sudo systemctl restart ssh
```

---

## Prevention: How to Avoid This Issue

### ✅ Always Allow SSH Before Enabling Firewall

When setting up a firewall, **ALWAYS** follow this order:

```bash
# 1. Install firewall
sudo apt-get install ufw

# 2. ALLOW SSH FIRST (before enabling)
sudo ufw allow 22/tcp

# 3. Allow other services you need
sudo ufw allow 5000/tcp  # Example: web dashboard

# 4. Enable firewall LAST
sudo ufw enable

# 5. Verify
sudo ufw status
```

### ✅ Use Our Setup Script

The `setup_mcwb.sh` script has safety checks:

```bash
./setup_mcwb.sh
# Choose option 8: Configure firewall
# The script will WARN you if SSH is not allowed before enabling
```

### ✅ Document Your Configuration

Keep notes of:
- Which ports you've opened
- Any SSH configuration changes
- Firewall rules you've added

---

## Testing SSH Access

### Test from Local Network

```bash
# Test SSH connection
ssh user@192.168.1.109

# Test with verbose output (for debugging)
ssh -v user@192.168.1.109

# Test specific port
ssh -p 22 user@192.168.1.109
```

### Test from Remote Network

If you've set up port forwarding or VPN:

```bash
# Via port forwarding
ssh -p 2222 user@YOUR_PUBLIC_IP

# Via Tailscale
ssh user@100.x.x.x

# Via DuckDNS
ssh user@yourbot.duckdns.org
```

---

## Common Error Messages Explained

| Error Message | Most Likely Cause | Fix |
|--------------|------------------|-----|
| `Connection refused` | SSH service not running OR firewall blocking | Check service status; check firewall |
| `Connection timed out` | Wrong IP address OR firewall blocking | Verify IP; check firewall |
| `No route to host` | Network issue OR firewall | Check network; check firewall |
| `Permission denied` | Wrong password OR SSH keys issue | Check credentials; check SSH config |
| `Host key verification failed` | SSH key changed (Pi was reinstalled) | Remove old key: `ssh-keygen -R 192.168.1.109` |

---

## Advanced Debugging

### Check Network Connectivity

```bash
# From another device on the same network:

# Test if port 22 is open (should return "Connected")
nc -zv 192.168.1.109 22

# Or use nmap
nmap -p 22 192.168.1.109
```

### Check from the Pi Itself

If you have physical access:

```bash
# Check if SSH is listening on port 22
sudo netstat -tlnp | grep :22

# Should show something like:
# tcp   0   0 0.0.0.0:22   0.0.0.0:*   LISTEN   1234/sshd

# Check SSH service logs
sudo journalctl -u ssh -n 50

# Check authentication logs
sudo tail -f /var/log/auth.log
```

---

## Quick Reference Commands

```bash
# Fix firewall blocking SSH:
sudo ufw allow 22/tcp && sudo ufw reload

# Check firewall status:
sudo ufw status verbose

# Disable firewall (temporary):
sudo ufw disable

# Check SSH service:
sudo systemctl status ssh

# Start SSH service:
sudo systemctl start ssh

# Check what's listening on port 22:
sudo netstat -tlnp | grep :22

# View SSH logs:
sudo journalctl -u ssh -n 50

# View authentication logs:
sudo tail -f /var/log/auth.log
```

---

## Still Having Issues?

1. **Run the diagnostic script:**
   ```bash
   cd ~/MCWB
   ./fix_ssh_access.sh
   ```

2. **Check all services:**
   ```bash
   sudo systemctl status ssh
   sudo ufw status
   sudo netstat -tlnp | grep :22
   ```

3. **Get detailed SSH connection info:**
   ```bash
   ssh -vvv user@192.168.1.109
   ```

4. **Review documentation:**
   - [SSH Remote Access Guide](SSH_REMOTE_ACCESS.md) - Comprehensive SSH setup
   - [Raspberry Pi Setup](RASPBERRY_PI_SETUP.md) - Initial Pi configuration
   - [Troubleshooting](TROUBLESHOOTING.md) - General troubleshooting

---

## Security Best Practices

Once SSH access is restored:

1. **Set up SSH key authentication** (more secure than passwords)
   ```bash
   # See SSH_REMOTE_ACCESS.md for detailed instructions
   ssh-keygen -t ed25519
   ssh-copy-id user@192.168.1.109
   ```

2. **Properly configure the firewall** (in the right order!)
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw enable
   ```

3. **Consider changing SSH port** (reduces automated attacks)
   ```bash
   # See SSH_REMOTE_ACCESS.md section on SSH hardening
   ```

4. **Monitor SSH attempts**
   ```bash
   sudo tail -f /var/log/auth.log
   ```

---

## Related Documentation

- **[SSH_REMOTE_ACCESS.md](SSH_REMOTE_ACCESS.md)** - Complete guide to secure remote SSH access
- **[RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)** - Initial Raspberry Pi setup instructions
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - General troubleshooting guide
- **[SETUP_MENU_GUIDE.md](SETUP_MENU_GUIDE.md)** - Using the setup menu system

---

**Remember:** The most common cause of "can ping but can't SSH" is **firewall blocking port 22**. Always allow SSH before enabling the firewall!
