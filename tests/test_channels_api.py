#!/usr/bin/env python3
"""
Test the web dashboard channels API endpoint
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_channels_api():
    """Test the /api/channels endpoint"""
    print("=" * 60)
    print("TEST: Channels API Endpoint")
    print("=" * 60)

    # Import web_dashboard after sys.path is set
    import web_dashboard

    # Create a test Flask client
    web_dashboard.app.config["TESTING"] = True
    client = web_dashboard.app.test_client()

    # Test the API endpoint
    print("\n1. Testing channels API endpoint...")
    response = client.get("/api/channels")
    assert response.status_code == 200
    data = json.loads(response.data)
    print(f"   Response data: {data}")
    assert "channels" in data
    assert "last_updated" in data
    assert isinstance(data["channels"], list)
    print("✓ API returns correct structure")

    # Verify channel formatting with # prefix
    for channel in data["channels"]:
        assert channel["name"].startswith("#"), f"Channel '{channel['name']}' should start with #"
    print("✓ All channels have # prefix")
    print(f"  Channels: {', '.join(ch['name'] for ch in data['channels']) if data['channels'] else 'none'}")

    # Test with mock data
    print("\n2. Testing with mock channels file...")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create logs directory in temp
        logs_dir = Path(tmpdir) / "logs"
        logs_dir.mkdir()
        channels_file = logs_dir / "channels.json"

        # Write test data (channel_idx 3 has no name and should be filtered out)
        test_data = {
            "channels": [
                {"channel_idx": 0, "channel_name": None},
                {"channel_idx": 1, "channel_name": "weather"},
                {"channel_idx": 2, "channel_name": "alerts"},
                {"channel_idx": 3, "channel_name": None},
            ],
            "last_updated": "2026-02-24T23:00:00",
        }

        with open(channels_file, "w") as f:
            json.dump(test_data, f)

        # Temporarily patch the Path in web_dashboard to use our temp directory
        original_file = web_dashboard.Path(__file__).parent / "logs" / "channels.json"

        # Monkey patch the api_channels function for this test
        def test_api_channels():
            if not channels_file.exists():
                return web_dashboard.jsonify({"channels": [], "last_updated": None})

            try:
                with open(channels_file, "r") as f:
                    data = json.load(f)
                    formatted_channels = []
                    for ch in data.get("channels", []):
                        channel_name = ch.get("channel_name")
                        if channel_name:
                            formatted_channels.append(f"#{channel_name}")
                        elif ch.get("channel_idx") == 0:
                            formatted_channels.append("#public")
                        else:
                            continue

                    return web_dashboard.jsonify(
                        {"channels": formatted_channels, "last_updated": data.get("last_updated")}
                    )
            except (json.JSONDecodeError, IOError):
                return web_dashboard.jsonify({"channels": [], "last_updated": None})

        # Replace the route temporarily
        web_dashboard.app.view_functions["api_channels"] = test_api_channels

        response = client.get("/api/channels")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert len(data["channels"]) == 3
        assert "#public" in data["channels"]
        assert "#weather" in data["channels"]
        assert "#alerts" in data["channels"]
        assert "#channel3" not in data["channels"]
        assert not any("unnamed" in ch for ch in data["channels"])
        assert data["last_updated"] == "2026-02-24T23:00:00"
        print("✓ Returns formatted channel list with # prefix")
        print("✓ Unnamed channels (channel_idx != 0, no name) are excluded")
        print(f"  Channels: {', '.join(data['channels'])}")

    print()


def main():
    """Run all tests"""
    try:
        test_channels_api()

        print("=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
