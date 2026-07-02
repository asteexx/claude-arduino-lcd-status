// Diagnostic: toggles one LCD signal pin at a time (all others held LOW) so you
// can watch the screen and see which pin, if any, visibly affects it — same
// idea as pin_scan.ino for the LEDs. No LiquidCrystal library used here.
// Set contrast (V0 pot) to wherever you saw the darkest blocks before running this.

struct Wire { int pin; const char *name; };
Wire WIRES[] = {
  {12, "RS"},
  {11, "R/W"},
  {6,  "E"},
  {5,  "DB4"},
  {4,  "DB5"},
  {3,  "DB6"},
  {2,  "DB7"},
};
const int N = 7;

void allLow() {
  for (int i = 0; i < N; i++) digitalWrite(WIRES[i].pin, LOW);
}

void setup() {
  for (int i = 0; i < N; i++) pinMode(WIRES[i].pin, OUTPUT);
  allLow();
  Serial.begin(9600);
}

void loop() {
  for (int i = 0; i < N; i++) {
    Serial.print("Toggling pin ");
    Serial.print(WIRES[i].pin);
    Serial.print(" (");
    Serial.print(WIRES[i].name);
    Serial.println(") for 12s - watch the screen");
    for (int cycle = 0; cycle < 3; cycle++) {
      digitalWrite(WIRES[i].pin, HIGH);
      delay(2000);
      digitalWrite(WIRES[i].pin, LOW);
      delay(2000);
    }
  }
}
