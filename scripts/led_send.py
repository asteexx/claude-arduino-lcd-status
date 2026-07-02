#!/usr/bin/env python3
"""Sends one status command (R/Y/G/O) to the Arduino via led_daemon.py,
starting the daemon on first use. Meant to be called from Claude Code hooks.
"""
import os
import socket
import subprocess
import sys
import time

SOCK_PATH = "/tmp/claude-arduino-led.sock"
LOG_PATH = "/tmp/claude-arduino-led.log"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAEMON_PATH = os.path.join(SCRIPT_DIR, "led_daemon.py")


def send(cmd):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(1.0)
    s.connect(SOCK_PATH)
    s.sendall(cmd.encode())
    s.close()


def ensure_daemon_and_send(cmd):
    with open(LOG_PATH, "a") as log:
        subprocess.Popen(
            [sys.executable, DAEMON_PATH],
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    for _ in range(40):  # up to ~10s for the board to reset and boot
        time.sleep(0.25)
        try:
            send(cmd)
            return
        except OSError:
            continue


def is_valid(cmd):
    if cmd in {"R", "Y", "G", "O"}:
        return True
    return cmd.startswith("P") and cmd[1:].isdigit() and 0 <= int(cmd[1:]) <= 100


def main():
    if len(sys.argv) != 2 or not is_valid(sys.argv[1].upper()):
        sys.exit("usage: led_send.py [R|Y|G|O|P<0-100>]")
    cmd = sys.argv[1].upper()
    try:
        send(cmd)
    except OSError:
        ensure_daemon_and_send(cmd)


if __name__ == "__main__":
    main()
