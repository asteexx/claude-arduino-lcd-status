#!/usr/bin/env python3
"""Claude Code statusLine command. Reads the status JSON on stdin, pushes the
5-hour rate-limit usage percentage to the LED matrix (skipping redundant
writes to avoid hammering the serial link), and prints a normal status line.
"""
import datetime
import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LED_SEND = os.path.join(SCRIPT_DIR, "led_send.py")
LAST_PATH = "/tmp/claude-arduino-led-last-pct"
DEBUG_LOG = "/tmp/claude-statusline-debug.log"


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    with open(DEBUG_LOG, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat()} invoked, stdin={raw[:500]!r}\n")

    try:
        data = json.loads(raw)
    except ValueError:
        data = {}

    pct = (
        data.get("rate_limits", {})
        .get("five_hour", {})
        .get("used_percentage")
    )

    if pct is not None:
        pct = round(pct)
        last = None
        if os.path.exists(LAST_PATH):
            with open(LAST_PATH) as f:
                last = f.read().strip()
        if str(pct) != last:
            subprocess.run(
                [sys.executable, LED_SEND, f"P{pct}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
            with open(LAST_PATH, "w") as f:
                f.write(str(pct))
        print(f"5h limit: {pct}%")
    else:
        print("5h limit: n/a")


if __name__ == "__main__":
    main()
