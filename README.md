# 졸음 감지 시스템 (Study Drowsiness Detection)

OpenCV와 MediaPipe를 활용하여 실시간으로 눈 감김을 감지하고, Arduino LED로 경보를 출력하는 졸음 감지 프로젝트입니다.

## 동작 원리

**EAR (Eye Aspect Ratio)** 알고리즘으로 눈의 개폐 상태를 수치화합니다.

```
EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
```

MediaPipe Face Mesh가 얼굴의 478개 랜드마크를 실시간으로 추적하고, 눈 주변 6개 좌표로 EAR을 계산합니다. EAR이 임계값(`0.25`) 미만으로 일정 프레임(`4프레임`) 이상 지속되면 졸음으로 판단합니다.

## 시스템 구성

```
웹캠 → MediaPipe Face Mesh → EAR 계산 → 졸음 판별 → Arduino LED 제어
```

## 개발 환경

- Python 3.x (Anaconda 가상환경 권장)
- Arduino (핀 13 내장 LED)

## 설치

```bash
conda create -n drowsiness python=3.10
conda activate drowsiness
pip install opencv-python mediapipe numpy pyserial
```

> `opencv-python-headless`는 `cv2.imshow`를 지원하지 않으므로 반드시 `opencv-python`을 사용해야 합니다.

## Arduino 준비

`step_4_serial_communication.ino`를 Arduino IDE로 보드에 업로드합니다.

```cpp
void setup() {
    pinMode(13, OUTPUT);
    Serial.begin(9600);
}

void loop() {
    if (Serial.available() > 0) {
        char data = Serial.read();
        if (data == '1') digitalWrite(13, HIGH);
        else if (data == '0') digitalWrite(13, LOW);
    }
}
```

## 실행

```bash
conda activate drowsiness
python step_5_intergration.py
```

Arduino가 연결되지 않아도 실행 가능합니다 (LED 제어만 비활성화). `q` 키를 누르면 종료됩니다.

## 파일 구성

| 파일 | 설명 |
|------|------|
| `step_0_load_image.py` | 이미지 파일 로드 및 표시 |
| `step_1_webcam_input.py` | 웹캠 영상 입력 |
| `step_2_face_landmark.py` | MediaPipe 얼굴 랜드마크 시각화 |
| `step_3_EAR.py` | EAR 계산 및 눈 감김 판별 |
| `step_4_serial_communication.py` | Arduino 시리얼 통신 테스트 |
| `step_4_serial_communication.ino` | Arduino 펌웨어 |
| `step_5_intergration.py` | 전체 통합 실행 파일 |

## 주요 파라미터

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `EAR_THRESHOLD` | 0.25 | 눈 감김 판단 기준값 |
| `CONSECUTIVE_FRAMES` | 4 | 졸음 판단에 필요한 연속 프레임 수 |

## 사용 기술

- [OpenCV](https://opencv.org/) - 영상 처리
- [MediaPipe](https://mediapipe.dev/) - 얼굴 랜드마크 감지
- [pyserial](https://pyserial.readthedocs.io/) - Arduino 시리얼 통신
