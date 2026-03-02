"""
Pytest configuration and shared fixtures for the MCWB test suite.
"""

import os
from pathlib import Path

import pytest

# Paths to shared state files that must be cleaned between tests
_LOGS_DIR = Path(__file__).parent.parent / "logs"
_CHANNELS_FILE = _LOGS_DIR / "channels.json"
_LAST_WEATHER_CHANNEL_FILE = _LOGS_DIR / ".last_weather_channel"


@pytest.fixture(autouse=True)
def clean_shared_state():
    """Remove shared state files before and after each test.

    The channels.json and .last_weather_channel files persist between test
    runs and cause state pollution: a WeatherBot created in one test will
    load data written by a previous test, leading to unexpected channel
    indices and _weather_channel_detected values.
    """
    for path in (_CHANNELS_FILE, _LAST_WEATHER_CHANNEL_FILE):
        if path.exists():
            path.unlink()
    yield
    for path in (_CHANNELS_FILE, _LAST_WEATHER_CHANNEL_FILE):
        if path.exists():
            path.unlink()
