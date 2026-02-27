# Quick Deployment Guide

## Fastest Ways to Deploy Your MCWB Wiki

### Option 1: GitHub Pages (Recommended - Free & Easy)

1. **Push to GitHub** (already done if you're reading this!)

2. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` (or your branch)
   - Folder: `/public_html/wx`
   - Click Save

3. **Access your site:**
   - URL: `https://hostyorkshire.github.io/MCWB/`
   - Updates automatically on git push!

### Option 2: Netlify (Automatic Deployment from GitHub)

**Connect GitHub Repository (Recommended - Auto-deploys on commit!):**
1. Go to: https://app.netlify.com/
2. Click "Add new site" → "Import an existing project"
3. Choose "Deploy with GitHub"
4. Authorize Netlify to access your GitHub account
5. Select the `hostyorkshire/MCWB` repository
6. Configure build settings (should auto-detect from netlify.toml):
   - Base directory: (leave empty)
   - Build command: (leave empty)
   - Publish directory: `public_html/wx`
7. Click "Deploy site"
8. Your site is live and will automatically update on every git push!

**Drag & Drop (Manual deployment - no auto-updates):**
1. Go to: https://app.netlify.com/drop
2. Drag the entire `public_html/wx` folder
3. Your site is live instantly! (Note: You'll need to manually redeploy for updates)

**CLI Deployment:**
```bash
npm install -g netlify-cli
cd public_html/wx
netlify deploy --prod
```

### Option 3: Your Own Server

**Copy to web server:**
```bash
# Via rsync
rsync -avz public_html/wx/ user@yourserver.com:/var/www/html/mcwb/

# Via SCP
scp -r public_html/wx/* user@yourserver.com:/var/www/html/mcwb/
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
cd public_html/wx
python3 -m http.server 8000
# Open: http://localhost:8000
```

## Custom Domain Setup

### With GitHub Pages:
1. Add `CNAME` file to public_html/wx folder with your domain
2. Add DNS record: `CNAME` → `yourusername.github.io`

### With Netlify:
1. Domain Settings → Add custom domain
2. Follow DNS instructions

## That's It! 🎉

Your wiki is now live and accessible under your domain!

For more details, see the complete `README.md` in this folder.
