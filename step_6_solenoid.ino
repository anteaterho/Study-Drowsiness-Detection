// 릴레이 제어 핀 (로우레벨 트리거: LOW = 릴레이 ON, HIGH = 릴레이 OFF)
const int RELAY_PIN = 9;

// 탭 타이밍 설정 (ms)
const int TAP_ON_TIME  = 80;   // 솔레노이드 당기는 시간
const int TAP_OFF_TIME = 120;  // 복귀 시간

bool tapping = false;

void setup() {
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, HIGH);  // 시작 시 릴레이 OFF (로우레벨이므로 HIGH = OFF)
    Serial.begin(9600);
}

void loop() {
    if (Serial.available() > 0) {
        char cmd = Serial.read();
        if (cmd == 'T') tapping = true;
        else if (cmd == 'S') {
            tapping = false;
            digitalWrite(RELAY_PIN, HIGH);  // 즉시 릴레이 OFF
        }
    }

    if (tapping) {
        digitalWrite(RELAY_PIN, LOW);   // 릴레이 ON → 솔레노이드 당김
        delay(TAP_ON_TIME);
        digitalWrite(RELAY_PIN, HIGH);  // 릴레이 OFF → 솔레노이드 복귀
        delay(TAP_OFF_TIME);
    }
}
