#!/usr/bin/env python3
"""
Test to validate that systemd service files are clean and don't contain HTML entities.

This test ensures that service files in the repository don't have corrupted content
like HTML entities (&gt;, &lt;, &amp;) which would cause systemd errors.
"""

import os
import sys


def test_service_files_no_html_entities():
    """Verify that service files don't contain HTML entities"""
    print("=" * 60)
    print("TEST: Service Files - No HTML Entities")
    print("=" * 60)

    # Get the repository root (parent of tests directory)
    test_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(test_dir)

    # Service files to check
    service_files = [
        os.path.join(repo_root, "weather_bot.service"),
        os.path.join(repo_root, "mcwb-dashboard.service"),
    ]

    html_entities = ["&gt;", "&lt;", "&amp;", "&quot;", "&apos;"]
    errors = []

    for service_file in service_files:
        if not os.path.exists(service_file):
            print(f"⚠️  Service file not found: {service_file}")
            continue

        print(f"\n✓ Checking: {os.path.basename(service_file)}")

        with open(service_file, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        # Check for HTML entities
        for line_num, line in enumerate(lines, 1):
            for entity in html_entities:
                if entity in line:
                    error_msg = (
                        f"  ❌ Line {line_num}: Found HTML entity '{entity}' in {os.path.basename(service_file)}"
                    )
                    print(error_msg)
                    print(f"     Content: {line.strip()}")
                    errors.append(error_msg)

        # Check that section headers are properly formatted
        section_headers = ["[Unit]", "[Service]", "[Install]"]
        found_headers = []

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped in section_headers:
                found_headers.append(stripped)

        if not all(header in found_headers for header in section_headers):
            missing = [h for h in section_headers if h not in found_headers]
            error_msg = f"  ❌ Missing or malformed section headers in {os.path.basename(service_file)}: {missing}"
            print(error_msg)
            errors.append(error_msg)
        else:
            print(f"  ✓ All required section headers found: {', '.join(found_headers)}")

        # Verify the file is valid UTF-8
        try:
            content.encode("utf-8")
            print(f"  ✓ File is valid UTF-8")
        except UnicodeEncodeError as e:
            error_msg = f"  ❌ File contains invalid UTF-8: {e}"
            print(error_msg)
            errors.append(error_msg)

    print("\n" + "=" * 60)

    if errors:
        print(f"❌ FAILED: Found {len(errors)} error(s)")
        for error in errors:
            print(error)
        return False
    else:
        print("✅ PASSED: All service files are clean and properly formatted")
        return True


def main():
    """Run the service file validation test"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 14 + "Service File Validation" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        if test_service_files_no_html_entities():
            print("\n✅ All service file validation tests passed!")
            return 0
        else:
            print("\n❌ Service file validation failed!")
            return 1

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
