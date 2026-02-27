# MCWB Wiki Website

This is a comprehensive wiki-style documentation website for the MeshCore Weather Bot (MCWB).

## Features

- 🌙 **Dark Mode Design** - Professional dark theme optimized for readability
- 📱 **Fully Responsive** - Works perfectly on desktop, tablet, and mobile devices
- 📊 **Demo Dashboard** - Static demo showing dashboard capabilities
- 🎨 **Modern UI** - Clean, professional design with smooth animations
- 🔍 **Easy Navigation** - Clear menu structure and search-friendly content
- ⚡ **Fast & Lightweight** - Pure HTML/CSS/JavaScript, no build process needed

## Pages Included

1. **Home** (`index.html`) - Overview and introduction
2. **Getting Started** (`getting-started.html`) - Quick setup guide
3. **Installation** (`installation.html`) - Detailed installation instructions
4. **Features** (`features.html`) - Complete feature list
5. **Commands** (`commands.html`) - Command reference and usage
6. **Channels** (`channels.html`) - Channel configuration guide
7. **Live Dashboard** (`dashboard.html`) - Demo dashboard with DDNS/remote access information
8. **Troubleshooting** (`troubleshooting.html`) - Common issues and solutions
9. **API** (`api.html`) - Technical documentation and protocol details

## About the Dashboard

The Live Dashboard page (`dashboard.html`) displays **demo data only**. This is intentional to keep the static website lightweight and avoid resource costs from live data connections.

**For live, real-time monitoring:**
- Access the web dashboard directly on your Raspberry Pi
- Run: `python3 web_dashboard.py --host 0.0.0.0`
- Access locally at: `http://[your-pi-ip]:5000`
- For remote access, see the DDNS/No-IP setup instructions on the dashboard page

This approach:
- ✅ Keeps Netlify hosting free and lightweight
- ✅ Eliminates CORS and connectivity issues
- ✅ Provides direct, fast access to live data on your local network
- ✅ Enables remote access via DDNS when needed

## Deployment Instructions

### Option 1: Simple File Hosting

Upload the entire `website` folder to any static web hosting service:

**Popular Free Options:**
- **GitHub Pages** - Free hosting directly from your repo
- **Netlify** - Drag-and-drop deployment
- **Vercel** - Simple git-based deployment
- **Cloudflare Pages** - Fast global CDN
- **AWS S3** - Static website hosting
- **Azure Static Web Apps** - Microsoft's static hosting

### Option 2: GitHub Pages (Recommended)

1. **Enable GitHub Pages:**
   - Go to your repository settings on GitHub
   - Navigate to "Pages" section
   - Select source: Deploy from a branch
   - Select branch: `main` or your working branch
   - Select folder: `/website` (if your repo has the website in a subfolder)
   - Click Save

2. **Access your site:**
   - Your site will be available at: `https://[username].github.io/MCWB/`
   - Custom domains are also supported

### Option 3: Netlify (Automatic Deployment)

**Connect GitHub Repository (Recommended):**
1. Go to: https://app.netlify.com/
2. Click "Add new site" → "Import an existing project"
3. Choose "Deploy with GitHub" and authorize Netlify
4. Select the `yourusername/MCWB` repository
5. Configure build settings (auto-detected from netlify.toml):
   - Base directory: (leave empty)
   - Build command: (leave empty)
   - Publish directory: `website`
6. Click "Deploy site"
7. Your site will automatically update on every git push!

**Manual Deployment Options:**

1. **CLI Deployment:**
   ```bash
   # Install Netlify CLI (optional)
   npm install -g netlify-cli
   
   # Deploy from website folder
   cd website
   netlify deploy --prod
   ```

2. **Drag-and-drop:**
   - Go to https://app.netlify.com/drop
   - Drag the `website` folder to the upload area
   - Your site is live instantly!

### Option 4: Your Own Web Server

Upload to your web server via FTP, SFTP, or rsync:

```bash
# Example: rsync to your server
rsync -avz public_html/wx/ user@yourserver.com:/var/www/html/mcwb/

# Example: SCP
scp -r public_html/wx/* user@yourserver.com:/var/www/html/mcwb/
```

**Web Server Configuration:**

**Apache (.htaccess):**
```apache
# Enable clean URLs (optional)
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^([^\.]+)$ $1.html [NC,L]
```

**Nginx:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/html/mcwb;
    index index.html;

    location / {
        try_files $uri $uri.html $uri/ =404;
    }
}
```

### Option 5: Local Development Server

For local testing:

```bash
# Python 3
cd website
python3 -m http.server 8000

# Access at: http://localhost:8000

# Or with Node.js (if installed)
npx http-server -p 8000
```

## Custom Domain Setup

### With GitHub Pages

1. Add a `CNAME` file to the website folder:
   ```
   yourdomain.com
   ```

2. Configure DNS:
   - Add CNAME record pointing to `[username].github.io`
   - Or A records to GitHub's IPs:
     - 185.199.108.153
     - 185.199.109.153
     - 185.199.110.153
     - 185.199.111.153

### With Netlify

1. Go to Domain Settings in Netlify dashboard
2. Click "Add custom domain"
3. Follow the DNS configuration instructions

## File Structure

```
public_html/wx/
├── index.html              # Homepage
├── getting-started.html    # Quick start guide
├── installation.html       # Installation guide
├── features.html          # Feature list
├── commands.html          # Command reference
├── channels.html          # Channel configuration
├── dashboard.html         # Live monitoring (demo)
├── troubleshooting.html   # Troubleshooting guide
├── api.html              # API documentation
├── css/
│   └── style.css         # Main stylesheet (dark mode)
├── js/
│   ├── main.js           # Main JavaScript
│   └── dashboard.js      # Dashboard functionality
└── README.md             # This file
```

## Customization

### Change Colors

Edit `public_html/wx/css/style.css` and modify the color variables:

```css
:root {
    --bg-primary: #0f1419;          /* Main background */
    --accent-primary: #60a5fa;      /* Accent color */
    /* ... other colors ... */
}
```

### Update Content

Simply edit the HTML files. No build process required!

### Add New Pages

1. Create a new HTML file (e.g., `newpage.html`)
2. Copy the structure from an existing page
3. Update the navigation in all pages to include your new page
4. Add your content

## Browser Compatibility

The website works on all modern browsers:
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- No external dependencies (except Chart.js for dashboard)
- Minimal CSS (~14KB)
- Minimal JavaScript (~3KB main + ~8KB dashboard)
- Fast load times
- Works offline after first load

## SEO Optimization

The website includes:
- Semantic HTML structure
- Meta descriptions on all pages
- Proper heading hierarchy
- Alt text for images (if added)
- Clean URLs
- Mobile-friendly design

## Accessibility

- High contrast dark mode for readability
- Semantic HTML elements
- Keyboard navigation support
- Screen reader friendly
- ARIA labels where appropriate

## Live Dashboard Notes

The Live Dashboard page (`dashboard.html`) shows **demo data only**. This keeps the static website lightweight and resource-efficient.

**For real-time bot monitoring:**
1. Run the Python web dashboard on your Raspberry Pi:
   ```bash
   python3 web_dashboard.py --host 0.0.0.0
   ```
2. Access it locally at `http://[your-pi-ip]:5000`
3. For remote access outside your network, set up DDNS (Dynamic DNS) with services like:
   - [No-IP](https://www.noip.com/) - Free DDNS service
   - [DuckDNS](https://www.duckdns.org/) - Simple and free
   - [Dynu](https://www.dynu.com/) - Free with multiple hostnames

The dashboard page includes complete setup instructions for DDNS/No-IP remote access.

## Maintenance

To update the website:
1. Edit the HTML files with new content
2. Test locally with a web server
3. Deploy updated files to your hosting service

## Support

For issues or questions about the bot itself, see:
- [MCWB GitHub Repository](https://github.com/yourusername/MCWB)
- [Issue Tracker](https://github.com/yourusername/MCWB/issues)

## License

Same as MCWB project - MIT License

See the main repository [LICENSE](https://github.com/yourusername/MCWB/blob/main/LICENSE) file for details.
