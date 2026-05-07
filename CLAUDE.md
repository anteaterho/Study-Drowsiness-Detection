# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

- **Python 환경**: Anaconda `drowsiness` 가상환경
- **실행 방법**: `conda activate drowsiness` 후 각 step 파일을 직접 실행
  ```
  python step_5_intergration.py
  ```
- **필수 패키지**: `opencv-python` (headless 버전 아님), `mediapipe`, `numpy`, `pyserial`
- **OpenCV 주의**: `opencv-python-headless`는 `cv2.imshow`가 없으므로 반드시 `opencv-python` 사용

## 프로젝트 구조 (단계별 학습)

각 파일은 독립 실행 가능한 단계별 실습 파일이며, 최종 통합본은 `step_5_intergration.py`이다.

| 파일 | 내용 |
|------|------|
| `step_0_load_image.py` | 정적 이미지 로드 및 표시 |
| `step_1_webcam_input.py` | 웹캠 영상 입력 |
| `step_2_face_landmark.py` | MediaPipe Face Mesh로 478개 랜드마크 시각화 |
| `step_3_EAR.py` | EAR 계산 및 눈 감김 판별 |
| `step_4_serial_communication.py` | Arduino 시리얼 통신 단독 테스트 |
| `step_4_serial_communication.ino` | Arduino 펌웨어 (핀 13 LED 제어) |
| `step_5_intergration.py` | 전체 통합 (EAR + Arduino LED) |

## 핵심 알고리즘

**EAR (Eye Aspect Ratio)**
```
EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
```
- `EAR_THRESHOLD = 0.25`: 이 값 미만이면 눈 감김으로 판단
- `CONSECUTIVE_FRAMES = 4`: 연속 프레임 수 초과 시 DROWSINESS ALERT 표시

**MediaPipe 랜드마크 인덱스 (6점)**
- `RIGHT_EYE = [33, 160, 158, 133, 153, 144]`
- `LEFT_EYE = [362, 385, 387, 263, 373, 380]`

## Arduino 연동

- 통신 속도: 9600 baud
- 프로토콜: `b'1'` → LED ON, `b'0'` → LED OFF
- `step_5_intergration.py`는 COM 포트를 자동 탐지 (`Arduino`, `CH340`, `USB` 키워드 기준)
- Arduino가 없어도 실행 가능 (LED 제어만 비활성화)
- `step_4_serial_communication.ino`를 Arduino IDE로 업로드해야 함

## 이미지 경로

- `assets/lama.jpg`: 프로젝트 루트 기준 상대 경로로 참조 (`'assets/lama.jpg'`)
- Windows 경로 문자열에서 `\a`, `\l` 등은 이스케이프 문자로 해석되므로 슬래시(`/`) 또는 raw string(`r''`) 사용
