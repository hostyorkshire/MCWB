# MCWB Tests

This directory contains all test files for the MeshCore Weather Bot (MCWB) project.

## Running Tests

To run all tests from the project root:

```bash
python3 run_all_tests.py
```

To run individual tests:

```bash
python3 tests/test_weather_bot.py
python3 tests/test_lora_serial.py
```

## Test Categories

- **Core functionality tests**: `test_weather_bot.py`, `test_bot_response.py`
- **Serial communication tests**: `test_lora_serial.py`, `test_usb_port_detection.py`
- **Channel functionality tests**: `test_channel_*.py`, `test_multi_channel*.py`
- **Message handling tests**: `test_frame_codes*.py`, `test_garbled_*.py`, `test_encrypted_*.py`
- **Location/country tests**: `test_country_*.py`, `test_york_ambiguity.py`

## Notes

All tests run in simulation mode and do not require physical hardware.
