# MCWBv2 Website - Hosting Guide

This directory contains the website/wiki for the MeshCore Weather Bot. The website is designed in a wiki style and can be easily integrated into WordPress.

## Contents

- `index.html` - Standalone HTML version of the wiki
- `index.php` - WordPress-compatible PHP version
- `style.css` - Wiki-style CSS (works with both HTML and PHP versions)
- `RASPBERRY_PI_HOSTING.md` - Complete guide for hosting on Raspberry Pi
- `WORDPRESS_INTEGRATION.md` - Comprehensive WordPress integration guide

## Quick Start

### Option 1: View Locally (No Server Required)
Simply open `index.html` in your web browser:
```bash
cd public_html
firefox index.html
# or
chromium-browser index.html
```

### Option 2: Host on Raspberry Pi
See [RASPBERRY_PI_HOSTING.md](RASPBERRY_PI_HOSTING.md) for complete instructions on setting up a web server on your Raspberry Pi.

### Option 3: WordPress Integration
Multiple integration methods available! See [WORDPRESS_INTEGRATION.md](WORDPRESS_INTEGRATION.md) for complete guide including:
- Page Templates (recommended)
- Shortcodes
- Custom Plugins
- Gutenberg Blocks
- iFrame Embeds

## Files

### index.html
Standalone HTML page that can be opened directly in a browser or served via any web server. No server-side processing required.

### index.php
WordPress-compatible version that:
- Automatically detects if running within WordPress
- Uses WordPress header/footer when available
- Falls back to standalone mode if WordPress is not available
- Can be used as a WordPress page template

### style.css
Wiki-style CSS with:
- Responsive design for mobile devices
- WordPress compatibility classes
- Print-friendly styles
- Clean, readable wiki appearance

## Hosting Options

### Static Hosting (HTML only)
Any web server can host the HTML version:
- Apache
- Nginx
- Python's built-in server: `python3 -m http.server 8000`
- Node.js http-server: `npx http-server`

### Dynamic Hosting (PHP version)
Requires a web server with PHP support:
- Apache with mod_php
- Nginx with PHP-FPM
- See RASPBERRY_PI_HOSTING.md for setup instructions

## WordPress Integration

See [WORDPRESS_INTEGRATION.md](WORDPRESS_INTEGRATION.md) for comprehensive integration guide with 5 different methods:

1. **Page Template** - Full theme integration with native WordPress features
2. **Shortcode** - Flexible embedding in any page or post
3. **Custom Plugin** - Theme-independent, portable solution
4. **iFrame Embed** - Quick and easy, no code changes needed
5. **Gutenberg Block** - Modern block editor integration

Each method includes step-by-step instructions, code examples, and troubleshooting tips.

## Customization

### Colors
Edit the CSS variables in `style.css`:
```css
:root {
    --primary-color: #0066cc;    /* Main theme color */
    --secondary-color: #f8f9fa;  /* Background color */
    --border-color: #ddd;        /* Border color */
    /* ... more variables ... */
}
```

### Content
Edit `index.html` or `index.php` to modify the content. Both files contain the same content structure.

## License

MIT License - same as the main MCWB project.
