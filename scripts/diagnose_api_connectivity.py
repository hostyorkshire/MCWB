#!/usr/bin/env python3
"""
API Connectivity Diagnostic Tool

This script helps identify whether weather lookup failures are caused by:
1. Network connectivity issues (cannot reach the internet)
2. DNS resolution problems (cannot resolve api.open-meteo.com)
3. API service being down or slow
4. Bot code issues
5. Firewall/proxy blocking the connection

Usage:
    python3 diagnose_api_connectivity.py
    python3 diagnose_api_connectivity.py --location York --country UK
"""

import argparse
import socket
import sys
import time

try:
    import requests
except ImportError:
    print("❌ Error: requests module not installed")
    print("   Install with: pip install requests")
    sys.exit(1)


def test_dns_resolution(hostname):
    """Test if we can resolve the hostname to an IP address."""
    print(f"\n{'='*70}")
    print(f"TEST 1: DNS Resolution for {hostname}")
    print("=" * 70)

    try:
        ip_address = socket.gethostbyname(hostname)
        print(f"✅ PASS: {hostname} resolves to {ip_address}")
        return True
    except socket.gaierror as e:
        print(f"❌ FAIL: Cannot resolve {hostname}")
        print(f"   Error: {e}")
        print("   Possible causes:")
        print("   - No internet connection")
        print("   - DNS server not configured")
        print("   - /etc/resolv.conf issues (Linux)")
        return False


def test_tcp_connection(hostname, port=443):
    """Test if we can establish a TCP connection to the host."""
    print(f"\n{'='*70}")
    print(f"TEST 2: TCP Connection to {hostname}:{port}")
    print("=" * 70)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((hostname, port))
        sock.close()

        if result == 0:
            print(f"✅ PASS: Can connect to {hostname}:{port}")
            return True
        else:
            print(f"❌ FAIL: Cannot connect to {hostname}:{port}")
            print(f"   Error code: {result}")
            print("   Possible causes:")
            print(f"   - Firewall blocking port {port}")
            print("   - Host is down")
            print("   - Network routing issues")
            return False
    except socket.timeout:
        print(f"❌ FAIL: Connection timeout to {hostname}:{port}")
        print("   Possible causes:")
        print("   - Network is very slow")
        print("   - Firewall silently dropping packets")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error connecting to {hostname}:{port}")
        print(f"   Error: {e}")
        return False


def test_http_request(url, params=None):
    """Test if we can make an HTTP request and get a response."""
    print(f"\n{'='*70}")
    print(f"TEST 3: HTTP Request to {url}")
    print("=" * 70)

    if params:
        print(f"Parameters: {params}")

    try:
        start_time = time.time()
        response = requests.get(url, params=params, timeout=10)
        elapsed = time.time() - start_time

        print(f"✅ HTTP Status: {response.status_code}")
        print(f"⏱️  Response time: {elapsed:.2f} seconds")

        if response.status_code == 200:
            print("✅ PASS: Request successful")
            return True, response
        else:
            print("⚠️  WARNING: Non-200 status code")
            print(f"   Response: {response.text[:200]}")
            return False, response

    except requests.exceptions.Timeout:
        print("❌ FAIL: Request timeout (>10 seconds)")
        print("   Possible causes:")
        print("   - API is very slow")
        print("   - Network congestion")
        print("   - Proxy/firewall delaying traffic")
        return False, None

    except requests.exceptions.ConnectionError as e:
        print("❌ FAIL: Connection error")
        print(f"   Error: {e}")
        print("   Possible causes:")
        print("   - Cannot reach API server")
        print("   - SSL/TLS issues")
        print("   - Network down")
        return False, None

    except requests.exceptions.SSLError as e:
        print("❌ FAIL: SSL/TLS error")
        print(f"   Error: {e}")
        print("   Possible causes:")
        print("   - Certificate verification failed")
        print("   - Outdated SSL libraries")
        print("   - Corporate proxy intercepting HTTPS")
        return False, None

    except Exception as e:
        print("❌ FAIL: Unexpected error")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error: {e}")
        return False, None


def test_geocoding_api(location, country=None):
    """Test the geocoding API specifically."""
    print(f"\n{'='*70}")
    print(f"TEST 4: Geocoding API for '{location}'" + (f" in {country}" if country else ""))
    print("=" * 70)

    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": location, "count": 1, "language": "en", "format": "json"}

    if country:
        params["country"] = country

    success, response = test_http_request(url, params)

    if success and response:
        try:
            data = response.json()
            if "results" in data and data["results"]:
                result = data["results"][0]
                print("\n✅ Location found:")
                print(f"   Name: {result.get('name')}")
                print(f"   Country: {result.get('country')} ({result.get('country_code')})")
                print(f"   Coordinates: {result.get('latitude')}, {result.get('longitude')}")
                return True
            else:
                print(f"\n⚠️  Location '{location}' not found in API database")
                return False
        except Exception as e:
            print(f"\n❌ Error parsing response: {e}")
            print(f"   Response: {response.text[:200]}")
            return False

    return False


def test_weather_api(lat=53.9599, lon=-1.0873):
    """Test the weather forecast API."""
    print(f"\n{'='*70}")
    print(f"TEST 5: Weather API for coordinates ({lat}, {lon})")
    print("=" * 70)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
        "timezone": "auto",
    }

    success, response = test_http_request(url, params)

    if success and response:
        try:
            data = response.json()
            if "current" in data:
                current = data["current"]
                print("\n✅ Weather data received:")
                print(f"   Temperature: {current.get('temperature_2m')}°C")
                print(f"   Humidity: {current.get('relative_humidity_2m')}%")
                print(f"   Wind: {current.get('wind_speed_10m')} km/h")
                return True
            else:
                print("\n⚠️  No current weather data in response")
                return False
        except Exception as e:
            print(f"\n❌ Error parsing response: {e}")
            return False

    return False


def main():
    parser = argparse.ArgumentParser(description="Diagnose API connectivity issues for the weather bot")
    parser.add_argument("--location", default="York", help="Location to test geocoding with (default: York)")
    parser.add_argument("--country", default="UK", help="Country code for geocoding test (default: UK)")

    args = parser.parse_args()

    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "API Connectivity Diagnostic Tool" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")

    results = []

    # Test 1: DNS resolution for geocoding API
    results.append(("DNS (geocoding)", test_dns_resolution("geocoding-api.open-meteo.com")))

    # Test 2: DNS resolution for weather API
    results.append(("DNS (weather)", test_dns_resolution("api.open-meteo.com")))

    # Test 3: TCP connection to geocoding API
    results.append(("TCP Connection", test_tcp_connection("geocoding-api.open-meteo.com", 443)))

    # Test 4: Geocoding API request
    results.append(("Geocoding API", test_geocoding_api(args.location, args.country)))

    # Test 5: Weather API request
    results.append(("Weather API", test_weather_api()))

    # Summary
    print(f"\n{'='*70}")
    print("DIAGNOSTIC SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)

    print(f"\nResults: {passed_tests}/{total_tests} tests passed")

    print(f"\n{'='*70}")
    print("DIAGNOSIS")
    print("=" * 70)

    if passed_tests == total_tests:
        print("✅ All tests passed!")
        print("   The bot should be able to fetch weather data successfully.")
        print("   If you're still seeing errors, they may be intermittent.")

    elif not results[0][1] or not results[1][1]:
        print("❌ DNS Resolution Failed")
        print("   The system cannot resolve API hostnames to IP addresses.")
        print()
        print("   LIKELY CAUSES:")
        print("   1. No internet connection")
        print("   2. DNS server not configured or unreachable")
        print("   3. /etc/resolv.conf not configured (Linux)")
        print()
        print("   SOLUTIONS:")
        print("   • Check internet connection: ping 8.8.8.8")
        print("   • Check DNS: cat /etc/resolv.conf")
        print("   • Try Google DNS: echo 'nameserver 8.8.8.8' >> /etc/resolv.conf")

    elif not results[2][1]:
        print("❌ TCP Connection Failed")
        print("   DNS works, but cannot establish connection to API.")
        print()
        print("   LIKELY CAUSES:")
        print("   1. Firewall blocking outbound HTTPS (port 443)")
        print("   2. Corporate proxy requiring configuration")
        print("   3. API service is down")
        print()
        print("   SOLUTIONS:")
        print("   • Check firewall rules: sudo iptables -L")
        print("   • Test with curl: curl -v https://api.open-meteo.com")
        print("   • Check if proxy needed: echo $https_proxy")

    elif not results[3][1]:
        print("❌ Geocoding API Failed")
        print("   Network connection works, but geocoding API has issues.")
        print()
        print("   LIKELY CAUSES:")
        print("   1. API rate limiting (too many requests)")
        print("   2. API service temporarily down")
        print("   3. SSL/TLS certificate issues")
        print()
        print("   SOLUTIONS:")
        print("   • Wait a few minutes and try again")
        print("   • Check API status: https://status.open-meteo.com")
        print("   • Update CA certificates: sudo apt-get install ca-certificates")

    elif not results[4][1]:
        print("❌ Weather API Failed")
        print("   Geocoding works, but weather forecast API has issues.")
        print()
        print("   LIKELY CAUSES:")
        print("   1. Different API endpoint blocked by firewall")
        print("   2. Weather API service temporarily down")
        print()
        print("   SOLUTIONS:")
        print("   • Check if both APIs work: compare test results")
        print("   • Wait and retry")

    else:
        print("⚠️  Partial Success")
        print("   Some tests passed, some failed.")
        print("   Review individual test results above for details.")

    print()

    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())
