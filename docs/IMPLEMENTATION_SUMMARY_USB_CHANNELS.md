# USB Port Auto-Detection and Channel Filtering - Implementation Summary

## Overview

This PR addresses two critical issues with the MCWB Weather Bot:

1. **USB Port Auto-Detection**: Bot stops listening after reboots due to USB port changes
2. **Channel Filtering Confusion**: Users experiencing issues with bot not responding on non-wxtest channels

## Changes Implemented

### 1. USB Port Auto-Detection

#### Problem
After a system reboot, USB device names can change (e.g., `/dev/ttyUSB1` → `/dev/ttyUSB0`), causing the bot to fail to connect and stop listening for messages.

#### Solution
- Added `find_serial_ports()` function in `meshcore.py` to detect available USB/ACM/AMA ports
- Modified `_connect_serial()` to automatically try available ports if the specified port fails
- Added support for `--port auto` CLI option in `weather_bot.py`
- Updated `weather_bot.service` to use `--port auto` for automatic port detection

#### Features
- Automatically detects available USB serial devices (ttyUSB*, ttyACM*, ttyAMA*)
- Falls back to alternative ports if primary port fails
- Sorts ports for consistent ordering
- Handles errors gracefully
- Logs all connection attempts for debugging

#### Usage
```bash
# Auto-detect available port
python3 weather_bot.py --port auto --baud 115200 -d

# Still supports specific port
python3 weather_bot.py --port /dev/ttyUSB0 --baud 115200 -d
```

### 2. Channel Filtering Investigation & Diagnostics

#### Problem
User reported: "filtering is making my script not connecting and getting responses in other channels apart from wxtest"

#### Root Cause Analysis
After investigation, identified potential confusion between two different parameters:
- `--channel`: Controls which channels the bot ACCEPTS queries FROM (filtering)
- `--announce-channel`: Controls where periodic announcements are SENT TO (default: wxtest)

#### Solution
- Verified bot correctly accepts queries from ALL channels by default (no `--channel` parameter)
- Created diagnostic tools to help identify misconfigurations
- Added comprehensive troubleshooting documentation
- Created test scripts to verify multi-channel behavior

#### Key Findings
1. **Default Behavior (Correct):**
   - Bot accepts queries from ALL channels
   - Bot replies on the SAME channel_idx where each query came from
   - Announcements go to wxtest channel (configurable)

2. **With --channel Parameter (Restrictive):**
   - Bot ONLY accepts queries from specified channel(s)
   - Queries from other channels are IGNORED
   - This is likely the source of user's problem

3. **Binary Protocol Messages:**
   - Messages with channel_idx but no channel name are accepted regardless of filter
   - This ensures physical radio channel messages work correctly

## Testing

### New Tests Created
1. `test_usb_port_detection.py` - 6 tests for USB port detection
2. `test_usb_edge_cases.py` - 4 tests for edge cases
3. `test_response_channels.py` - Verify multi-channel response behavior
4. Updated `test_weather_channel_filtering.py` - Corrected filtering expectations

### Test Results
- **Total Tests:** 21
- **Passed:** 21
- **Failed:** 0
- **All existing tests continue to pass**

### Code Quality
- ✅ No Python syntax errors
- ✅ All imports work correctly
- ✅ CodeQL security scan: 0 vulnerabilities
- ✅ Code review feedback addressed

## Documentation

### New Documentation
1. **CHANNEL_FILTERING_TROUBLESHOOTING.md** - Comprehensive guide for channel filtering issues
2. **Updated README.md** - Added USB port auto-detection information
3. **Updated README.md** - Added troubleshooting section for USB port issues

### Diagnostic Tools
1. **diagnose_channels.py** - Script to diagnose channel filtering configuration
2. **demo_usb_detection.py** - Demo script showing USB port detection
3. **run_all_tests.py** - Comprehensive test runner

## Files Changed

### Core Functionality
- `meshcore.py` - Added USB port detection and auto-connection retry logic
- `weather_bot.py` - Added support for `--port auto` option
- `weather_bot.service` - Updated to use `--port auto`

### Tests
- `test_usb_port_detection.py` (new)
- `test_usb_edge_cases.py` (new)
- `test_response_channels.py` (new)
- `test_weather_channel_filtering.py` (updated)
- `run_all_tests.py` (new)

### Documentation
- `README.md` (updated)
- `CHANNEL_FILTERING_TROUBLESHOOTING.md` (new)
- `diagnose_channels.py` (new)
- `demo_usb_detection.py` (new)

## How to Use

### For USB Port Issues After Reboot

1. Update your service file:
```bash
sudo nano /etc/systemd/system/weather_bot.service
```

2. Change `ExecStart` line to:
```
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --port auto --baud 115200 -d
```

3. Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart weather_bot
```

### For Channel Filtering Issues

1. Run the diagnostic:
```bash
python3 diagnose_channels.py
```

2. Check your configuration:
```bash
systemctl status weather_bot
journalctl -u weather_bot -n 50 | grep "Channel filter"
```

3. If you see "Channel filter enabled", remove the `--channel` parameter from your startup command

4. Verify correct behavior:
```bash
python3 test_response_channels.py
```

## Recommendations

### For Production Use
1. **Use auto-detection:** `--port auto` in service files
2. **Don't use --channel:** Unless you specifically want to filter incoming queries
3. **Configure announce-channel:** Set to desired announcement channel (default: wxtest)
4. **Enable debug mode:** Use `-d` flag for troubleshooting
5. **Monitor logs:** Use `journalctl -u weather_bot -f` to watch for issues

### Service File Template
```ini
[Unit]
Description=MeshCore Weather Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/MCWB
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --port auto --baud 115200 -d
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## Security Summary

### CodeQL Analysis
- **Alerts Found:** 0
- **Status:** ✅ No security vulnerabilities detected

### Security Considerations
- USB port detection uses pyserial's built-in port enumeration
- No external commands or shell injections
- Proper exception handling for all serial operations
- Graceful degradation when ports are not available

## Conclusion

This PR successfully addresses both reported issues:

1. ✅ **USB Port Auto-Detection:** Bot now automatically finds and connects to available USB ports, preventing connection failures after reboots

2. ✅ **Channel Filtering:** Clarified the distinction between channel filtering and announcement channels, provided diagnostic tools, and verified correct multi-channel behavior

The bot now:
- Automatically adapts to USB port changes
- Accepts queries from all channels by default
- Replies on the correct channel for each query
- Provides clear diagnostics for troubleshooting
- Maintains backward compatibility with existing configurations

All tests pass, code quality is verified, and no security vulnerabilities were found.
