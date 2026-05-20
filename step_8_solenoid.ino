/*
 * step_8_solenoid.ino
 * 이 파일은 Python 코드(step_8_intergration_3.py)에서 보내는 시리얼 명령을 받아
 * 릴레이를 통해 12V 솔레노이드를 짧게 ON/OFF 반복 제어하는 Arduino 코드이다.
 *
 * Python ↔ Arduino 시리얼 통신 설정:
 *   - 통신 속도: 9600 baud
 *   - Python이 'T'를 보내면 솔레노이드 탭 동작 시작
 *   - Python이 'S'를 보내면 솔레노이드 탭 동작 즉시 정지
 *
 * 안전 설계:
 *   - 솔레노이드는 오래 켜 두면 열이 나므로 짧은 펄스로만 동작시킨다.
 *   - 한 번 탭 동작이 시작되면 최대 5초까지만 반복하고 자동으로 꺼진다.
 *   - Python이 멈추거나 'S' 명령을 못 보내도 Arduino가 5초 후 자체 정지한다.
 *
 * 배선 주의:
 *   - 릴레이 제어선(IN)은 Arduino D9 핀에 연결한다.
 *   - 솔레노이드 전원은 Arduino 5V에서 직접 공급하지 않는다.
 *   - 12V 어댑터, 릴레이, 보호 다이오드를 사용해 별도 전원으로 구동한다.
 *   - 솔레노이드 전원선은 릴레이 COM-NO 단자에 연결한다.
 *   - NC 단자에 연결하면 대기 상태에서도 전기가 들어갈 수 있으므로 사용하지 않는다.
 */

const int RELAY_PIN = 9;  // 릴레이 모듈 IN 핀과 연결된 Arduino 디지털 핀 번호이다.

const int RELAY_ON_LEVEL = HIGH;  // 현재 릴레이 모듈 기준으로 D9가 HIGH일 때 릴레이를 켠다.
const int RELAY_OFF_LEVEL = LOW;  // 현재 릴레이 모듈 기준으로 D9가 LOW일 때 릴레이를 끈다.

const int TAP_ON_TIME = 80;  // 솔레노이드에 전기를 인가하는 시간이다. 단위는 ms이고, 80ms만 켠다.
const int TAP_OFF_TIME = 120;  // 솔레노이드 전기를 끄고 복귀를 기다리는 시간이다. 단위는 ms이다.
const unsigned long MAX_TAP_DURATION_MS = 5000;  // 한 번의 탭 세션이 최대 5초를 넘지 않게 제한한다.

bool tapping = false;  // 현재 탭 동작 전체가 진행 중인지 저장한다. true이면 탭 반복 중이다.
bool solenoidOn = false;  // 현재 순간에 솔레노이드가 켜져 있는지 저장한다. true이면 전기 인가 중이다.
unsigned long tapStartMillis = 0;  // 탭 세션이 시작된 시각을 millis() 값으로 저장한다.
unsigned long phaseStartMillis = 0;  // 현재 ON 또는 OFF 구간이 시작된 시각을 millis() 값으로 저장한다.

void relayOff() {  // 릴레이를 꺼서 솔레노이드 전원을 차단하는 함수이다.
    digitalWrite(RELAY_PIN, RELAY_OFF_LEVEL);  // D9 핀을 OFF 레벨로 출력해 릴레이를 끈다.
    solenoidOn = false;  // 프로그램 내부 상태도 "솔레노이드 꺼짐"으로 맞춘다.
}

void relayOn() {  // 릴레이를 켜서 솔레노이드에 전기를 인가하는 함수이다.
    digitalWrite(RELAY_PIN, RELAY_ON_LEVEL);  // D9 핀을 ON 레벨로 출력해 릴레이를 켠다.
    solenoidOn = true;  // 프로그램 내부 상태도 "솔레노이드 켜짐"으로 맞춘다.
}

void stopTapping() {  // 탭 반복 동작을 완전히 멈추는 함수이다.
    tapping = false;  // 탭 세션 상태를 false로 바꿔 updateTapping()이 더 이상 동작하지 않게 한다.
    relayOff();  // 안전을 위해 정지할 때는 반드시 릴레이를 끄고 솔레노이드 전원을 차단한다.
}

void startTapping() {  // 탭 반복 동작을 시작하는 함수이다.
    if (!tapping) {  // 이미 탭 중이 아닐 때만 시작 시각을 새로 기록한다.
        tapStartMillis = millis();  // 전체 탭 세션 시작 시간을 저장한다. 5초 제한 계산에 사용된다.
        phaseStartMillis = millis();  // 첫 번째 ON 구간 시작 시간을 저장한다.
        relayOn();  // 시작하자마자 솔레노이드에 짧게 전기를 인가한다.
    }
    tapping = true;  // 탭 세션 상태를 true로 바꿔 updateTapping()이 ON/OFF 반복을 수행하게 한다.
}

void processSerial() {  // Python에서 들어온 시리얼 명령을 읽고 처리하는 함수이다.
    while (Serial.available() > 0) {  // 시리얼 버퍼에 읽을 데이터가 남아 있는 동안 반복한다.
        char cmd = Serial.read();  // Python이 보낸 문자 1개를 읽는다.
        if (cmd == 'T') {  // 명령이 'T'이면 Tapping 시작 명령으로 해석한다.
            startTapping();  // 솔레노이드 탭 반복을 시작한다.
        } else if (cmd == 'S') {  // 명령이 'S'이면 Stop 명령으로 해석한다.
            stopTapping();  // 솔레노이드 탭 반복을 즉시 멈춘다.
        }
    }
}

void updateTapping() {  // 탭 중일 때 솔레노이드 ON/OFF 타이밍을 갱신하는 함수이다.
    if (!tapping) {  // 탭 세션이 진행 중이 아니면 할 일이 없다.
        return;  // 함수 실행을 바로 끝낸다.
    }

    if (millis() - tapStartMillis >= MAX_TAP_DURATION_MS) {  // 탭 시작 후 5초 이상 지났는지 확인한다.
        stopTapping();  // 5초가 넘으면 과열 방지를 위해 무조건 정지한다.
        return;  // 정지 후 아래 ON/OFF 전환 로직은 실행하지 않는다.
    }

    unsigned long phaseElapsed = millis() - phaseStartMillis;  // 현재 ON 또는 OFF 구간이 얼마나 지났는지 계산한다.

    if (solenoidOn) {  // 현재 솔레노이드가 켜져 있는 ON 구간이면 아래 로직을 실행한다.
        if (phaseElapsed >= (unsigned long)TAP_ON_TIME) {  // ON 시간이 80ms 이상 지났는지 확인한다.
            relayOff();  // 80ms가 지나면 릴레이를 꺼서 솔레노이드 전원을 끊는다.
            phaseStartMillis = millis();  // OFF 구간 시작 시간을 새로 기록한다.
        }
    } else {  // 현재 솔레노이드가 꺼져 있는 OFF 구간이면 아래 로직을 실행한다.
        if (phaseElapsed >= (unsigned long)TAP_OFF_TIME) {  // OFF 시간이 120ms 이상 지났는지 확인한다.
            relayOn();  // 120ms가 지나면 다시 릴레이를 켜서 다음 탭을 만든다.
            phaseStartMillis = millis();  // ON 구간 시작 시간을 새로 기록한다.
        }
    }
}

void setup() {  // Arduino가 켜지거나 리셋될 때 한 번만 실행되는 초기화 함수이다.
    digitalWrite(RELAY_PIN, RELAY_OFF_LEVEL);  // pinMode 설정 전에도 가능한 한 OFF 레벨을 먼저 준비한다.
    pinMode(RELAY_PIN, OUTPUT);  // 릴레이 제어 핀을 출력 모드로 설정한다.
    relayOff();  // 시작 직후 릴레이를 확실히 꺼서 솔레노이드가 켜지지 않게 한다.
    Serial.begin(9600);  // Python 코드와 같은 9600 baud 속도로 시리얼 통신을 시작한다.
}

void loop() {  // Arduino가 켜져 있는 동안 계속 반복 실행되는 메인 함수이다.
    processSerial();  // Python에서 새로 들어온 'T' 또는 'S' 명령이 있는지 확인한다.
    updateTapping();  // 탭 중이라면 80ms ON / 120ms OFF 패턴과 5초 제한을 처리한다.
}
