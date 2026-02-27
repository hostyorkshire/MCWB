# Security Anonymization Documentation

This document describes the security anonymization performed on this repository to protect sensitive information used during development.

## Purpose

During the development of MCWB, real production values were used in examples and documentation. This posed a security risk if the repository was made public or shared. This anonymization effort ensures that all examples use safe placeholder values.

## Changes Made

### 1. Domain Names
- **Before:** `wx.intergalactic.it.com` (real production domain)
- **After:** `weather.example.com` (RFC 2606 compliant example domain)
- **Files Affected:** 17 files including documentation, scripts, and website files
- **Reason:** Exposing the real domain could allow attackers to discover the production infrastructure

### 2. IP Addresses
- **Before:** `192.168.1.109` (specific local IP address)
- **After:** `192.168.1.100` (generic example IP)
- **Files Affected:** 23 files including all documentation
- **Reason:** While 192.168.x.x is private, using a consistent specific IP could reveal internal network topology

### 3. GitHub Username
- **Before:** `hostyorkshire` (real GitHub username)
- **After:** `yourusername` (generic placeholder)
- **Files Affected:** 24 files (excluding LICENSE which retains original copyright)
- **Reason:** Linking repository examples to a specific user account could enable targeted attacks

### 4. Email Addresses
- **Before:** `your_email@gmail.com` (template using Gmail)
- **After:** `your.email@example.com` (RFC 2606 compliant example)
- **Files Affected:** 1 file (SSH_REMOTE_ACCESS.md)
- **Reason:** Using example.com makes it clear these are placeholders and prevents accidental misconfiguration

## Important Notes

### License Preservation
The `LICENSE` file retains the original copyright holder `hostyorkshire` as required for legal attribution. This is the ONLY file where the original username is preserved.

### User Action Required
When using this repository, users MUST replace the following placeholders with their actual values:

| Placeholder | Description | Example Replacement |
|-------------|-------------|-------------------|
| `weather.example.com` | Your actual domain | `weather.yourdomain.com` |
| `192.168.1.100` | Your local IP address | `192.168.1.25` |
| `yourusername` | Your GitHub username | `yourname` |
| `your.email@example.com` | Your email address | `you@yourdomain.com` |

### Security Best Practices
1. **Never commit real credentials** to any repository (public or private)
2. **Use environment variables** for sensitive configuration values
3. **Use `.gitignore`** to exclude files containing secrets
4. **Use placeholder domains** like `example.com`, `example.org` for documentation
5. **Use RFC 1918 addresses** (192.168.x.x, 10.x.x.x) for internal IP examples
6. **Document clearly** when examples use placeholder values

## Files Modified

The anonymization affected the following categories:
- **Documentation:** 30+ markdown files
- **Website:** HTML, JavaScript, and configuration files in `public_html/wx/`
- **Scripts:** Shell scripts for installation and configuration
- **Code:** Python files with example configurations

## Verification

To verify no sensitive data remains, run:
```bash
# Check for old domain
grep -r "wx\.intergalactic" . --exclude-dir=.git

# Check for specific old IP
grep -r "192\.168\.1\.109" . --exclude-dir=.git

# Check for old username (excluding LICENSE)
grep -r "hostyorkshire" . --exclude-dir=.git | grep -v LICENSE

# Check for old email
grep -r "your_email@gmail" . --exclude-dir=.git
```

All commands should return no results (or only results from this documentation file).

## Security Scanning

This repository has been scanned with:
- **CodeQL:** No security vulnerabilities found
- **Code Review:** No sensitive information detected

## Contact

If you discover any remaining sensitive information that should be anonymized, please report it responsibly through:
- GitHub Issues (for non-sensitive reports)
- Private communication for sensitive discoveries

---

**Last Updated:** 2026-02-27  
**Reviewed By:** GitHub Copilot Security Agent
