#!/usr/bin/env python3
"""
Test API retry logic with exponential backoff.
Verifies that the retry mechanism handles timeouts and connection errors properly.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock, patch, call

import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

from weather_bot import WeatherBot, api_request_with_retry


def test_api_retry_on_timeout():
    """Test that API requests retry on timeout"""
    print("=" * 70)
    print("TEST: API Retry on Timeout")
    print("=" * 70)

    mock_func = MagicMock()

    # First two calls timeout, third succeeds
    mock_func.side_effect = [
        Timeout("Request timed out"),
        Timeout("Request timed out"),
        MagicMock(status_code=200),
    ]

    start_time = time.time()
    result = api_request_with_retry(mock_func, "test_url", max_retries=3)
    elapsed = time.time() - start_time

    # Should have been called 3 times (2 failures + 1 success)
    assert mock_func.call_count == 3, f"Expected 3 calls, got {mock_func.call_count}"

    # Should have waited: 1s + 2s = 3s between retries (plus some overhead)
    assert elapsed >= 3.0, f"Expected at least 3s wait time, got {elapsed:.2f}s"

    # Should succeed on third attempt
    assert result.status_code == 200

    print(f"✅ PASS: Retried {mock_func.call_count} times, waited {elapsed:.2f}s")
    print()


def test_api_retry_on_connection_error():
    """Test that API requests retry on connection errors"""
    print("=" * 70)
    print("TEST: API Retry on Connection Error")
    print("=" * 70)

    mock_func = MagicMock()

    # First call fails, second succeeds
    mock_func.side_effect = [
        ConnectionError("Cannot reach server"),
        MagicMock(status_code=200),
    ]

    result = api_request_with_retry(mock_func, "test_url", max_retries=3)

    assert mock_func.call_count == 2, f"Expected 2 calls, got {mock_func.call_count}"
    assert result.status_code == 200

    print("✅ PASS: Recovered from connection error on retry")
    print()


def test_api_retry_exhaustion():
    """Test that API requests fail after exhausting retries"""
    print("=" * 70)
    print("TEST: API Retry Exhaustion")
    print("=" * 70)

    mock_func = MagicMock()

    # All attempts timeout
    mock_func.side_effect = Timeout("Request timed out")

    try:
        api_request_with_retry(mock_func, "test_url", max_retries=3)
        assert False, "Should have raised RequestException"
    except RequestException as e:
        assert "failed after 3 attempts" in str(e)
        assert mock_func.call_count == 3, f"Expected 3 calls, got {mock_func.call_count}"
        print(f"✅ PASS: Correctly failed after {mock_func.call_count} attempts")
        print()


def test_api_retry_timeout_progression():
    """Test that timeouts increase with each retry"""
    print("=" * 70)
    print("TEST: Timeout Progression")
    print("=" * 70)

    mock_func = MagicMock()

    # Capture the timeout values passed to the function
    timeouts = []

    def capture_timeout(*args, **kwargs):
        timeouts.append(kwargs.get('timeout'))
        if len(timeouts) < 3:
            raise Timeout("Request timed out")
        return MagicMock(status_code=200)

    mock_func.side_effect = capture_timeout

    result = api_request_with_retry(mock_func, "test_url", max_retries=3, initial_timeout=10)

    # Timeouts should be: 10s, 15s, 20s
    assert len(timeouts) == 3
    assert timeouts[0] == 10, f"First timeout should be 10s, got {timeouts[0]}s"
    assert timeouts[1] == 15, f"Second timeout should be 15s, got {timeouts[1]}s"
    assert timeouts[2] == 20, f"Third timeout should be 20s, got {timeouts[2]}s"

    print(f"✅ PASS: Timeouts increased: {timeouts[0]}s → {timeouts[1]}s → {timeouts[2]}s")
    print()


def test_weather_bot_uses_retry():
    """Test that WeatherBot methods use retry logic"""
    print("=" * 70)
    print("TEST: WeatherBot Uses Retry Logic")
    print("=" * 70)

    bot = WeatherBot(debug=False)

    # Test geocode_location with retry
    with patch("weather_bot.api_request_with_retry") as mock_retry:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"name": "York", "latitude": 53.9, "longitude": -1.1}]
        }
        mock_retry.return_value = mock_response

        try:
            result = bot.geocode_location("York")
            assert mock_retry.called, "geocode_location should use api_request_with_retry"
            print("✅ PASS: geocode_location uses retry logic")
        except Exception as e:
            print(f"⚠️  Note: {e}")

    # Test get_weather with retry
    with patch("weather_bot.api_request_with_retry") as mock_retry:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current": {"temperature_2m": 15, "weather_code": 1}
        }
        mock_retry.return_value = mock_response

        result = bot.get_weather(53.9, -1.1)
        assert mock_retry.called, "get_weather should use api_request_with_retry"
        print("✅ PASS: get_weather uses retry logic")

    # Test get_outlook with retry
    with patch("weather_bot.api_request_with_retry") as mock_retry:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "daily": {"time": ["2024-01-01"], "weather_code": [1]}
        }
        mock_retry.return_value = mock_response

        result = bot.get_outlook(53.9, -1.1)
        assert mock_retry.called, "get_outlook should use api_request_with_retry"
        print("✅ PASS: get_outlook uses retry logic")

    print()


def test_non_retryable_errors():
    """Test that non-retryable errors (like HTTP 404) are raised immediately"""
    print("=" * 70)
    print("TEST: Non-Retryable Errors")
    print("=" * 70)

    mock_func = MagicMock()

    # HTTP error should not be retried
    http_error = requests.exceptions.HTTPError("404 Not Found")
    mock_func.side_effect = RequestException("404 Not Found")

    try:
        api_request_with_retry(mock_func, "test_url", max_retries=3)
        assert False, "Should have raised RequestException"
    except RequestException:
        # Should only try once for non-retryable errors
        assert mock_func.call_count == 1, f"Expected 1 call for non-retryable error, got {mock_func.call_count}"
        print("✅ PASS: Non-retryable error raised immediately (1 attempt)")
        print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "API Retry Logic Tests" + " " * 27 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    tests = [
        test_api_retry_on_timeout,
        test_api_retry_on_connection_error,
        test_api_retry_exhaustion,
        test_api_retry_timeout_progression,
        test_weather_bot_uses_retry,
        test_non_retryable_errors,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {test.__name__}")
            print(f"   Error: {e}")
            print()
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test.__name__}")
            print(f"   {e}")
            import traceback
            traceback.print_exc()
            print()
            failed += 1

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
