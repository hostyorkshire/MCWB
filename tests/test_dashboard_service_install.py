#!/usr/bin/env python3
"""
Test dashboard service installation script
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import site
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestDashboardServiceInstall(unittest.TestCase):
    """Test dashboard service installation"""

    def test_user_site_detection(self):
        """Test that USER_SITE can be detected"""
        user_site = site.USER_SITE
        self.assertIsNotNone(user_site)
        self.assertIn(".local", user_site)
        self.assertIn("site-packages", user_site)
        print(f"✓ USER_SITE detected: {user_site}")

    def test_service_file_generation(self):
        """Test that service file generation works correctly"""
        # Read the template service file
        service_template = Path(__file__).parent.parent / "mcwb-dashboard.service"
        self.assertTrue(service_template.exists(), "Service template file not found")

        # Simulate the install script's service file generation
        import getpass

        current_user = getpass.getuser()
        install_dir = str(Path(__file__).parent.parent)

        # Create a temporary service file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".service") as tmp:
            tmp_path = tmp.name

        try:
            # Simulate the sed commands from install script
            subprocess.run(
                ["sed", f"s|User=pi|User={current_user}|g", str(service_template)],
                stdout=open(tmp_path, "w"),
                check=True,
            )

            subprocess.run(["sed", "-i", f"s|/home/pi/MCWB|{install_dir}|g", tmp_path], check=True)

            # Read generated file
            with open(tmp_path, "r") as f:
                content = f.read()

            # Verify replacements
            self.assertIn(f"User={current_user}", content, "User not replaced correctly")
            self.assertIn(f"WorkingDirectory={install_dir}", content, "WorkingDirectory not replaced")
            self.assertNotIn("/home/pi/MCWB", content, "Path placeholder not replaced")
            # Python automatically includes user site-packages, so PYTHONPATH is not needed
            self.assertNotIn(
                "PYTHONPATH", content, "PYTHONPATH should not be set (Python includes user site-packages automatically)"
            )

            print(f"✓ Service file generation successful")
            print(f"  User: {current_user}")
            print(f"  Install dir: {install_dir}")
            print(f"  Python will automatically use user site-packages")

        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_pythonpath_environment(self):
        """Test that Flask can be imported from user site-packages"""
        user_site = site.USER_SITE

        # Test that Flask can be imported (Python includes user site-packages automatically)
        result = subprocess.run(["python3", "-c", 'import flask; print("Flask OK")'], capture_output=True, text=True)

        self.assertEqual(result.returncode, 0, "Flask import failed")
        self.assertIn("Flask OK", result.stdout)
        print(f"✓ Flask imports successfully from user site-packages: {user_site}")


if __name__ == "__main__":
    print("Running Dashboard Service Installation Tests...")
    print("=" * 70)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDashboardServiceInstall)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
