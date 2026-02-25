#!/usr/bin/env python3
"""
Generate self-signed SSL certificate for MCWB Dashboard
This creates a certificate valid for local network use on Raspberry Pi
"""

import sys
from pathlib import Path

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    import datetime
except ImportError:
    print("=" * 70)
    print("ERROR: cryptography package not installed")
    print("=" * 70)
    print()
    print("To generate SSL certificates, install cryptography:")
    print()
    print("    pip install cryptography")
    print()
    print("=" * 70)
    sys.exit(1)


def generate_self_signed_cert(cert_file="cert.pem", key_file="key.pem", hostname="192.168.1.109"):
    """Generate a self-signed certificate for local use"""
    
    print("=" * 70)
    print("Generating Self-Signed SSL Certificate")
    print("=" * 70)
    print()
    print(f"📁 Certificate will be saved to: {cert_file}")
    print(f"🔑 Private key will be saved to: {key_file}")
    print(f"🌐 Certificate valid for: {hostname}")
    print()
    
    # Generate private key
    print("🔧 Generating private key...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Generate certificate
    print("📝 Creating certificate...")
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Local"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Local"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"MCWB"),
        x509.NameAttribute(NameOID.COMMON_NAME, hostname),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        # Valid for 1 year
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(hostname),
            x509.DNSName("localhost"),
            x509.DNSName("raspberrypi.local"),
            x509.IPAddress(hostname.encode('utf-8') if not hostname.replace('.', '').isdigit() else 
                          __import__('ipaddress').IPv4Address(hostname)),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256(), default_backend())
    
    # Write certificate to file
    print(f"💾 Saving certificate to {cert_file}...")
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # Write private key to file
    print(f"💾 Saving private key to {key_file}...")
    with open(key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    print()
    print("✅ Certificate generated successfully!")
    print()
    print("=" * 70)
    print("IMPORTANT: Self-Signed Certificate Warning")
    print("=" * 70)
    print()
    print("⚠️  Browsers will show a security warning for self-signed certificates.")
    print("   This is normal and safe for local network use.")
    print()
    print("To use the certificate:")
    print()
    print("1. Start the dashboard with SSL:")
    print("   python3 web_dashboard.py --ssl")
    print()
    print("2. In your browser, accept the security warning:")
    print("   - Chrome: Click 'Advanced' → 'Proceed to [IP] (unsafe)'")
    print("   - Firefox: Click 'Advanced' → 'Accept the Risk and Continue'")
    print("   - Safari: Click 'Show Details' → 'visit this website'")
    print()
    print("3. For production use, consider:")
    print("   - Using a reverse proxy with Let's Encrypt (Caddy, nginx)")
    print("   - Using Cloudflare Tunnel for secure external access")
    print("   - Using ngrok for temporary external access")
    print()
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate SSL certificate for MCWB Dashboard")
    parser.add_argument("--cert", default="cert.pem", help="Certificate file path (default: cert.pem)")
    parser.add_argument("--key", default="key.pem", help="Private key file path (default: key.pem)")
    parser.add_argument("--hostname", default="192.168.1.109", 
                       help="Hostname or IP address for the certificate (default: 192.168.1.109)")
    
    args = parser.parse_args()
    
    try:
        generate_self_signed_cert(args.cert, args.key, args.hostname)
    except Exception as e:
        print(f"\n❌ Error generating certificate: {e}", file=sys.stderr)
        sys.exit(1)
