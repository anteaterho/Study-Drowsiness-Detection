/*
 * step_8_solenoid.ino
 * step_8_intergration_3.py 와 짝을 이루는 솔레노이드 제어 펌웨어
 *
 * 시리얼: 9600 baud
 * 프로토콜:
 *   'T' → 탭 시작 (80ms ON / 120ms OFF 반복)
 *   'S' → 즉시 정지 (릴레이 OFF)
 *
 * 안전:
 *   - 탭 시작 후 최대 5초(MAX_TAP_DURATION_MS) 경과 시 자동 정지
 *   - Python(SOLENOID_MAX_DURATION=5.0)과 동일한 상한
 *
 * 배선:
 *   - 릴레이 IN → Arduino D9
 *   - 12V 솔레노이드는 릴레이·다이오드·별도 어댑터로 구동
 *   - 솔레노이드 전원선은 릴레이 COM-NO 단자에 연결 (NC 사용 금지)
 */

const int RELAY_PIN = 9;
const int RELAY_ON_LEVEL = HIGH;  // 현재 릴레이 증상 기준: HIGH일 때 ON
const int RELAY_OFF_LEVEL = LOW;  // 무신호/대기 상태에서 솔레노이드 OFF

const int TAP_ON_TIME  = 80;    // 솔레노이드 당김 시간 (ms)
const int TAP_OFF_TIME = 120;   // 스프링 복귀 대기 (ms)
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
