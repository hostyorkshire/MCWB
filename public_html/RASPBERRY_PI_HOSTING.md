# Hosting MCWB Website on Raspberry Pi

This guide covers complete setup for hosting the MeshCore Weather Bot website on a Raspberry Pi, from installing a web server to making it accessible on your network.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Setup (Lighttpd - Recommended)](#quick-setup-lighttpd---recommended)
3. [Apache Setup (Alternative)](#apache-setup-alternative)
4. [Nginx Setup (Alternative)](#nginx-setup-alternative)
5. [Deployment](#deployment)
6. [Network Access](#network-access)
7. [Domain Setup (Optional)](#domain-setup-optional)
8. [SSL/HTTPS (Optional)](#sslhttps-optional)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

- Raspberry Pi (any model, Pi Zero 2 W or newer recommended)
- Raspberry Pi OS (formerly Raspbian) installed
- Internet connection
- SSH access or direct terminal access

## Quick Setup (Lighttpd - Recommended)

Lighttpd is lightweight and perfect for Raspberry Pi. It uses minimal resources and is easy to configure.

### 1. Install Lighttpd

```bash
sudo apt update
sudo apt install lighttpd -y
```

### 2. Enable and Start Service

```bash
sudo systemctl enable lighttpd
sudo systemctl start lighttpd
```

### 3. Deploy Website

```bash
# Navigate to your MCWB repository
cd /home/pi/MCWB

# Copy website files to web root
sudo cp -r public_html/* /var/www/html/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 755 /var/www/html/
```

### 4. Test

Open a browser and navigate to:
- From the Pi: `http://localhost`
- From another device: `http://[PI_IP_ADDRESS]`

To find your Pi's IP address:
```bash
hostname -I
```

### 5. Enable PHP Support (Optional)

If you want to use the PHP version:

```bash
sudo apt install php-cgi -y

# Enable PHP in Lighttpd
sudo lighttpd-enable-mod fastcgi
sudo lighttpd-enable-mod fastcgi-php
sudo systemctl restart lighttpd
```

Now you can access `http://[PI_IP_ADDRESS]/index.php`

## Apache Setup (Alternative)

Apache is more feature-rich but uses more resources than Lighttpd.

### 1. Install Apache

```bash
sudo apt update
sudo apt install apache2 -y
```

### 2. Install PHP (if needed)

```bash
sudo apt install php libapache2-mod-php -y
```

### 3. Enable and Start Service

```bash
sudo systemctl enable apache2
sudo systemctl start apache2
```

### 4. Deploy Website

```bash
# Navigate to your MCWB repository
cd /home/pi/MCWB

# Copy website files to web root
sudo cp -r public_html/* /var/www/html/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 755 /var/www/html/
```

### 5. Configure Virtual Host (Optional)

For better organization:

```bash
sudo nano /etc/apache2/sites-available/mcwb.conf
```

Add:
```apache
<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html
    ServerName mcwb.local

    <Directory /var/www/html>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

Enable the site:
```bash
sudo a2ensite mcwb.conf
sudo systemctl reload apache2
```

## Nginx Setup (Alternative)

Nginx is efficient and handles many concurrent connections well.

### 1. Install Nginx

```bash
sudo apt update
sudo apt install nginx -y
```

### 2. Install PHP-FPM (if needed)

```bash
sudo apt install php-fpm -y
```

### 3. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/mcwb
```

Add:
```nginx
server {
    listen 80;
    listen [::]:80;
    
    root /var/www/html;
    index index.php index.html index.htm;
    
    server_name _;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
    }
    
    location ~ /\.ht {
        deny all;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/mcwb /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Deploy Website

```bash
# Navigate to your MCWB repository
cd /home/pi/MCWB

# Copy website files to web root
sudo cp -r public_html/* /var/www/html/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 755 /var/www/html/
```

## Deployment

### Automated Deployment Script

Create a deployment script for easy updates:

```bash
nano ~/deploy-mcwb-website.sh
```

Add:
```bash
#!/bin/bash
# Deploy MCWB website to web server

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Deploying MCWB website..."

# Navigate to MCWB repository
cd /home/pi/MCWB || exit 1

# Pull latest changes (if using git)
echo "Pulling latest changes..."
git pull origin main

# Copy files to web root
echo "Copying files to web root..."
sudo cp -r public_html/* /var/www/html/

# Set permissions
echo "Setting permissions..."
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 755 /var/www/html/

# Restart web server
if systemctl is-active --quiet lighttpd; then
    echo "Restarting Lighttpd..."
    sudo systemctl restart lighttpd
elif systemctl is-active --quiet apache2; then
    echo "Restarting Apache..."
    sudo systemctl restart apache2
elif systemctl is-active --quiet nginx; then
    echo "Restarting Nginx..."
    sudo systemctl restart nginx
fi

echo -e "${GREEN}Deployment complete!${NC}"
echo "Website available at: http://$(hostname -I | awk '{print $1}')"
```

Make it executable:
```bash
chmod +x ~/deploy-mcwb-website.sh
```

Run it:
```bash
~/deploy-mcwb-website.sh
```

### Automatic Deployment on Git Pull

To automatically update the website when you pull changes:

```bash
cd /home/pi/MCWB
nano .git/hooks/post-merge
```

Add:
```bash
#!/bin/bash
/home/pi/deploy-mcwb-website.sh
```

Make it executable:
```bash
chmod +x .git/hooks/post-merge
```

## Network Access

### Find Your Pi's IP Address

```bash
hostname -I
# or
ip addr show | grep inet
```

### Access from Local Network

From any device on your network, open a browser and go to:
```
http://[PI_IP_ADDRESS]
```

Example: `http://192.168.1.100`

### Make IP Address Static

To ensure your Pi always has the same IP:

#### Method 1: Router DHCP Reservation (Recommended)
1. Log into your router's admin panel
2. Find DHCP settings
3. Add a reservation for your Pi's MAC address
4. Assign a static IP (e.g., 192.168.1.100)

#### Method 2: Configure on Pi
```bash
sudo nano /etc/dhcpcd.conf
```

Add (adjust for your network):
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8

interface wlan0
static ip_address=192.168.1.101/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Restart networking:
```bash
sudo systemctl restart dhcpcd
```

## Domain Setup (Optional)

### Local Network Domain (mDNS)

Install Avahi for local network discovery:

```bash
sudo apt install avahi-daemon -y
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
```

Now you can access your site at:
```
http://raspberrypi.local
```

To use a custom hostname:
```bash
sudo raspi-config
# Navigate to: System Options > Hostname
# Set to: mcwb
```

Access at: `http://mcwb.local`

### Public Domain (Advanced)

For internet access, you'll need:

1. **Port forwarding** on your router (port 80 to your Pi's IP)
2. **Dynamic DNS** service (like No-IP, DuckDNS, or DynDNS)

Example with DuckDNS:

```bash
# Install DuckDNS updater
mkdir -p ~/duckdns
cd ~/duckdns
nano duck.sh
```

Add (replace with your domain and token):
```bash
echo url="https://www.duckdns.org/update?domains=YOUR_DOMAIN&token=YOUR_TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

Make executable:
```bash
chmod +x duck.sh
```

Add to crontab:
```bash
crontab -e
```

Add:
```
*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

## SSL/HTTPS (Optional)

Secure your website with Let's Encrypt (free SSL certificate).

### Prerequisites
- Public domain name pointing to your Pi
- Port 80 and 443 forwarded to your Pi

### Install Certbot

```bash
sudo apt install certbot -y
```

### For Apache:
```bash
sudo apt install python3-certbot-apache -y
sudo certbot --apache -d your-domain.com
```

### For Nginx:
```bash
sudo apt install python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### For Lighttpd:
```bash
sudo certbot certonly --standalone -d your-domain.com

# Configure Lighttpd
sudo nano /etc/lighttpd/lighttpd.conf
```

Add:
```
$SERVER["socket"] == ":443" {
    ssl.engine = "enable"
    ssl.pemfile = "/etc/letsencrypt/live/your-domain.com/fullchain.pem"
    ssl.privkey = "/etc/letsencrypt/live/your-domain.com/privkey.pem"
}
```

Restart:
```bash
sudo systemctl restart lighttpd
```

### Auto-Renewal

Let's Encrypt certificates expire after 90 days. Set up auto-renewal:

```bash
sudo crontab -e
```

Add:
```
0 0 * * * certbot renew --quiet && systemctl reload lighttpd
```

## Troubleshooting

### Website Not Loading

1. **Check if web server is running:**
   ```bash
   sudo systemctl status lighttpd  # or apache2 or nginx
   ```

2. **Check firewall:**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. **Check web server logs:**
   ```bash
   # Lighttpd
   sudo tail -f /var/log/lighttpd/error.log
   
   # Apache
   sudo tail -f /var/log/apache2/error.log
   
   # Nginx
   sudo tail -f /var/log/nginx/error.log
   ```

### PHP Not Working

1. **Check PHP is installed:**
   ```bash
   php -v
   ```

2. **Check PHP module is enabled:**
   ```bash
   # Apache
   sudo a2enmod php7.4
   
   # Nginx/Lighttpd
   sudo systemctl status php7.4-fpm
   ```

3. **Test PHP:**
   ```bash
   echo "<?php phpinfo(); ?>" | sudo tee /var/www/html/info.php
   ```
   Visit: `http://[PI_IP]/info.php`

### Permission Issues

```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/html/

# Fix permissions
sudo chmod -R 755 /var/www/html/
```

### Can't Access from Other Devices

1. **Check Pi's IP address:**
   ```bash
   hostname -I
   ```

2. **Ping the Pi from another device:**
   ```bash
   ping [PI_IP_ADDRESS]
   ```

3. **Check firewall on Pi:**
   ```bash
   sudo ufw status
   # If active, allow HTTP
   sudo ufw allow 80/tcp
   ```

4. **Ensure devices are on same network**

### Low Memory/Performance

Lighttpd is recommended for Raspberry Pi as it uses minimal resources. If using Apache:

```bash
# Check memory usage
free -h

# Switch to Lighttpd if needed
sudo systemctl stop apache2
sudo systemctl disable apache2
sudo apt install lighttpd -y
sudo systemctl enable lighttpd
sudo systemctl start lighttpd
```

## Performance Optimization

### Enable Gzip Compression

**Lighttpd:**
```bash
sudo lighttpd-enable-mod compress
sudo systemctl restart lighttpd
```

**Apache:**
```bash
sudo a2enmod deflate
sudo systemctl restart apache2
```

**Nginx:**
Add to `/etc/nginx/nginx.conf`:
```nginx
gzip on;
gzip_vary on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

### Enable Caching

**Lighttpd:**
```bash
sudo nano /etc/lighttpd/lighttpd.conf
```

Add:
```
server.modules += ( "mod_expire" )
expire.url = ( "" => "access plus 1 hours" )
```

### Monitor Resources

```bash
# Install htop
sudo apt install htop -y

# Monitor in real-time
htop
```

## Running Both Bot and Website

Your Raspberry Pi can run both the weather bot and serve the website simultaneously:

```bash
# Start weather bot as service
sudo systemctl start weather_bot

# Web server runs automatically
sudo systemctl status lighttpd

# Check both are running
systemctl is-active weather_bot lighttpd
```

## Backup and Restore

### Backup Website

```bash
# Create backup
sudo tar -czf ~/mcwb-website-backup-$(date +%Y%m%d).tar.gz /var/www/html/

# List backups
ls -lh ~/mcwb-website-backup-*
```

### Restore Website

```bash
# Restore from backup
sudo tar -xzf ~/mcwb-website-backup-YYYYMMDD.tar.gz -C /
sudo chown -R www-data:www-data /var/www/html/
sudo systemctl restart lighttpd
```

## Further Reading

- [Lighttpd Documentation](https://www.lighttpd.net/)
- [Apache Documentation](https://httpd.apache.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [Let's Encrypt](https://letsencrypt.org/)
