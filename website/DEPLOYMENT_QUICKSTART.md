# Quick Deployment Guide

## Fastest Ways to Deploy Your MCWB Wiki

### Option 1: GitHub Pages (Recommended - Free & Easy)

1. **Push to GitHub** (already done if you're reading this!)

2. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` (or your branch)
   - Folder: `/website`
   - Click Save

3. **Access your site:**
   - URL: `https://hostyorkshire.github.io/MCWB/`
   - Updates automatically on git push!

### Option 2: Netlify (Instant Deployment)

**Drag & Drop:**
1. Go to: https://app.netlify.com/drop
2. Drag the entire `website` folder
3. Your site is live instantly!

**CLI Deployment:**
```bash
npm install -g netlify-cli
cd website
netlify deploy --prod
```

### Option 3: Your Own Server

**Copy to web server:**
```bash
# Via rsync
rsync -avz website/ user@yourserver.com:/var/www/html/mcwb/

# Via SCP
scp -r website/* user@yourserver.com:/var/www/html/mcwb/
```

**Basic Apache config:**
```apache
<Directory /var/www/html/mcwb>
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>
```

**Basic Nginx config:**
```nginx
server {
    listen 80;
    server_name mcwb.yourdomain.com;
    root /var/www/html/mcwb;
    index index.html;
}
```

### Option 4: Test Locally First

```bash
cd website
python3 -m http.server 8000
# Open: http://localhost:8000
```

## Custom Domain Setup

### With GitHub Pages:
1. Add `CNAME` file to website folder with your domain
2. Add DNS record: `CNAME` → `yourusername.github.io`

### With Netlify:
1. Domain Settings → Add custom domain
2. Follow DNS instructions

## That's It! 🎉

Your wiki is now live and accessible under your domain!

For more details, see the complete `README.md` in this folder.
