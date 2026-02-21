#!/usr/bin/env python3
"""
Demonstration script showing USB port auto-detection functionality
"""

import sys
from meshcore import find_serial_ports

def main():
    print("=" * 60)
    print("USB Port Auto-Detection Demo")
    print("=" * 60)
    print()
    
    print("Searching for available USB serial ports...")
    print()
    
    ports = find_serial_ports(debug=True)
    
    print()
    print("-" * 60)
    
    if ports:
        print(f"✓ Found {len(ports)} port(s):")
        for i, port in enumerate(ports, 1):
            print(f"  {i}. {port}")
        print()
        print("To use auto-detection with weather_bot:")
        print("  python3 weather_bot.py --port auto --baud 115200 -d")
        print()
        print("To use a specific port:")
        print(f"  python3 weather_bot.py --port {ports[0]} --baud 115200 -d")
    else:
        print("✗ No USB serial ports found.")
        print()
        print("Possible reasons:")
        print("  - No USB serial device connected")
        print("  - Device not recognized (check drivers)")
        print("  - Permission issues (add user to dialout group)")
        print()
        print("To check manually:")
        print("  ls -l /dev/ttyUSB* /dev/ttyACM*")
    
    print("-" * 60)
    print()
    
    return 0 if ports else 1

if __name__ == "__main__":
    sys.exit(main())
