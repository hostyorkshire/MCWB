#!/usr/bin/env python3
"""
serial_diagnostic.py  -  Complete serial-port diagnostic tool
Target: Silicon Labs CP2102  VID=0x10C4  PID=0xEA60
Chip  : ESP32-D0WDQ6 (revision 1)  MAC 2c:bc:bb:9f:df:44  40 MHz crystal

Usage:
    python serial_diagnostic.py                  # auto-detect CP2102 port
    python serial_diagnostic.py /dev/ttyUSB1     # explicit port
    python serial_diagnostic.py --baud 9600      # override baud (default 115200)
    python serial_diagnostic.py --skip-baud-probe

Why RTS/DTR matter on the Heltec V2:
    RTS -> ESP32 EN (chip reset).  If asserted, chip is held in reset.
    DTR -> IO0  (boot-mode select). If asserted, chip tries to enter bootloader.
    pyserial can inherit these states from Arduino IDE or esptool.
    This tool always deasserts both lines before sending any command.

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""

import sys
import time
import argparse
from datetime import datetime

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("ERROR: pyserial not installed.")
    print("       Run:  pip install pyserial")
    sys.exit(1)

# --------------------------------------------------------------------------- #
#  Hardware fingerprint
# --------------------------------------------------------------------------- #
TARGET_VID = 0x10C4   # Silicon Labs
TARGET_PID = 0xEA60   # CP2102 / CP210x

# --------------------------------------------------------------------------- #
#  MeshCore companion radio protocol constants
# --------------------------------------------------------------------------- #
FRAME_TO_NODE    = 0x3C   # '<'
FRAME_FROM_NODE  = 0x3E   # '>'
FIRMWARE_VER     = 9
CMD_DEVICE_QUERY = 22
CMD_APP_START    = 1
RESP_DEVICE_INFO = 13
RESP_SELF_INFO   = 5

BAUDS_TO_TRY = [115200, 9600, 57600, 38400, 19200]


# --------------------------------------------------------------------------- #
#  Logging helpers
# --------------------------------------------------------------------------- #
def _ts():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def ok(msg):   print(f"  [{_ts()}]  OK   {msg}")
def warn(msg): print(f"  [{_ts()}]  WARN {msg}")
def err(msg):  print(f"  [{_ts()}]  FAIL {msg}")
def info(msg): print(f"  [{_ts()}]       {msg}")


# --------------------------------------------------------------------------- #
#  Protocol helpers
# --------------------------------------------------------------------------- #
def encode_frame(payload: bytes) -> bytes:
    n = len(payload)
    return bytes([FRAME_TO_NODE, n & 0xFF, (n >> 8) & 0xFF]) + payload


def read_until_frame(ser, timeout=4.0, target_code=None):
    buf = bytearray()
    deadline = time.time() + timeout
    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buf += chunk
        while True:
            if FRAME_FROM_NODE not in buf:
                break
            idx = buf.index(FRAME_FROM_NODE)
            if len(buf) < idx + 3:
                break
            length = buf[idx + 1] | (buf[idx + 2] << 8)
            if length == 0 or length > 300:
                buf = buf[idx + 1:]
                continue
            if len(buf) < idx + 3 + length:
                break
            payload = bytes(buf[idx + 3: idx + 3 + length])
            buf = buf[idx + 3 + length:]
            if target_code is None or (payload and payload[0] == target_code):
                return payload, bytes(buf)
    return None, bytes(buf)

def open_port_safe(port, baud):
    ser = serial.Serial(
        port, baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.05,
        write_timeout=2,
        rtscts=False,
        dsrdtr=False,
    )
    rts_was = ser.rts
    dtr_was = ser.dtr
    ser.rts = False
    ser.dtr = False
    if rts_was or dtr_was:
        warn(f"RTS={{rts_was}} DTR={{dtr_was}} were asserted - deasserted now. "
             "Waiting 2s for ESP32 to boot...")
        time.sleep(2.0)
    ser.reset_input_buffer()
    return ser, rts_was, dtr_was

# --------------------------------------------------------------------------- #
#  Test sections
# --------------------------------------------------------------------------- #
def section(title):
    print()
    print("=" * 68)
    print(f"  {{title}}")
    print("=" * 68)


def test_1_port_enumeration(explicit_port):
    section("TEST 1 - Port enumeration")
    all_ports = list(serial.tools.list_ports.comports())
    if all_ports:
        info("All detected serial ports:")
        for p in all_ports:
            vid = f"0x{{p.vid:04X}}" if p.vid else "  -   "
            pid = f"0x{{p.pid:04X}}" if p.pid else "  -   "
            marker = " <<< CP2102" if (p.vid == TARGET_VID and p.pid == TARGET_PID) else ""
            info(f"  {{p.device:<18}} VID={{vid}} PID={{pid}}  {{p.description}}{{marker}}")
    else:
        warn("No serial ports found at all.")

    cp_ports = [p for p in all_ports if p.vid == TARGET_VID and p.pid == TARGET_PID]
    if cp_ports:
        ok(f"Found {{len(cp_ports)}} CP2102 port(s)")
    else:
        warn("No CP2102 (VID=0x10C4 PID=0xEA60) detected.")
        if not explicit_port:
            err("Cannot continue. Connect device or pass port explicitly.")
            sys.exit(1)
    return cp_ports


def test_2_select_port(explicit_port, cp_ports):
    section("TEST 2 - Port selection")
    if explicit_port:
        port = explicit_port
        info(f"Using explicitly specified port: {{port}}")
    else:
        port = cp_ports[0].device
        ok(f"Auto-selected first CP2102 port: {{port}}")
    return port


def test_3_open_port(port, baud):
    section(f"TEST 3 - Open port  {{port}} @ {{baud}} baud  (RTS/DTR safe)")
    info(f"Opening {{port}} ...")
    try:
        ser, rts_was, dtr_was = open_port_safe(port, baud)
    except serial.SerialException as e:
        err(f"Cannot open {{port}}: {{e}}")
        err("Possible causes:")
        err("  - Port in use by another process (Arduino IDE, esptool, etc.)")
        err("  - Permission denied  (Linux: sudo usermod -aG dialout $USER)")
        err("  - Wrong port path")
        sys.exit(1)
    ok(f"Port open  {{port}} @ {{baud}} baud")
    ok(f"RTS={{ser.rts}} DTR={{ser.dtr}}  rtscts=False  dsrdtr=False")
    return ser


def test_4_line_states(ser):
    section("TEST 4 - RTS / DTR line verification")
    if ser.rts:
        err("RTS is ASSERTED - ESP32 EN is being held LOW (continuous reset!)")
        err("Fix: ser.rts = False")
    else:
        ok("RTS deasserted - ESP32 EN pin is free to run")
    if ser.dtr:
        warn("DTR is ASSERTED - ESP32 IO0 held LOW (boot-loader mode)")
        warn("Normal running requires DTR deasserted")
    else:
        ok("DTR deasserted - ESP32 IO0 in normal-run state")


def test_5_baud_probe(port, requested_baud):
    section("TEST 5 - Baud-rate probe")
    probe_order = [requested_baud] + [b for b in BAUDS_TO_TRY if b != requested_baud]
    info(f"Probing baud rates in order: {{probe_order}}")
    for b in probe_order:
        try:
            ser2, _, _ = open_port_safe(port, b)
            frame = encode_frame(bytes([CMD_DEVICE_QUERY, FIRMWARE_VER]))
            ser2.write(frame)
            ser2.flush()
            payload, _ = read_until_frame(ser2, timeout=1.0)
            ser2.close()
            if payload:
                if b == requested_baud:
                    ok(f"{{b}} baud - response received (baud confirmed)")
                else:
                    warn(f"{{b}} baud - response received  "
                         f"(mismatch with --baud {{requested_baud}}; use --baud {{b}})")
                return b
            info(f"  {{b:7d}} baud - no response")
        except serial.SerialException:
            info(f"  {{b:7d}} baud - port error (skipped)")

    warn("No baud rate produced a response.")
    warn("Check: MeshCore companion radio firmware is flashed "
         "(not AT-command / factory firmware).")
    return requested_baud


def test_6_write(ser):
    section("TEST 6 - Write test  (CMD_DEVICE_QUERY frame)")
    frame = encode_frame(bytes([CMD_DEVICE_QUERY, FIRMWARE_VER]))
    info(f"Frame bytes: {{frame.hex(' ').upper()}}")
    try:
        n = ser.write(frame)
        ser.flush()
        ok(f"Wrote {{n}} byte(s) without error")
    except serial.SerialException as e:
        err(f"Write failed: {{e}}")
        sys.exit(1)


def test_7_read_device_info(ser):
    section("TEST 7 - Read test  (RESP_DEVICE_INFO expected)")
    info("Waiting up to 4 s for RESP_DEVICE_INFO (code 13) ...")
    payload, raw = read_until_frame(ser, timeout=4.0, target_code=RESP_DEVICE_INFO)

    if payload is None:
        err("No response received within 4 s.")
        if raw:
            hex_preview = raw[:64].hex(' ').upper()
            warn(f"Raw bytes seen ({{len(raw)}} bytes): {{hex_preview}}")
            warn("If bytes look like ASCII the firmware sends AT-style responses -")
            warn("you need the MeshCore companion radio build.")
        else:
            warn("No bytes at all - check USB cable and that device is powered.")
        return False, {}

    ok(f"Frame received ({{len(payload)}} payload bytes)")
    info(f"Payload hex: {{payload[:24].hex(' ').upper()}} ...")

    if payload[0] != RESP_DEVICE_INFO:
        warn(f"Response code 0x{{payload[0]:02X}} - expected 0x{{RESP_DEVICE_INFO:02X}} "
             "(RESP_DEVICE_INFO).  Node alive but unexpected response code.")
        return True, {}

    result = {}
    if len(payload) > 1:
        result["fw_ver_code"]  = payload[1]
    if len(payload) > 2:
        result["max_contacts"] = payload[2] * 2
    if len(payload) >= 80:
        result["build_date"]   = payload[7:19].decode("utf-8", errors="replace").rstrip("\x00")
        result["manufacturer"] = payload[19:59].decode("utf-8", errors="replace").rstrip("\x00")
        result["fw_version"]   = payload[59:79].decode("utf-8", errors="replace").rstrip("\x00")

    ok("Parsed DEVICE_INFO:")
    for k, v in result.items():
        info(f"    {{k:<20s}} = {{v}}")

    fw = result.get("fw_ver_code", 0)
    if fw != FIRMWARE_VER:
        warn(f"fw_ver_code={{fw}}, expected {{FIRMWARE_VER}} (MeshCore v1.13.0 protocol)")
        warn("This may cause issues with message send/receive.")
    else:
        ok(f"fw_ver_code={{fw}} matches expected {{FIRMWARE_VER}}")

    return True, result


def test_8_app_start(ser):
    section("TEST 8 - APP_START handshake  (RESP_SELF_INFO expected)")
    app_payload = bytes([CMD_APP_START]) + bytes(7) + b"MCWB_diag"
    frame = encode_frame(app_payload)
    info(f"Sending CMD_APP_START: {{frame.hex(' ').upper()}}")
    try:
        ser.write(frame)
        ser.flush()
    except serial.SerialException as e:
        err(f"Write failed: {{e}}")
        return False, {}

    payload, _ = read_until_frame(ser, timeout=3.0, target_code=RESP_SELF_INFO)
    if payload is None:
        err("No SELF_INFO response - APP_START handshake failed.")
        err("Possible causes:")
        err("  - fw_ver_code mismatch (see Test 7)")
        err("  - Node is still booting - retry after a few seconds")
        return False, {}

    ok(f"SELF_INFO received ({{len(payload)}} bytes)")
    result = {}
    if len(payload) >= 57:
        result["node_name"] = payload[56:].decode("utf-8", errors="replace").rstrip("\x00")
    ok(f"node_name = {{result.get('node_name', '(could not parse)')}}")
    return True, result


def test_9_summary(port, baud, dev_info_ok, app_start_ok, device_info, self_info):
    section("TEST 9 - Summary")
    print()
    print(f"  {{'Port':<20}}: {{port}}")
    print(f"  {{'Baud':<20}}: {{baud}}")
    print(f"  {{'DEVICE_INFO':<20}}: {{'PASS' if dev_info_ok else 'FAIL'}}")
    print(f"  {{'APP_START':<20}}: {{'PASS' if app_start_ok else 'FAIL'}}")
    if device_info:
        for k, v in device_info.items():
            print(f"  {{k:<20}}: {{v}}")
    if self_info:
        print(f"  {{'node_name':<20}}: {{self_info.get('node_name', '?')}}")
    print()
    if dev_info_ok and app_start_ok:
        ok("ALL CHECKS PASSED - hardware is ready for weather_bot.py")
    else:
        err("One or more checks FAILED.")
        err("Fix the issues reported above before starting weather_bot.py.")
    print()
    return dev_info_ok and app_start_ok

# --------------------------------------------------------------------------- #
#  Main
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(
        description="ESP32-D0WDQ6 / CP2102 serial diagnostic tool for MeshCore",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python serial_diagnostic.py
  python serial_diagnostic.py /dev/ttyUSB1
  python serial_diagnostic.py COM4 --baud 9600
  python serial_diagnostic.py --skip-baud-probe
        """,
    )
    parser.add_argument("port", nargs="?", default=None,
                        help="Serial port path (auto-detect CP2102 if omitted)")
    parser.add_argument("--baud", type=int, default=115200,
                        help="Initial baud rate to try (default: 115200)")
    parser.add_argument("--skip-baud-probe", action="store_true",
                        help="Skip baud-rate probe and use --baud value directly")
    args = parser.parse_args()

    print()
    print("+" + "-" * 66 + "+")
    print("|  MeshCore / ESP32-CP2102 Serial Diagnostic Tool                  |")
    print("|  Target : VID=0x10C4  PID=0xEA60  (Silicon Labs CP2102)          |")
    print("|  Chip   : ESP32-D0WDQ6 rev1   MAC 2c:bc:bb:9f:df:44             |")
    print("|  Crystal: 40 MHz                                                  |")
    print("+" + "-" * 66 + "+")

    cp_ports = test_1_port_enumeration(args.port)
    port     = test_2_select_port(args.port, cp_ports)
    ser      = test_3_open_port(port, args.baud)
    test_4_line_states(ser)

    if not args.skip_baud_probe:
        ser.close()
        detected_baud = test_5_baud_probe(port, args.baud)
        ser = test_3_open_port(port, detected_baud)
    else:
        detected_baud = args.baud
        info("Baud-rate probe skipped (--skip-baud-probe)")

    test_6_write(ser)
    dev_info_ok, device_info = test_7_read_device_info(ser)
    app_start_ok, self_info  = test_8_app_start(ser)
    ser.close()

    passed = test_9_summary(
        port, detected_baud,
        dev_info_ok=dev_info_ok,
        app_start_ok=app_start_ok,
        device_info=device_info,
        self_info=self_info,
    )
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()