// Bring-up test for a parallel HD44780-compatible LCD1602, wired 4-bit mode:
// RS=12, R/W=11, E=6, DB4=5, DB5=4, DB6=3, DB7=2. V0 through a 10k pot.
#include <LiquidCrystal.h>

const int LCD_RS = 12, LCD_RW = 11, LCD_E = 6, LCD_D4 = 5, LCD_D5 = 4, LCD_D6 = 3, LCD_D7 = 2;

LiquidCrystal lcd(LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7);

void setup() {
  pinMode(LCD_RW, OUTPUT);
  digitalWrite(LCD_RW, LOW);  // library assumes R/W is tied to GND; hold it low ourselves
  lcd.begin(16, 2);
  lcd.print("LCD OK, hello!");
  lcd.setCursor(0, 1);
  lcd.print("count: ");
}

void loop() {
  static unsigned long last = 0;
  static int n = 0;
  if (millis() - last > 1000) {
    last = millis();
    lcd.setCursor(7, 1);
    lcd.print("   ");
    lcd.setCursor(7, 1);
    lcd.print(n % 1000);
    n++;
  }
}
