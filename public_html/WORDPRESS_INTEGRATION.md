# WordPress Integration Guide for MCWB Website

This guide provides detailed instructions for integrating the MeshCore Weather Bot website into WordPress in multiple ways.

## Table of Contents

1. [Integration Methods Overview](#integration-methods-overview)
2. [Method 1: Page Template (Recommended)](#method-1-page-template-recommended)
3. [Method 2: Shortcode](#method-2-shortcode)
4. [Method 3: Custom Plugin](#method-3-custom-plugin)
5. [Method 4: iFrame Embed](#method-4-iframe-embed)
6. [Method 5: Block Editor (Gutenberg)](#method-5-block-editor-gutenberg)
7. [Styling and Customization](#styling-and-customization)
8. [Troubleshooting](#troubleshooting)

## Integration Methods Overview

| Method | Difficulty | Best For | Pros | Cons |
|--------|-----------|----------|------|------|
| Page Template | Easy | Dedicated page | Full control, native WP integration | Requires theme access |
| Shortcode | Easy | Any page/post | Flexible placement | May conflict with theme styles |
| Custom Plugin | Medium | Portable solution | Theme-independent | Requires plugin development |
| iFrame | Very Easy | Quick embed | No file changes needed | Limited styling control |
| Block Editor | Medium | Gutenberg users | Modern WP experience | WP 5.0+ required |

## Method 1: Page Template (Recommended)

This method creates a custom page template that integrates seamlessly with your WordPress theme.

### Step 1: Copy Files to Theme

```bash
# Via SSH on your WordPress server
cd /path/to/wordpress/wp-content/themes/your-theme/

# Create template file
cp /path/to/MCWB/public_html/index.php page-mcwb-wiki.php

# Copy CSS
mkdir -p assets/css
cp /path/to/MCWB/public_html/style.css assets/css/mcwb-wiki.css
```

### Step 2: Modify Template Header

Edit `page-mcwb-wiki.php` and update the header:

```php
<?php
/**
 * Template Name: MCWB Weather Bot Wiki
 * Description: MeshCore Weather Bot documentation page
 */

get_header();
?>
```

### Step 3: Enqueue Styles

Add to your theme's `functions.php`:

```php
function mcwb_enqueue_wiki_styles() {
    if (is_page_template('page-mcwb-wiki.php')) {
        wp_enqueue_style(
            'mcwb-wiki-style',
            get_template_directory_uri() . '/assets/css/mcwb-wiki.css',
            array(),
            '1.0.0'
        );
    }
}
add_action('wp_enqueue_scripts', 'mcwb_enqueue_wiki_styles');
```

### Step 4: Create Page in WordPress

1. Log into WordPress admin
2. Go to **Pages > Add New**
3. Enter title: "Weather Bot Wiki"
4. In **Page Attributes** (right sidebar), select **Template: MCWB Weather Bot Wiki**
5. Click **Publish**

### Step 5: Test

Visit your new page: `https://yoursite.com/weather-bot-wiki/`

## Method 2: Shortcode

Create a shortcode to embed the wiki content anywhere.

### Step 1: Add Shortcode Function

Add to your theme's `functions.php` or create a custom plugin:

```php
function mcwb_wiki_shortcode($atts) {
    // Extract shortcode attributes
    $atts = shortcode_atts(array(
        'section' => 'all',  // Can be: all, overview, features, installation, etc.
    ), $atts);
    
    // Enqueue styles
    wp_enqueue_style(
        'mcwb-wiki-style',
        get_template_directory_uri() . '/assets/css/mcwb-wiki.css'
    );
    
    // Start output buffering
    ob_start();
    
    // Include the template
    include(get_template_directory() . '/templates/mcwb-wiki-content.php');
    
    return ob_get_clean();
}
add_shortcode('mcwb_wiki', 'mcwb_wiki_shortcode');
```

### Step 2: Create Content Template

Create `templates/mcwb-wiki-content.php` in your theme directory with the content from `index.php` (the main wiki content section).

### Step 3: Use the Shortcode

In any page or post, add:

```
[mcwb_wiki]
```

Or show only a specific section:

```
[mcwb_wiki section="installation"]
```

### Step 4: Enhanced Shortcode with Section Filter

For more control, enhance the shortcode:

```php
function mcwb_wiki_shortcode($atts) {
    $atts = shortcode_atts(array(
        'section' => 'all',
    ), $atts);
    
    wp_enqueue_style('mcwb-wiki-style', get_template_directory_uri() . '/assets/css/mcwb-wiki.css');
    
    ob_start();
    
    $section = sanitize_key($atts['section']);
    
    // Include full wiki or specific section
    if ($section === 'all') {
        include(get_template_directory() . '/templates/mcwb-wiki-content.php');
    } else {
        include(get_template_directory() . '/templates/mcwb-wiki-sections/' . $section . '.php');
    }
    
    return ob_get_clean();
}
add_shortcode('mcwb_wiki', 'mcwb_wiki_shortcode');
```

## Method 3: Custom Plugin

Create a standalone plugin for theme-independent integration.

### Step 1: Create Plugin Directory

```bash
cd /path/to/wordpress/wp-content/plugins/
mkdir mcwb-wiki-plugin
cd mcwb-wiki-plugin
```

### Step 2: Create Main Plugin File

Create `mcwb-wiki-plugin.php`:

```php
<?php
/**
 * Plugin Name: MCWB Weather Bot Wiki
 * Plugin URI: https://github.com/hostyorkshire/MCWB
 * Description: Adds MeshCore Weather Bot documentation to your WordPress site
 * Version: 1.0.0
 * Author: Your Name
 * License: MIT
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class MCWB_Wiki_Plugin {
    
    private static $instance = null;
    
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    private function __construct() {
        add_action('init', array($this, 'register_post_type'));
        add_shortcode('mcwb_wiki', array($this, 'wiki_shortcode'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_styles'));
    }
    
    public function enqueue_styles() {
        wp_enqueue_style(
            'mcwb-wiki-style',
            plugin_dir_url(__FILE__) . 'assets/css/style.css',
            array(),
            '1.0.0'
        );
    }
    
    public function wiki_shortcode($atts) {
        $atts = shortcode_atts(array(
            'section' => 'all',
        ), $atts);
        
        ob_start();
        include(plugin_dir_path(__FILE__) . 'templates/wiki-content.php');
        return ob_get_clean();
    }
    
    public function register_post_type() {
        // Optional: Register custom post type for wiki pages
        register_post_type('mcwb_wiki', array(
            'labels' => array(
                'name' => 'MCWB Wiki',
                'singular_name' => 'Wiki Page'
            ),
            'public' => true,
            'has_archive' => true,
            'menu_icon' => 'dashicons-book',
            'supports' => array('title', 'editor', 'thumbnail')
        ));
    }
}

// Initialize plugin
MCWB_Wiki_Plugin::get_instance();
```

### Step 3: Create Plugin Structure

```bash
mkdir -p assets/css templates
cp /path/to/MCWB/public_html/style.css assets/css/
cp /path/to/MCWB/public_html/index.php templates/wiki-content.php
```

### Step 4: Activate Plugin

1. Go to WordPress admin
2. Navigate to **Plugins**
3. Find "MCWB Weather Bot Wiki"
4. Click **Activate**

### Step 5: Use the Plugin

Add `[mcwb_wiki]` to any page or post.

## Method 4: iFrame Embed

Simplest method - embed the standalone HTML page in an iframe.

### Step 1: Upload Files

Upload `public_html` folder to your WordPress site:

```bash
# Via FTP or SSH
cp -r /path/to/MCWB/public_html /path/to/wordpress/wp-content/uploads/mcwb-wiki/
```

### Step 2: Create Page with iFrame

In WordPress, create a new page and add this HTML:

```html
<iframe 
    src="/wp-content/uploads/mcwb-wiki/index.html" 
    width="100%" 
    height="3000px" 
    frameborder="0"
    style="border: none;">
</iframe>
```

### Step 3: Make Responsive (Optional)

Add this CSS to your theme's Custom CSS (Appearance > Customize > Additional CSS):

```css
.mcwb-wiki-iframe {
    width: 100%;
    height: 0;
    padding-bottom: 100%; /* Adjust as needed */
    position: relative;
}

.mcwb-wiki-iframe iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: none;
}
```

Use it:

```html
<div class="mcwb-wiki-iframe">
    <iframe src="/wp-content/uploads/mcwb-wiki/index.html"></iframe>
</div>
```

## Method 5: Block Editor (Gutenberg)

Create a custom Gutenberg block for modern WordPress.

### Step 1: Create Block Plugin

Create `mcwb-wiki-block/mcwb-wiki-block.php`:

```php
<?php
/**
 * Plugin Name: MCWB Wiki Block
 * Description: Gutenberg block for MCWB Weather Bot Wiki
 * Version: 1.0.0
 */

function mcwb_register_wiki_block() {
    if (!function_exists('register_block_type')) {
        return;
    }
    
    wp_register_script(
        'mcwb-wiki-block',
        plugins_url('block.js', __FILE__),
        array('wp-blocks', 'wp-element', 'wp-editor'),
        filemtime(plugin_dir_path(__FILE__) . 'block.js')
    );
    
    wp_register_style(
        'mcwb-wiki-style',
        plugins_url('style.css', __FILE__),
        array(),
        filemtime(plugin_dir_path(__FILE__) . 'style.css')
    );
    
    register_block_type('mcwb/wiki-block', array(
        'editor_script' => 'mcwb-wiki-block',
        'style' => 'mcwb-wiki-style',
        'render_callback' => 'mcwb_render_wiki_block',
    ));
}
add_action('init', 'mcwb_register_wiki_block');

function mcwb_render_wiki_block($attributes) {
    ob_start();
    include(plugin_dir_path(__FILE__) . 'templates/wiki-content.php');
    return ob_get_clean();
}
```

### Step 2: Create Block JavaScript

Create `block.js`:

```javascript
(function(blocks, element, editor) {
    var el = element.createElement;
    
    blocks.registerBlockType('mcwb/wiki-block', {
        title: 'MCWB Wiki',
        icon: 'book',
        category: 'widgets',
        
        edit: function() {
            return el('div', {
                className: 'mcwb-wiki-placeholder'
            }, 'MCWB Weather Bot Wiki will appear here');
        },
        
        save: function() {
            return null; // Rendered via PHP
        }
    });
})(
    window.wp.blocks,
    window.wp.element,
    window.wp.editor
);
```

### Step 3: Use the Block

1. Edit a page in WordPress
2. Click the **+** button to add a block
3. Search for "MCWB Wiki"
4. Add the block

## Styling and Customization

### Override Theme Styles

If your theme's styles conflict with the wiki, add this to your `functions.php`:

```php
function mcwb_wiki_override_styles() {
    $custom_css = "
        .wiki-content * {
            box-sizing: border-box;
        }
        .wiki-content a {
            color: #0066cc;
        }
        /* Add more overrides as needed */
    ";
    wp_add_inline_style('mcwb-wiki-style', $custom_css);
}
add_action('wp_enqueue_scripts', 'mcwb_wiki_override_styles');
```

### Match Your Theme's Colors

Edit `style.css` variables to match your theme:

```css
:root {
    --primary-color: #your-theme-primary-color;
    --secondary-color: #your-theme-secondary-color;
    /* etc. */
}
```

Or use WordPress Customizer settings:

```php
function mcwb_wiki_custom_colors() {
    $primary_color = get_theme_mod('primary_color', '#0066cc');
    
    $custom_css = "
        :root {
            --primary-color: {$primary_color};
        }
    ";
    wp_add_inline_style('mcwb-wiki-style', $custom_css);
}
add_action('wp_enqueue_scripts', 'mcwb_wiki_custom_colors');
```

### Add to WordPress Menu

After creating your wiki page, add it to your WordPress menu:

1. Go to **Appearance > Menus**
2. Select your menu
3. Find your wiki page in the left sidebar
4. Click **Add to Menu**
5. Save

## Troubleshooting

### Styles Not Loading

**Check if CSS file exists:**
```bash
ls /path/to/wordpress/wp-content/themes/your-theme/assets/css/mcwb-wiki.css
```

**Clear WordPress cache:**
- If using a caching plugin, clear the cache
- Hard refresh browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)

**Check browser console for errors:**
- Press F12 in browser
- Look for 404 errors in Network tab

### Template Not Showing

**Verify file location:**
```bash
ls /path/to/wordpress/wp-content/themes/your-theme/page-mcwb-wiki.php
```

**Check file permissions:**
```bash
chmod 644 /path/to/wordpress/wp-content/themes/your-theme/page-mcwb-wiki.php
```

**Refresh permalinks:**
1. Go to **Settings > Permalinks**
2. Click **Save Changes** (don't change anything)

### Content Not Displaying

**Check PHP errors:**
```bash
tail -f /var/log/apache2/error.log
# or
tail -f /var/log/nginx/error.log
```

**Enable WordPress debugging:**

Edit `wp-config.php`:
```php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);
```

Check logs at: `wp-content/debug.log`

### Shortcode Not Working

**Verify shortcode is registered:**

Add temporary debug code to `functions.php`:
```php
add_action('init', function() {
    global $shortcode_tags;
    error_log('Registered shortcodes: ' . print_r(array_keys($shortcode_tags), true));
});
```

**Check for shortcode conflicts:**

Some plugins may interfere. Try disabling other plugins temporarily.

### Layout Broken in WordPress

**Wrap content in container:**

```php
echo '<div class="mcwb-wiki-wrapper">';
// wiki content here
echo '</div>';
```

Add CSS:
```css
.mcwb-wiki-wrapper {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}
```

## Best Practices

1. **Use Child Theme**: Always add customizations to a child theme, not the main theme
2. **Version Control**: Keep track of your modifications with git
3. **Testing**: Test on a staging site before deploying to production
4. **Backups**: Always backup before making changes
5. **Updates**: Keep WordPress, themes, and plugins updated
6. **Performance**: Use caching plugins (WP Super Cache, W3 Total Cache)
7. **Security**: Keep files and folders with proper permissions

## Example Child Theme Setup

Create a child theme for safe customizations:

### 1. Create Child Theme Directory

```bash
cd /path/to/wordpress/wp-content/themes/
mkdir your-theme-child
cd your-theme-child
```

### 2. Create style.css

```css
/*
Theme Name: Your Theme Child
Template: your-theme
*/

@import url("../your-theme/style.css");

/* MCWB Wiki specific styles */
@import url("assets/css/mcwb-wiki.css");
```

### 3. Create functions.php

```php
<?php
function child_theme_enqueue_styles() {
    wp_enqueue_style('parent-style', get_template_directory_uri() . '/style.css');
    wp_enqueue_style('child-style', get_stylesheet_uri());
}
add_action('wp_enqueue_scripts', 'child_theme_enqueue_styles');

// Add MCWB wiki functions here
include_once('includes/mcwb-wiki-functions.php');
```

### 4. Activate Child Theme

1. Go to **Appearance > Themes**
2. Activate your child theme

## Additional Resources

- [WordPress Theme Development](https://developer.wordpress.org/themes/)
- [WordPress Plugin Development](https://developer.wordpress.org/plugins/)
- [Gutenberg Block Development](https://developer.wordpress.org/block-editor/)
- [WordPress Shortcode API](https://codex.wordpress.org/Shortcode_API)
- [WordPress Template Hierarchy](https://developer.wordpress.org/themes/basics/template-hierarchy/)

## Support

For issues specific to the MCWB wiki integration:
- GitHub: https://github.com/hostyorkshire/MCWB/issues
- Documentation: See other guides in `public_html/`

For WordPress-specific issues:
- WordPress Support Forums: https://wordpress.org/support/
- WordPress Stack Exchange: https://wordpress.stackexchange.com/
