# 🚨 EMERGENCY: Cannot SSH Into Pi OR Cannot See Dashboard

## Quick Recovery Card
**Save or print this for emergencies!**

---

## Symptoms
You are experiencing ONE or BOTH of these problems:
- ❌ **SSH fails:** Cannot connect via SSH to your Raspberry Pi
- ❌ **Dashboard fails:** Cannot access http://[your-pi-ip]:5000 in browser

---

## ⚡ FASTEST FIX (One Command Fixes Both)

### With Physical Access (Keyboard + Monitor) - RECOMMENDED

1. **Connect keyboard and monitor to your Raspberry Pi**
2. **Log in locally** with your username and password
3. **Run this ONE command:**

```bash
cd ~/MCWB && ./fix_access_issues.sh
```

4. **Follow the prompts** - The script will:
   - ✅ Automatically diagnose SSH issues
   - ✅ Automatically diagnose dashboard issues
   - ✅ Fix firewall blocking SSH (port 22)
   - ✅ Fix dashboard service not running
   - ✅ Enable both services to start on boot
   - ✅ Show you the URLs to test

**That's it!** One script fixes everything.

---

## What This Script Does

### For SSH Issues:
- Checks if SSH service is running → Starts it if needed
- Checks if firewall is blocking port 22 → Opens it if needed
- Verifies SSH is accessible

### For Dashboard Issues:
- Checks if dashboard service is installed → Guides you to install if missing
- Checks if dashboard service is running → Starts it if needed
- Checks if dashboard service is enabled → Enables it if needed
- Tests if dashboard responds on port 5000
- Optionally opens firewall port 5000 for remote access

---

## Individual Issue Scripts

If you only have ONE specific problem, use these targeted scripts:

### SSH Issue Only
```bash
cd ~/MCWB
./fix_ssh_access.sh
```

### Dashboard Issue Only
```bash
cd ~/MCWB
./fix_dashboard.sh
```

---

## Without Physical Access

If you **cannot** physically access the Pi:

### For SSH Issues:
1. **Remove SD card** from Pi
2. **Mount SD card** on another Linux/Mac computer
3. **Edit `/etc/ufw/ufw.conf`** on the SD card
4. **Change** `ENABLED=yes` to `ENABLED=no`
5. **Unmount** and reinsert into Pi
6. **Boot** - SSH should now work
7. **Run** `./fix_ssh_access.sh` to properly configure firewall

### For Dashboard Issues:
- Dashboard requires SSH access to fix remotely
- Fix SSH first using the steps above
- Then SSH in and run `./fix_access_issues.sh`

---

## After Fix - Test Your Services

### Test SSH Connection
From another computer on the same network:
```bash
ssh your_username@your-pi-ip
# Example: ssh pi@192.168.1.109
```

### Test Dashboard Access
Open in your web browser:
```
http://your-pi-ip:5000
# Example: http://192.168.1.109:5000
```

**Note:** Use `http://` NOT `https://` by default

---

## Prevention Tips

### For SSH:
**Always configure firewall in this order:**
```bash
# ✅ CORRECT ORDER:
sudo ufw allow 22/tcp    # 1. Allow SSH FIRST
sudo ufw enable          # 2. Enable firewall LAST

# ❌ WRONG ORDER (locks you out):
sudo ufw enable          # 1. Enables firewall first
sudo ufw allow 22/tcp    # 2. Too late! Already locked out
```

### For Dashboard:
**Make sure service is enabled to start on boot:**
```bash
sudo systemctl enable mcwb-dashboard
```

---

## Quick Commands Reference

```bash
# Check SSH service status
sudo systemctl status ssh

# Check dashboard service status
sudo systemctl status mcwb-dashboard

# Check firewall status
sudo ufw status verbose

# View dashboard logs
sudo journalctl -u mcwb-dashboard -n 50

# View SSH logs
sudo journalctl -u ssh -n 50

# Get your Pi's IP address
hostname -I
```

---

## Still Having Issues?

### Check Network Connectivity:
```bash
# From your computer, ping your Pi:
ping your-pi-ip

# If ping fails, it's a network issue (not SSH/firewall)
```

### Common Network Issues:
- ❌ Pi and computer on different networks
- ❌ Router blocking connections
- ❌ Wrong IP address (Pi may have changed IP)
- ❌ VPN or firewall on your computer blocking connections

### Get Your Pi's Current IP:
On the Pi itself:
```bash
hostname -I
# First IP shown is usually the correct one
```

Or check your router's DHCP client list.

---

## Full Documentation

For detailed troubleshooting, see:
- **QUICK_FIX_GUIDE.md** - Fast solutions for common issues
- **SSH_TROUBLESHOOTING.md** - Complete SSH recovery guide
- **SSH_EMERGENCY.md** - SSH emergency procedures
- **DASHBOARD_CONNECTIVITY_TROUBLESHOOTING.md** - Dashboard diagnosis
- **TROUBLESHOOTING.md** - General troubleshooting

---

## Contact

If you're still stuck after trying these fixes:
1. Check the full troubleshooting documentation
2. Open a GitHub issue with details
3. Include output from:
   ```bash
   sudo systemctl status ssh
   sudo systemctl status mcwb-dashboard
   sudo ufw status verbose
   hostname -I
   ```

---

**Remember:** Most SSH and dashboard issues are simple service or firewall problems. The fix is usually just one command!

**Print this card and keep it handy!** 🖨️
