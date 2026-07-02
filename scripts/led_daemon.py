#!/usr/bin/env python3
"""Keeps one serial connection to the Arduino open and forwards single-char
status commands received over a Unix socket. Opening/closing serial on every
hook call would reset an Uno-style board each time (slow); this daemon opens
it once and stays alive so hook calls are near-instant.
"""
import glob
import os
import socket
import sys
import time

import serial

SOCK_PATH = "/tmp/claude-arduino-led.sock"
BAUD = 9600
VALID_CMDS = {"R", "Y", "G", "O"}


def to_wire(cmd):
    """Translate a validated command string into the bytes the sketch expects.

    Text commands (line-1 text, message count) are passed through verbatim so
    their case and spacing survive; only legacy control letters are matched
    against the fixed set.
    """
    if cmd in VALID_CMDS:
        return cmd.encode()  # legacy R/Y/G/O, ignored by the LCD sketch
    if cmd.startswith("P") and cmd[1:].isdigit():
        pct = max(0, min(100, int(cmd[1:])))
        return f"P{pct}\n".encode()
    if cmd.startswith("1"):
        return (cmd + "\n").encode()  # line 1 text: "1<text>"
    if cmd.startswith("M") and cmd[1:].lstrip("-").isdigit():
        return (cmd + "\n").encode()  # message count: "M<num>"
    if cmd == "U":
        return b"U\n"  # reset uptime clock
    return None


def find_port():
    candidates = sorted(glob.glob("/dev/cu.usbmodem*"))
    if not candidates:
        raise SystemExit("no Arduino found on /dev/cu.usbmodem*")
    return candidates[0]


def open_serial(port):
    ser = serial.Serial(port, BAUD, timeout=1)
    time.sleep(2.0)  # board resets when the serial port opens; let it boot
    ser.reset_input_buffer()
    return ser


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else find_port()
    ser = open_serial(port)

    if os.path.exists(SOCK_PATH):
        os.remove(SOCK_PATH)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK_PATH)
    srv.listen(5)
    print(f"led daemon: connected to {port}, listening on {SOCK_PATH}", flush=True)

    try:
        while True:
            conn, _ = srv.accept()
            with conn:
                data = conn.recv(64)
                if not data:
                    continue
                # Do not upper-case: line-1 text must keep its original casing.
                cmd = data.decode(errors="ignore").strip()
                wire = to_wire(cmd)
                if wire is None:
                    continue
                try:
                    ser.write(wire)
                except serial.SerialException:
                    # USB re-enumerated or the board reset; reopen once and retry.
                    print("led daemon: serial write failed, reconnecting", flush=True)
                    try:
                        ser.close()
                    except serial.SerialException:
                        pass
                    try:
                        ser = open_serial(port)
                        ser.write(wire)
                    except (serial.SerialException, OSError) as exc:
                        print(f"led daemon: reconnect failed: {exc}", flush=True)
    finally:
        srv.close()
        if os.path.exists(SOCK_PATH):
            os.remove(SOCK_PATH)
        ser.close()


if __name__ == "__main__":
    main()
