# LED Indicators Fix Summary

## Problem Statement

The color LED activity indicators did not work on the DollaTek ESP32 SX1276 Wireless Bridge when flashed with Heltec v2 firmware (1.13.0).

## Root Cause Analysis

The issue was caused by incorrect GPIO pin assumptions in the original implementation:

### Original (Incorrect) Configuration
- Blue LED: GPIO25 ✓ (correct)
- Green LED: GPIO26 ✗ (conflicts with LoRa DIO0)
- Red LED: GPIO27 ✗ (conflicts with LoRa MOSI)

### Hardware Reality
The DollaTek ESP32 SX1276 and most ESP32 LoRa boards use specific GPIO pins for the SX1276 LoRa module:

| GPIO Pin | Hardware Usage | Available for LED? |
|----------|----------------|-------------------|
| GPIO25 | Onboard LED | ✅ Yes |
| GPIO26 | LoRa DIO0 (interrupt) | ❌ No - causes LoRa failures |
| GPIO27 | LoRa MOSI (SPI data) | ❌ No - causes LoRa failures |

Attempting to control LEDs on GPIO26/27 would interfere with LoRa communication.

## Solution Implemented

### 1. Board Variant System

Added a flexible board variant system with presets:

```python
BOARD_VARIANTS = {
    "dollatek": {
        "blue": 25,    # Only LED available
        "green": None, # GPIO26 used by LoRa
        "red": None,   # GPIO27 used by LoRa
    },
    "heltec-v2": {
        "blue": 25,    # Only LED available
        "green": None, # GPIO26 used by LoRa
        "red": None,   # GPIO27 used by LoRa
    },
}
```

### 2. Safe Default Configuration

Changed defaults to avoid GPIO conflicts:
- Default Blue LED: GPIO25 (safe on all boards)
- Default Green LED: None (disabled to avoid conflicts)
- Default Red LED: None (disabled to avoid conflicts)

### 3. Command-Line Interface

Added flexible configuration options:

**Board variant presets:**
```bash
python3 weather_bot.py --enable-leds --led-board-variant dollatek
python3 weather_bot.py --enable-leds --led-board-variant heltec-v2
```

**Custom GPIO pins:**
```bash
python3 weather_bot.py --enable-leds \
  --led-blue-pin 25 \
  --led-green-pin 4 \
  --led-red-pin 5
```

### 4. Graceful Handling of Disabled LEDs

Updated LEDController to handle None pins properly:
- `_flash_pin()`: Returns early if pin is None
- `start_heartbeat()`: Checks if blue_pin is available
- `rx_flash()` / `tx_flash()`: Silently skip if pins are None

### 5. Comprehensive Documentation

- Created [DOLLATEK_SETUP.md](DOLLATEK_SETUP.md) with complete setup guide
- Updated README.md with correct GPIO information
- Added warnings about GPIO conflicts
- Included troubleshooting section

### 6. Test Coverage

Added comprehensive test suite (`tests/test_led_board_variants.py`):
- ✅ Default configuration test
- ✅ DollaTek variant test
- ✅ Heltec V2 variant test
- ✅ Custom pins test
- ✅ Pin override test
- ✅ Invalid variant test
- ✅ None pin handling test
- ✅ Board variants definition test

All tests pass (8/8).

## Usage Examples

### For DollaTek Board Users

**Basic usage:**
```bash
python3 weather_bot.py --enable-leds --led-board-variant dollatek
```

**With debug output:**
```bash
python3 weather_bot.py --enable-leds --led-board-variant dollatek --debug
```

**As a service (Raspberry Pi):**
```ini
# Edit /etc/systemd/system/weather_bot.service
ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py \
  --baud 115200 \
  --announce \
  --enable-leds \
  --led-board-variant dollatek
```

### LED Behavior on DollaTek

| LED Color | GPIO | Behavior | Status |
|-----------|------|----------|--------|
| Blue | GPIO25 | Heartbeat (blinks every 2s) | ✅ Working |
| Green | N/A | RX indicator | ⚠️ Logged only (no LED) |
| Red | N/A | TX indicator | ⚠️ Logged only (no LED) |

The blue LED provides visual confirmation that the bot is running. RX/TX events are logged in debug mode but don't flash LEDs since those GPIO pins are used by LoRa hardware.

## Benefits

1. **Fixes the original issue**: LED indicator now works on DollaTek board
2. **Prevents hardware conflicts**: Avoids using GPIO pins needed by LoRa
3. **Flexible configuration**: Supports different boards and custom setups
4. **Backward compatible**: Existing installations continue to work
5. **Well documented**: Clear guides for users
6. **Well tested**: Comprehensive test coverage

## Technical Details

### GPIO Pin Conflicts Explained

ESP32 LoRa boards use SPI to communicate with the SX1276 LoRa chip:

```
ESP32 GPIO Pins → SX1276 LoRa Chip
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GPIO5  → SCK   (SPI clock)
GPIO19 → MISO  (SPI data in)
GPIO27 → MOSI  (SPI data out)
GPIO18 → CS    (chip select)
GPIO14 → RESET (reset pin)
GPIO26 → DIO0  (interrupt for RX/TX)
```

Using GPIO26 or GPIO27 for LEDs would:
- Interfere with SPI communication
- Prevent LoRa packet reception (DIO0 interrupt)
- Cause data corruption on transmission (MOSI)
- Make the radio completely non-functional

### Why Only One LED?

Most ESP32 LoRa development boards prioritize:
1. **Small form factor** (30-40mm width)
2. **Low power consumption**
3. **Antenna/RF design**

This leaves limited space and GPIO pins for LEDs. The DollaTek board, like many ESP32 LoRa boards, includes only one user-accessible LED on GPIO25.

## Migration Guide

### Old Usage (Would Not Work)
```bash
# This would try to use GPIO26/27, causing LoRa failures
python3 weather_bot.py --enable-leds
```

### New Usage (Works Correctly)
```bash
# Use board variant for DollaTek
python3 weather_bot.py --enable-leds --led-board-variant dollatek
```

**No action required for users who:**
- Don't use `--enable-leds` flag (default)
- Already have working LED setup
- Don't have a DollaTek board

## Future Enhancements

Possible improvements for future versions:

1. **Auto-detect board type** from USB device identifiers
2. **Support for external LEDs** via GPIO expanders
3. **WS2812 RGB LED support** for single-pin multi-color indicators
4. **OLED display indicators** as alternative to LEDs
5. **Web dashboard integration** for remote LED status monitoring

## Related Documentation

- [DOLLATEK_SETUP.md](DOLLATEK_SETUP.md) - Complete DollaTek setup guide
- [README.md](README.md) - Main project documentation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General troubleshooting

## Conclusion

This fix resolves the LED indicator issue for DollaTek ESP32 SX1276 Wireless Bridge boards by correctly identifying and avoiding GPIO pin conflicts with LoRa hardware. The solution is flexible, well-documented, and thoroughly tested.

**Key takeaway**: Always verify GPIO pin assignments against your specific hardware before configuring peripherals like LEDs, especially on boards with integrated radios or other specialized hardware.
