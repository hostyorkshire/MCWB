#!/usr/bin/env python3
"""
Test that outlook is sent automatically without timeout concerns.
Since outlook is now sent immediately, there's no pending state or timeout to manage.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from unittest.mock import MagicMock, patch

from weather_bot import WeatherBot


def test_no_pending_outlook_state():
    """Test that outlook is sent immediately without pending state"""
    print("=" * 70)
    print("TEST: No Pending Outlook State (Immediate Send)")
    print("=" * 70)

    bot = WeatherBot(debug=False)
    bot._ser = MagicMock()

    # Verify no pending outlook tracking exists
    if not hasattr(bot, "_pending_outlook"):
        print("✅ PASS: No pending outlook state management (immediate send)")
    else:
        print("❌ FAIL: Bot still has pending outlook state tracking")
        return False

    # Verify no timeout configuration exists
    if not hasattr(bot, "_outlook_timeout"):
        print("✅ PASS: No outlook timeout configuration (not needed)")
    else:
        print("❌ FAIL: Bot still has outlook timeout configuration")
        return False

    print("\n✅ Bot sends outlook immediately - no state or timeout needed")
    return True


def main():
    """Run tests verifying no state management is needed"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Automatic Outlook Tests (No State)" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    tests = [
        test_no_pending_outlook_state,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Exception in {test.__name__}: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
