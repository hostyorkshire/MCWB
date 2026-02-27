# DollaTek ESP32 SX1276 Wireless Bridge Setup Guide

This guide provides specific setup instructions for the **DollaTek ESP32 SX1276 Wireless Bridge** board when using it with MCWB (MeshCore Weather Bot).

## Overview

The DollaTek ESP32 SX1276 Wireless Bridge is a compact LoRa development board that combines:
- ESP32-D0WDQ6 microcontroller (dual-core 32-bit)
- SX1276 LoRa chipset (470-928MHz)
- 8MB SDRAM and 8MB FLASH
- WiFi and Bluetooth support
- USB serial interface

This board is often sold as a "Lora Bridge" and is compatible with Heltec v2 firmware (1.13.0).

## Hardware Specifications

| Component | Details |
|-----------|---------|
| Microcontroller | ESP32-D0WDQ6 |
| LoRa Chipset | SX1276 |
| Frequency | 470-510MHz, max 863-928MHz |
| Memory | 8MB Flash, 8MB PSRAM |
| Connectivity | WiFi 802.11 b/g/n, Bluetooth V4.2 |
| Power | 5V DC Micro USB |
| Dimensions | 66(+10) x 30 x 15 mm |

## LED Indicators

⚠️ **IMPORTANT GPIO PIN NOTE**

The DollaTek board has **only one onboard LED** on GPIO25. Unlike some documentation that suggests three LEDs on GPIO25/26/27, this board has the following GPIO pin usage:

| GPIO Pin | Usage | Notes |
|----------|-------|-------|
| GPIO25 | Onboard LED (Blue) | ✅ Available for LED indicator |
| GPIO26 | LoRa DIO0 | ❌ Used by LoRa, NOT available for LED |
| GPIO27 | LoRa MOSI | ❌ Used by LoRa, NOT available for LED |

**This is why the LED activity indicators didn't work when using default Heltec v2 settings!**

## Quick Start with MCWB

### 1. Flash MeshCore Firmware

Flash your DollaTek board with MeshCore firmware (Heltec v2 firmware 1.13.0 or compatible).

### 2. Connect the Board

Connect the DollaTek board to your Raspberry Pi or PC via USB. The device typically appears as:
- Linux: `/dev/ttyUSB0` or `/dev/ttyACM0`
- macOS: `/dev/cu.usbserial-*`
- Windows: `COM3`, `COM4`, etc.

### 3. Configure Channels in MeshCore App

**Before starting the bot**, use the MeshCore app on your phone to:
1. Connect to your DollaTek board
2. Join/subscribe to the channels you want the bot to monitor (e.g., `#weather`, `#wxtest`)
3. The bot cannot add channels automatically - this must be done through the app

### 4. Run MCWB with DollaTek Board Support

```bash
# Basic usage (auto-detects serial port)
python3 weather_bot.py

# With LED indicator enabled (recommended for DollaTek)
python3 weather_bot.py --enable-leds --led-board-variant dollatek

# Specify serial port explicitly
python3 weather_bot.py --port /dev/ttyUSB0 --enable-leds --led-board-variant dollatek

# With debug output to see LED events
python3 weather_bot.py --enable-leds --led-board-variant dollatek --debug
```

## LED Behavior with DollaTek Board

When you enable LEDs with the DollaTek variant (`--enable-leds --led-board-variant dollatek`):

| LED Color | GPIO | Behavior |
|-----------|------|----------|
| Blue | GPIO25 | Heartbeat - blinks every 2 seconds while bot is running |
| Green | N/A | Not available (GPIO26 used by LoRa) |
| Red | N/A | Not available (GPIO27 used by LoRa) |

**Note**: RX and TX indicators are logged in debug mode but not shown on LEDs since those GPIO pins are not available.

## Troubleshooting

### LED Doesn't Work

If the LED indicator doesn't work:

1. **Verify you're using the correct board variant**:
   ```bash
   python3 weather_bot.py --enable-leds --led-board-variant dollatek --debug
   ```

2. **Check that GPIO25 is available** on your board (it should be by default)

3. **Verify MeshCore firmware supports GPIO commands** (most versions do, but if not, LED events will only be logged)

4. **Look for LED log messages** with `--debug` flag:
   ```
   LED BLUE GPIO25 ON  (0.1s)
   LED BLUE GPIO25 OFF
   ```

### No Serial Port Found

If the bot can't find the serial port:

1. **Check USB connection**: Ensure the board is powered and connected
2. **Check device permissions**: 
   ```bash
   # On Linux, add your user to the dialout group
   sudo usermod -a -G dialout $USER
   # Log out and back in for changes to take effect
   ```
3. **List available ports**:
   ```bash
   ls /dev/ttyUSB* /dev/ttyACM*
   ```
4. **Specify port explicitly**:
   ```bash
   python3 weather_bot.py --port /dev/ttyUSB0
   ```

### Bot Receives No Messages

If the bot connects but doesn't receive messages:

1. **Most common cause**: The board is not subscribed to the channels where users are sending messages
2. **Solution**: Use the MeshCore app to join/subscribe to channels (e.g., `#weather`) BEFORE starting the bot
3. **Verify**: Use `--debug` mode to see incoming messages:
   ```bash
   python3 weather_bot.py --debug
   ```

## Running as a Service (Raspberry Pi)

To run MCWB automatically on boot with DollaTek board:

1. **Install the service**:
   ```bash
   cd ~/MCWB
   ./install_service.sh
   ```

2. **Edit the service file** to add DollaTek LED support:
   ```bash
   sudo nano /etc/systemd/system/weather_bot.service
   ```

3. **Update the ExecStart line**:
   ```ini
   ExecStart=/usr/bin/python3 /home/pi/MCWB/weather_bot.py --baud 115200 --announce --enable-leds --led-board-variant dollatek
   ```

4. **Reload and restart the service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart weather_bot
   sudo systemctl status weather_bot
   ```

## Custom GPIO Configuration (Advanced)

If you've modified your DollaTek board or want to use external LEDs on different GPIO pins:

```bash
# Example: Blue LED on GPIO2, Green on GPIO4, Red on GPIO5
python3 weather_bot.py --enable-leds \
  --led-blue-pin 2 \
  --led-green-pin 4 \
  --led-red-pin 5
```

**⚠️ Warning**: Avoid using these GPIO pins as they conflict with hardware functions:
- **GPIO6-11**: Reserved for SPI flash
- **GPIO26**: Used for LoRa DIO0
- **GPIO34-39**: Input-only pins (cannot drive LEDs)

Always verify your board's pinout before configuring custom GPIO pins.

## Additional Resources

- [MCWB Main README](README.md) - General usage and features
- [Raspberry Pi Setup Guide](RASPBERRY_PI_SETUP.md) - Auto-start on boot
- [Web Dashboard Guide](WEB_DASHBOARD.md) - Monitor your bot with web interface
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- [Heltec Wireless Bridge Documentation](https://docs.heltec.org/en/node/esp32/wireless_bridge/index.html) - Hardware reference

## Technical Details

### Why GPIO26/27 Can't Be Used for LEDs

The DollaTek board (like most ESP32 LoRa boards) uses specific GPIO pins for the SX1276 LoRa module:

- **GPIO18**: LoRa SPI CS (Chip Select)
- **GPIO14**: LoRa RESET
- **GPIO26**: LoRa DIO0 (interrupt pin for packet reception)
- **GPIO27**: LoRa MOSI (SPI data line)
- **GPIO19**: LoRa MISO (SPI data line)
- **GPIO5**: LoRa SCK (SPI clock)

Attempting to use GPIO26 or GPIO27 for LED control would interfere with LoRa communication, causing packet loss or complete communication failure.

### Firmware Compatibility

This setup has been tested with:
- ✅ Heltec v2 firmware 1.13.0
- ✅ MeshCore firmware (various versions)
- ✅ Compatible ESP32 LoRa firmware variants

The `--led-board-variant dollatek` option tells MCWB to use only GPIO25 for the LED indicator, avoiding conflicts with the LoRa radio.

## Support

If you encounter issues:

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Run with `--debug` flag to see detailed log output
3. Check that your board is properly flashed with MeshCore firmware
4. Verify channel subscriptions in the MeshCore app
5. Open an issue on GitHub with debug logs if problems persist
