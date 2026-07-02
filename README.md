# Claude Code — Arduino LCD Status Display

A physical, live activity indicator for [Claude Code](https://claude.com/claude-code) sessions,
built on an **Arduino UNO R4 WiFi** with a parallel **HD44780-compatible LCD1602** (4-bit mode).

Claude Code hooks fire in real time and push the current activity to the LCD over serial:

```
+------------------+
| > Edit main.py   |   <- line 1: what Claude is doing right now
| msg:7 up 03:42   |   <- line 2: message count + a clock ticking on the Arduino
+------------------+
```

## How it works

```
Claude Code hook  ->  scripts/lcd_status.py  ->  Unix socket  ->  scripts/led_daemon.py  ->  serial  ->  Arduino LCD
```

- **`arduino/status_led/status_led.ino`** — the sketch. Renders line 1 (set by hooks) and
  line 2 (`msg:N up MM:SS`, where the clock advances locally in `loop()` from `millis()`,
  so it ticks between events, not only when a hook fires).
- **`scripts/led_daemon.py`** — holds one persistent serial connection open (re-opening the
  port resets the board and is slow) and forwards commands received on a Unix socket
  (`/tmp/claude-arduino-led.sock`).
- **`scripts/lcd_status.py`** — the hook script. Receives the event name as `argv[1]` and the
  hook JSON on stdin, maps each event to a line-1 label, tracks a per-session message counter,
  and talks to the daemon. Auto-starts the daemon on first use.

### Line-1 labels

| Event | Shows |
|-------|-------|
| `SessionStart` | `session start` |
| `UserPromptSubmit` | `thinking...` |
| `PreToolUse` | `> Bash`, `> Edit main.py`, `> Read x.py`, `> Grep`, `?? QUESTION`, … |
| `Notification` | `!! NEEDS YOU` |
| `Stop` | `= your turn =` |
| `SessionEnd` | `session ended` |

## Serial protocol (9600 baud, `\n`-terminated)

| Command | Effect |
|---------|--------|
| `1<text>` | write `<text>` (padded to 16 chars) to line 1 |
| `M<num>` | set the message counter on line 2 |
| `U` | reset the uptime clock to zero (sent at session start) |
| legacy `R`/`Y`/`G`/`O`/`P<n>` | accepted and ignored |

## Wiring (LCD1602, 4-bit mode)

| LCD pin | Arduino |
|---------|---------|
| RS | 12 |
| R/W | 11 (held LOW in code — write-only) |
| E | 6 |
| DB4–DB7 | 5, 4, 3, 2 |
| V0 (contrast) | 10 kΩ potentiometer |

> **Gotcha:** on a breadboard, the LCD and its jumper wires must be on the **same side** of the
> center channel (the `a-e` / `f-j` split). Same row number across the channel is electrically
> disconnected — a classic cause of "16 solid blocks, display unresponsive".

## Setup

1. Flash `arduino/status_led/status_led.ino` to the board (`arduino-cli` or the Arduino IDE).
2. Wire the hooks in Claude Code's `settings.json` to run `scripts/lcd_status.py <EventName>`
   for `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `Notification`, `Stop`, `SessionEnd`.
3. Requires Python 3 with [`pyserial`](https://pypi.org/project/pyserial/). The daemon
   auto-starts on the first hook call.

> **Note:** the daemon holds the serial port, so kill it before `arduino-cli upload` and restart
> it after (it will auto-restart on the next hook otherwise).

## Notes / limitations

- The `arduino/lcd_test/` and `arduino/lcd_pin_scan/` sketches are bring-up/diagnostic helpers.
- Live 5-hour usage-% display was abandoned: Claude Code's `statusLine` command is only invoked
  in an interactive terminal REPL, not in Claude Desktop's headless agent mode, so the percentage
  can't be obtained there. Ordinary event hooks fire fine in both.
