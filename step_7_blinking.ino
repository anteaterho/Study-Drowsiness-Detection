// the setup function runs once when you press reset or power the board
void setup() {
  // initialize digital pin LED_BUILTIN as an output.
  pinMode(9, OUTPUT);
}

// the loop function runs over and over again forever
void loop() {
  digitalWrite(9, HIGH);  // change state of the LED by setting the pin to the HIGH voltage level
  delay(500);                      // wait for a second
  digitalWrite(9, LOW);   // change state of the LED by setting the pin to the LOW voltage level
  delay(3000);                      // wait for a second
}
