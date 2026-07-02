// Isolate wiring problems: blinks ONE pin, 1s on / 1s off, forever.
const int PIN = 9;

void setup() {
  pinMode(PIN, OUTPUT);
}

void loop() {
  digitalWrite(PIN, HIGH);
  delay(1000);
  digitalWrite(PIN, LOW);
  delay(1000);
}
