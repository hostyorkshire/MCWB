# Netlify Static Website Deployment Guide

This guide shows you how to set up automatic deployment of the **static documentation website** from GitHub to Netlify. The website at https://mcwb.netlify.app/ contains documentation and a demo dashboard - **no live data is transmitted** to keep hosting free and lightweight.

## Important: Demo Data Only

The static website on Netlify displays **demo data only**. This design choice:
- ✅ Keeps Netlify hosting completely free
- ✅ Eliminates resource usage and costs
- ✅ Avoids CORS and connectivity issues
- ✅ Provides fast, reliable documentation access

**For live bot monitoring**, users should access the web dashboard directly on their Raspberry Pi (see instructions on the dashboard page, including DDNS/No-IP setup for remote access).

## Prerequisites

- A GitHub account with access to the MCWB repository
- A Netlify account (free - sign up at https://netlify.com)

## Setup Steps

### 1. Sign in to Netlify

1. Go to https://app.netlify.com/
2. Sign in (or create an account if you don't have one)
3. You can sign in using your GitHub account for easier integration

### 2. Import Your GitHub Repository

1. Click **"Add new site"** button
2. Select **"Import an existing project"**
3. Choose **"Deploy with GitHub"**
4. If prompted, authorize Netlify to access your GitHub account
5. Search for and select the **`hostyorkshire/MCWB`** repository

### 3. Configure Build Settings

Netlify should automatically detect the settings from the `netlify.toml` file in the repository:

- **Base directory:** (leave empty)
- **Build command:** (leave empty - no build needed)
- **Publish directory:** `website`

If these are not auto-filled, enter them manually.

### 4. Deploy!

1. Click **"Deploy site"**
2. Netlify will deploy your site and assign a random URL (e.g., `random-name-123.netlify.app`)
3. Wait for the deployment to complete (usually takes 30-60 seconds)

### 5. Configure Custom Domain (Optional)

If you want to use `mcwb.netlify.app` instead of the random URL:

1. Go to **Site settings** → **Domain management**
2. Click **"Options"** → **"Edit site name"**
3. Change the site name to `mcwb`
4. Your site will now be available at https://mcwb.netlify.app/

## How Automatic Deployment Works

Once configured, Netlify will:

1. **Monitor your GitHub repository** for changes to the website
2. **Automatically deploy** when you push commits to the main branch
3. **Publish static files** from the `website` directory
4. **Update the live site** at https://mcwb.netlify.app/

The website contains only static HTML/CSS/JavaScript - no server-side processing or live data connections.

You don't need to do anything else - just commit and push website changes to GitHub as usual!

## Deployment Triggers

Deployments are triggered by:
- ✅ Pushing commits to the main branch
- ✅ Merging pull requests
- ✅ Any changes to files in the `website` directory

## Verifying Deployment

After pushing changes to GitHub:

1. Go to your Netlify dashboard
2. Click on your site
3. View the **"Deploys"** tab to see deployment status
4. Each deployment shows:
   - Commit message
   - Deploy time
   - Deploy status (Success/Failed)
   - Deploy preview URL

## Configuration File

This repository includes a `netlify.toml` file at the root that configures:
- Publish directory: `website`
- No build command (static HTML site)
- Security headers
- Production and preview deployment settings

## Troubleshooting

### Site Not Updating After Push

1. Check the Netlify Deploys tab for errors
2. Verify that your changes were pushed to the correct branch
3. Check that the branch is configured in Netlify (Site settings → Build & deploy → Continuous Deployment)

### Build Fails

Since this is a static site with no build process, builds should not fail. If they do:
1. Check the deploy log in Netlify
2. Verify the `website` directory exists and contains HTML files
3. Check that `netlify.toml` is in the repository root

### Want to Deploy from a Different Branch

1. Go to Site settings → Build & deploy → Continuous Deployment
2. Edit the "Production branch" setting
3. Select your preferred branch

## Additional Features

### Deploy Previews

Netlify automatically creates preview deployments for pull requests, allowing you to:
- Preview changes before merging
- Test on a temporary URL
- Review with team members

### Branch Deployments

You can configure Netlify to deploy other branches automatically:
1. Go to Site settings → Build & deploy → Continuous Deployment
2. Scroll to "Branch deploys"
3. Choose which branches to deploy automatically

### Custom Domain

To use a custom domain:
1. Go to Site settings → Domain management
2. Click "Add custom domain"
3. Follow the DNS configuration instructions

## Need Help?

- [Netlify Documentation](https://docs.netlify.com/)
- [Netlify Support](https://www.netlify.com/support/)
- [MCWB Issues](https://github.com/hostyorkshire/MCWB/issues)

## Summary

With this setup, your workflow is simple:
1. Make changes to files in the `website` directory
2. Commit and push to GitHub
3. Netlify automatically detects the changes and deploys
4. Your site at https://mcwb.netlify.app/ is updated!

That's it! ✨
