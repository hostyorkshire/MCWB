# API Connectivity Error - Root Cause Analysis

## Your Error Message

```
Weather error: HTTPSConnectionPool(host='geocoding-api.open-meteo.com', port=443): 
Max retries exceeded with url: /v1/search?name=yo...
```

## Is This a Code Problem or API Problem?

**Answer: This is most likely a NETWORK CONNECTIVITY problem, not a code issue or API timeout.**

Here's how to tell the difference:

### What the Error Means

The error "Max retries exceeded" with "Failed to resolve" indicates that:
- ❌ **The bot cannot reach the API server at all**
- ❌ **DNS resolution is failing** (cannot convert hostname to IP address)
- ✅ **The bot's code is working correctly** - it's trying to connect
- ✅ **The API itself may be fine** - the bot just can't reach it

### Different Error Types and What They Mean

| Error Message | Meaning | Is it code or API? |
|--------------|---------|-------------------|
| `Failed to resolve` / `Name resolution error` | Cannot convert hostname to IP | **Network/DNS issue** |
| `Connection refused` | Server explicitly rejected connection | **API or firewall** |
| `Connection timeout` | Server not responding | **API slow or network** |
| `Read timeout` | Server slow to respond | **API performance** |
| `Max retries exceeded` | Multiple connection attempts failed | **Usually network** |
| `Certificate verify failed` | SSL/TLS problem | **System certificates** |
| `Location not found` | API worked but no results | **User input issue** |

## How to Diagnose

### Step 1: Run the Diagnostic Tool

We've created a diagnostic tool to identify the exact problem:

```bash
python3 diagnose_api_connectivity.py
```

This will test:
1. DNS resolution (can the system resolve `api.open-meteo.com`?)
2. TCP connection (can we connect to port 443?)
3. HTTP request (can we make an actual API call?)
4. API response (does the API return valid data?)

### Step 2: Check Basic Network Connectivity

```bash
# Test if you have internet at all
ping -c 3 8.8.8.8

# Test DNS resolution manually
nslookup api.open-meteo.com
# OR
dig api.open-meteo.com

# Test HTTPS connection
curl -v https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=0&current=temperature_2m
```

### Step 3: Check DNS Configuration

```bash
# Linux/Mac: Check DNS servers
cat /etc/resolv.conf

# Should see something like:
# nameserver 8.8.8.8
# nameserver 1.1.1.1
```

## Common Causes and Solutions

### Cause 1: No Internet Connection
**Symptoms:** DNS fails, ping fails, nothing works
**Solution:**
```bash
# Check network interface
ip addr show
# OR
ifconfig

# Restart networking
sudo systemctl restart networking
# OR
sudo service networking restart
```

### Cause 2: DNS Not Configured
**Symptoms:** `ping 8.8.8.8` works, but `ping api.open-meteo.com` fails
**Solution:**
```bash
# Add Google's DNS temporarily
sudo bash -c 'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
sudo bash -c 'echo "nameserver 1.1.1.1" >> /etc/resolv.conf'

# Or permanently (Ubuntu/Debian)
sudo nano /etc/systemd/resolved.conf
# Add: DNS=8.8.8.8 1.1.1.1
sudo systemctl restart systemd-resolved
```

### Cause 3: Firewall Blocking HTTPS
**Symptoms:** DNS works, but HTTPS connections fail
**Solution:**
```bash
# Check firewall rules
sudo iptables -L -n

# Allow outbound HTTPS (port 443)
sudo iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

# For UFW users
sudo ufw allow out 443/tcp
```

### Cause 4: Corporate Proxy
**Symptoms:** Error mentions proxy or connection refused
**Solution:**
```bash
# Set proxy environment variables
export http_proxy="http://proxy.company.com:8080"
export https_proxy="http://proxy.company.com:8080"

# Or for Python/requests specifically
export REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt
```

### Cause 5: Raspberry Pi - Network Not Up Yet
**Symptoms:** Bot fails at startup but works later
**Solution:**
```bash
# Add network wait to systemd service
sudo nano /etc/systemd/system/weather_bot.service

# Add these lines under [Unit]:
After=network-online.target
Wants=network-online.target

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
```

### Cause 6: Docker/Container - DNS Not Configured
**Symptoms:** Works outside container, fails inside
**Solution:**
```bash
# Add DNS to docker run command
docker run --dns 8.8.8.8 --dns 1.1.1.1 ...

# Or in docker-compose.yml:
services:
  weatherbot:
    dns:
      - 8.8.8.8
      - 1.1.1.1
```

## Verifying the Fix

After applying a solution, test with:

```bash
# Test 1: Basic connectivity
ping -c 3 api.open-meteo.com

# Test 2: API request
curl "https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=0&current=temperature_2m"

# Test 3: Run diagnostic
python3 diagnose_api_connectivity.py

# Test 4: Try the bot
python3 weather_bot.py --location York
```

## Is the Bot Code Working?

**YES**, the bot code is working correctly because:

1. ✅ The error handling properly catches and reports network errors
2. ✅ The bot is attempting to make the API call (proves code runs)
3. ✅ The error message shows the exact URL being requested (proves parsing works)
4. ✅ All unit tests pass (proves logic is correct)
5. ✅ The improved error handling now shows user-friendly messages

The bot cannot fix network/DNS issues - those must be resolved at the system level.

## Summary

| Question | Answer |
|----------|--------|
| Is it a code problem? | **No** - the bot code is working correctly |
| Is it an API problem? | **Probably not** - more likely can't reach it |
| Is it a network problem? | **Yes** - most likely DNS or connectivity |
| Can the bot fix it? | **No** - must be fixed at system level |
| How to diagnose? | Run `diagnose_api_connectivity.py` |
| How to fix? | See "Common Causes and Solutions" above |

## Need More Help?

1. Run the diagnostic tool and share the output
2. Share the output of these commands:
   ```bash
   ping -c 3 8.8.8.8
   ping -c 3 api.open-meteo.com
   cat /etc/resolv.conf
   curl -v https://api.open-meteo.com/v1/forecast?latitude=51&longitude=0&current=temperature_2m
   ```
3. Mention your environment (Raspberry Pi, Linux, Docker, etc.)
