#!/usr/bin/env python3
"""
Comprehensive test runner for MCWB project
Runs all test files and reports results
"""

import subprocess
import sys
import time

# List of test files to run
TEST_FILES = [
    'test_usb_port_detection.py',
    'test_lora_serial.py',
    'test_listener_startup.py',
    'test_weather_bot.py',
    'test_channel_functionality.py',
    'test_multi_channel.py',
    'test_multi_channel_reply.py',
    'test_channel_reply_behavior.py',
    'test_channel_filter_fix.py',
    'test_no_channel_filtering.py',
    'test_weather_channel_filtering.py',
    'test_weather_channel_reply.py',
    'test_country_code_conversion.py',
    'test_label_shortening.py',
    'test_html_encoding.py',
    'test_json_parsing_edge_cases.py',
    'test_garbled_data_logging.py',
    'test_frame_codes.py',
    'test_frame_code_0x00.py',
    'test_frame_code_0x01.py',
    'test_bot_response.py',
]

def run_test(test_file):
    """Run a single test file and return result"""
    print(f"\n{'='*70}")
    print(f"Running: {test_file}")
    print('='*70)
    
    start_time = time.time()
    try:
        result = subprocess.run(
            ['python3', test_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✓ PASSED ({elapsed:.2f}s)")
            return True, elapsed
        else:
            print(f"✗ FAILED ({elapsed:.2f}s)")
            print("\nSTDOUT:")
            print(result.stdout)
            print("\nSTDERR:")
            print(result.stderr)
            return False, elapsed
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"✗ TIMEOUT ({elapsed:.2f}s)")
        return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"✗ ERROR: {e} ({elapsed:.2f}s)")
        return False, elapsed

def main():
    """Run all tests and report summary"""
    print("="*70)
    print("MCWB Comprehensive Test Suite")
    print("="*70)
    
    results = []
    total_time = 0
    
    for test_file in TEST_FILES:
        passed, elapsed = run_test(test_file)
        results.append((test_file, passed, elapsed))
        total_time += elapsed
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed_count = sum(1 for _, passed, _ in results if passed)
    failed_count = len(results) - passed_count
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Total Time: {total_time:.2f}s")
    
    if failed_count > 0:
        print("\nFailed Tests:")
        for test_file, passed, elapsed in results:
            if not passed:
                print(f"  ✗ {test_file}")
    
    print("\n" + "="*70)
    
    if failed_count == 0:
        print("✓ ALL TESTS PASSED!")
        print("="*70)
        return 0
    else:
        print(f"✗ {failed_count} TEST(S) FAILED")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
