# Troubleshooting Scripts

This directory includes several scripts to help diagnose and fix common issues with the MeshCore Weather Bot.

## check_wifi.sh - WiFi Connectivity Diagnostic

**Use when:** 
- `git pull` fails with "could not resolve host"
- Cannot access the internet
- WiFi connection issues
- Network troubleshooting needed

```bash
cd ~/MCWB
./check_wifi.sh
```

**What it checks:**
1. WiFi adapter status and configuration
2. WiFi connection status and signal strength
3. IP address assignment
4. Gateway (router) connectivity
5. Internet connectivity (ping tests)
6. DNS resolution
7. Network configuration files

**Best for:**
- Diagnosing "could not resolve host" errors
- Network connectivity problems
- WiFi configuration issues
- Internet access troubleshooting

---

## fix_dashboard.sh - Quick Fix (Use this first!)

**Use when:** Dashboard was working before but stopped

```bash
cd ~/MCWB
./fix_dashboard.sh
```

**What it does:**
- Checks if the service is running
- Restarts it if needed
- Detects and fixes common issues:
  - Missing Python dependencies
  - Permission problems
  - Port conflicts
- Gets you back online in under 30 seconds

**Best for:** Quick recovery when something broke

---

## diagnose_dashboard.sh - Full Diagnostics

**Use when:** You need to understand what's wrong

```bash
cd ~/MCWB
./diagnose_dashboard.sh
```

**What it checks:**
1. Service installation status
2. Service enabled for boot startup
3. Service currently running
4. Local connectivity (localhost:5000)
5. Network interface binding (0.0.0.0 vs 127.0.0.1)
6. Firewall configuration (UFW)
7. Python dependencies (Flask, flask-cors)
8. End-to-end connectivity test

**Best for:** 
- Understanding root causes
- When quick fix doesn't work
- Setting up for the first time
- Preventive maintenance

---

## Common Scenarios

### "It worked yesterday, now it doesn't"
```bash
./fix_dashboard.sh
```
Most likely: Service stopped or didn't restart after reboot

### "It's never worked for me"
```bash
./diagnose_dashboard.sh
```
Let the diagnostic walk you through each issue

### "I just rebooted and can't connect"
```bash
./fix_dashboard.sh
```
Service may not have started automatically

### "I want to know exactly what's wrong"
```bash
./diagnose_dashboard.sh
```
Comprehensive 8-step check

---

## Manual Commands

If you prefer to check manually:

```bash
# Check service status
sudo systemctl status mcwb-dashboard

# Restart service
sudo systemctl restart mcwb-dashboard

# View logs
sudo journalctl -u mcwb-dashboard -n 50

# Test connectivity
curl http://localhost:5000

# Check firewall
sudo ufw status

# Check what's on port 5000
sudo netstat -tlnp | grep :5000
```

---

## Getting Help

If scripts don't resolve your issue:

1. Save the output: `./diagnose_dashboard.sh > diagnostic_output.txt`
2. Check service logs: `sudo journalctl -u mcwb-dashboard -n 100 > service_logs.txt`
3. Open an issue at https://github.com/yourusername/MCWB/issues
4. Include both output files

---

## See Also

- [CONNECTION_GUIDE.md](CONNECTION_GUIDE.md) - Simple connection guide
- [DASHBOARD_CONNECTIVITY_TROUBLESHOOTING.md](DASHBOARD_CONNECTIVITY_TROUBLESHOOTING.md) - Detailed troubleshooting
- [WEB_DASHBOARD.md](WEB_DASHBOARD.md) - Full dashboard documentation
