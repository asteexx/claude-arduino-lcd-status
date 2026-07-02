#!/usr/bin/env python3
"""Claude Code hook -> LCD1602 live activity display.

Called from hooks with the event name as argv[1]; the hook's JSON payload
arrives on stdin. Maps each event to line-1 text ("what's happening now") and
keeps a per-session message counter, pushing both to the Arduino via the
led_daemon Unix socket. Line-2's clock ticks on the Arduino itself.
"""
import json
import os
import socket
import subprocess
import sys
import time

SOCK_PATH = "/tmp/claude-arduino-led.sock"
STATE_PATH = "/tmp/claude-lcd-state.json"
LOG_PATH = "/tmp/claude-lcd-status.log"
DAEMON_LOG = "/tmp/claude-arduino-led.log"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAEMON_PATH = os.path.join(SCRIPT_DIR, "led_daemon.py")


def raw_send(msg):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(1.0)
    s.connect(SOCK_PATH)
    s.sendall(msg.encode())
    s.close()


def send(msg):
    """Send one command, starting the daemon on first use if needed."""
    try:
        raw_send(msg)
        return
    except OSError:
        pass
    with open(DAEMON_LOG, "a") as log:
        subprocess.Popen(
            [sys.executable, DAEMON_PATH],
            stdout=log, stderr=log,
            stdin=subprocess.DEVNULL, start_new_session=True,
        )
    for _ in range(40):  # up to ~10s for the board to reset and boot
        time.sleep(0.25)
        try:
            raw_send(msg)
            return
        except OSError:
            continue


def load_state():
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except Exception:
        return {"msgs": 0}


def save_state(st):
    with open(STATE_PATH, "w") as f:
        json.dump(st, f)


def base(p):
    return os.path.basename(str(p).rstrip("/")) if p else ""


def tool_label(data):
    """Short 'what's happening' label for a PreToolUse event (<=16 chars)."""
    name = data.get("tool_name", "") or ""
    ti = data.get("tool_input", {}) or {}
    if name == "AskUserQuestion":
        return "?? QUESTION"
    if name in ("Edit", "MultiEdit"):
        return ("> Edit " + base(ti.get("file_path", "")))[:16]
    if name == "Write":
        return ("> Write " + base(ti.get("file_path", "")))[:16]
    if name == "NotebookEdit":
        return ("> Edit " + base(ti.get("notebook_path", "")))[:16]
    if name == "Read":
        return ("> Read " + base(ti.get("file_path", "")))[:16]
    if name == "Bash":
        return "> Bash"
    if name == "Grep":
        return "> Grep"
    if name == "Glob":
        return "> Glob"
    if name in ("WebFetch", "WebSearch"):
        return "> Web"
    if name in ("Task", "Agent"):
        return "> Agent"
    if name.startswith("mcp__"):
        return ("> " + name.split("__")[-1])[:16]
    return ("> " + name)[:16] if name else "> working"


def main():
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    with open(LOG_PATH, "a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {event} tool={data.get('tool_name')}\n")

    st = load_state()

    if event == "SessionStart":
        st = {"msgs": 0}
        save_state(st)
        send("U")           # reset the clock
        send("M0")
        send("1session start")
        return

    if event == "UserPromptSubmit":
        st["msgs"] = int(st.get("msgs", 0)) + 1
        save_state(st)
        line1 = "thinking..."
    elif event == "PreToolUse":
        line1 = tool_label(data)
    elif event == "Notification":
        line1 = "!! NEEDS YOU"
    elif event == "Stop":
        line1 = "= your turn ="
    elif event == "SessionEnd":
        line1 = "session ended"
    else:
        line1 = None

    # Re-send the count every time so line 2 stays correct even if the board
    # reset (which zeroes its counter) since the last update.
    send(f"M{int(st.get('msgs', 0))}")
    if line1 is not None:
        send("1" + line1)


if __name__ == "__main__":
    main()
