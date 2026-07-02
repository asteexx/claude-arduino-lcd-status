// Diagnostic: lights one pin at a time (8..13) for 2s so we can see which
// pin drives which LED, since the breadboard wiring isn't visible in photos.
const int PINS[] = {8, 9, 10, 11, 12, 13};
const int N = 6;

void setup() {
  for (int i = 0; i < N; i++) pinMode(PINS[i], OUTPUT);
  Serial.begin(9600);
}

void loop() {
  for (int i = 0; i < N; i++) {
    for (int j = 0; j < N; j++) digitalWrite(PINS[j], LOW);
    digitalWrite(PINS[i], HIGH);
    Serial.print("PIN ");
    Serial.println(PINS[i]);
    delay(2000);
  }
}
