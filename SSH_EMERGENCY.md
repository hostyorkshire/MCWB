# 🚨 EMERGENCY: Can't SSH Into Raspberry Pi

## Quick Recovery Card
**Save or print this for emergencies!**

---

## Symptoms
- ✅ **Ping works:** `ping 192.168.1.100` succeeds  
- ❌ **SSH fails:** Connection refused or timeout

---

## Most Likely Cause
**Firewall is blocking SSH port 22**

---

## Recovery Steps

### With Physical Access (Keyboard + Monitor)

1. **Connect keyboard and monitor to your Raspberry Pi**
2. **Log in locally** with your username and password
3. **Run ONE of these commands:**

   ```bash
   # Option A: Use the fix script (easiest)
   cd ~/MCWB
   ./fix_ssh_access.sh
   
   # Option B: Quick manual fix
   sudo ufw allow 22/tcp && sudo ufw reload
   
   # Option C: Disable firewall (less secure)
   sudo ufw disable
   ```

4. **Test SSH** from another computer:
   ```bash
   ssh your_username@192.168.1.100
   ```

---

### Without Physical Access

If you can't physically access the Pi, try these:

1. **Wait until you have physical access** - then use steps above
2. **Remove SD card and fix on another computer:**
   - Mount the SD card on another Linux/Mac computer
   - Edit `/etc/ufw/ufw.conf` on the SD card
   - Change `ENABLED=yes` to `ENABLED=no`
   - Unmount and reinsert into Pi
   - Boot and SSH should work

---

## Prevention

**Always follow this order when setting up firewall:**

```bash
# ✅ CORRECT ORDER:
sudo ufw allow 22/tcp    # 1. Allow SSH FIRST
sudo ufw enable          # 2. Enable firewall LAST

# ❌ WRONG ORDER (locks you out):
sudo ufw enable          # 1. Enables firewall first
sudo ufw allow 22/tcp    # 2. Too late! Already locked out
```

---

## Full Documentation

For detailed troubleshooting, see:
- **SSH_TROUBLESHOOTING.md** - Complete recovery guide
- **TROUBLESHOOTING.md** - General troubleshooting
- **SSH_REMOTE_ACCESS.md** - SSH setup and security

---

## Quick Commands Reference

```bash
# Check firewall status
sudo ufw status

# Allow SSH
sudo ufw allow 22/tcp

# Reload firewall
sudo ufw reload

# Disable firewall
sudo ufw disable

# Check SSH service
sudo systemctl status ssh

# Start SSH service
sudo systemctl start ssh

# View what's listening on port 22
sudo netstat -tlnp | grep :22
```

---

## Contact

If you're still stuck after trying these fixes:
1. Check the full troubleshooting guide: **SSH_TROUBLESHOOTING.md**
2. Open a GitHub issue with details
3. Seek help in community forums

---

**Remember:** This is almost always a firewall issue. The fix is simple once you have physical access!

**Print this card and keep it handy!** 🖨️
