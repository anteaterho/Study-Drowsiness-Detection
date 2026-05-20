/*
 * step_6_solenoid.ino
 * step_6_intergration_2.py / step_8_intergration_3.py 와 동일 프로토콜
 * (상세 주석·구현은 step_8_solenoid.ino 와 동일)
 */

const int RELAY_PIN = 9;
const int RELAY_ON_LEVEL = HIGH;
const int RELAY_OFF_LEVEL = LOW;

const int TAP_ON_TIME  = 80;
const int TAP_OFF_TIME = 120;
const unsigned long MAX_TAP_DURATION_MS = 5000;

bool tapping = false;
bool solenoidOn = false;
unsigned long tapStartMillis = 0;
unsigned long phaseStartMillis = 0;

void relayOff() {
    digitalWrite(RELAY_PIN, RELAY_OFF_LEVEL);
    solenoidOn = false;
}

void relayOn() {
    digitalWrite(RELAY_PIN, RELAY_ON_LEVEL);
    solenoidOn = true;
}

void stopTapping() {
    tapping = false;
    relayOff();
}

void startTapping() {
    if (!tapping) {
        tapStartMillis = millis();
        phaseStartMillis = millis();
        relayOn();
    }
    tapping = true;
}

void processSerial() {
    while (Serial.available() > 0) {
        char cmd = Serial.read();
        if (cmd == 'T') {
            startTapping();
        } else if (cmd == 'S') {
            stopTapping();
        }
    }
}

void updateTapping() {
    if (!tapping) {
        return;
    }

    if (millis() - tapStartMillis >= MAX_TAP_DURATION_MS) {
        stopTapping();
        return;
    }

    unsigned long phaseElapsed = millis() - phaseStartMillis;

    if (solenoidOn) {
        if (phaseElapsed >= (unsigned long)TAP_ON_TIME) {
            relayOff();
            phaseStartMillis = millis();
        }
    } else {
        if (phaseElapsed >= (unsigned long)TAP_OFF_TIME) {
            relayOn();
            phaseStartMillis = millis();
        }
    }
}

void setup() {
    digitalWrite(RELAY_PIN, RELAY_OFF_LEVEL);
    pinMode(RELAY_PIN, OUTPUT);
    relayOff();
    Serial.begin(9600);
}

void loop() {
    processSerial();
    updateTapping();
}
