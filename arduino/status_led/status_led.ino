// Claude Code live activity display on an LCD1602 (4-bit mode).
// Line 1 = what Claude is doing right now (set by hooks over serial).
// Line 2 = "msg:N up MM:SS" — message count + a clock that ticks locally.
//
// Serial protocol (9600 baud), each command ends with '\n':
//   1<text>  -> write <text> (padded to 16 chars) to line 1 (top)
//   M<num>   -> set the message counter shown on line 2
//   U        -> reset the uptime clock to zero (call at session start)
// Legacy single letters R/Y/G/O and P<n> are accepted and ignored.
#include <LiquidCrystal.h>

// R/W is on pin 11, held LOW here (write-only). Other pins per the kit wiring.
const int LCD_RS = 12, LCD_RW = 11, LCD_E = 6, LCD_D4 = 5, LCD_D5 = 4, LCD_D6 = 3, LCD_D7 = 2;
LiquidCrystal lcd(LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7);

unsigned long uptimeBase = 0;
long msgCount = 0;

char cmdBuf[24];
int cmdLen = 0;

void writePadded(int row, const char *text) {
  char buf[17];
  int i = 0;
  for (; i < 16 && text[i]; i++) buf[i] = text[i];
  for (; i < 16; i++) buf[i] = ' ';
  buf[16] = '\0';
  lcd.setCursor(0, row);
  lcd.print(buf);
}

void refreshLine2() {
  unsigned long sec = (millis() - uptimeBase) / 1000UL;
  unsigned long mm = sec / 60UL;
  unsigned long ss = sec % 60UL;
  if (mm > 99) { mm = 99; ss = 59; }  // keep the field width sane
  char buf[17];
  snprintf(buf, sizeof(buf), "msg:%ld up %02lu:%02lu", msgCount, mm, ss);
  writePadded(1, buf);
}

void handleCommand() {
  cmdBuf[cmdLen] = '\0';
  if (cmdLen == 0) return;
  switch (cmdBuf[0]) {
    case '1': writePadded(0, cmdBuf + 1); break;
    case 'M': msgCount = atol(cmdBuf + 1); refreshLine2(); break;
    case 'U': uptimeBase = millis(); refreshLine2(); break;
    default: break;  // R/Y/G/O/P and anything else: ignore
  }
}

void setup() {
  pinMode(LCD_RW, OUTPUT);
  digitalWrite(LCD_RW, LOW);
  lcd.begin(16, 2);
  uptimeBase = millis();
  writePadded(0, "Claude Code");
  refreshLine2();
  Serial.begin(9600);
  Serial.println("READY");
}

unsigned long lastTick = 0;

void loop() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') {
      handleCommand();
      cmdLen = 0;
    } else if (cmdLen < (int)sizeof(cmdBuf) - 1) {
      cmdBuf[cmdLen++] = ch;
    }
  }
  if (millis() - lastTick >= 1000) {
    lastTick = millis();
    refreshLine2();
  }
}
