import cv2
import mediapipe as mp
import numpy as np
import serial
import serial.tools.list_ports
import time



#EAR 계산 함수

def calculate_ear(eye):

    #눈 수직 랜드마크 거리 계산(2개 쌍)
    A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
    B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))

    #눈 수평 랜드마크 거리 계산
    C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))

    #EAR 계산
    ear = (A + B) / (2.0 * C)
    return ear



# 파라미터 설정
# 눈 감김으로 판단할 EAR 임계값 (보통 0.2~0.25)
EAR_THRESHOLD = 0.25

# 눈 감김 지속 프레임 수 임계값 (약 4프레임 @30fps ≈ 0.13초)
CONSECUTIVE_FRAMES = 4

# 솔레노이드 한 세션 최대 동작 시간(초) — Arduino MAX_TAP_DURATION_MS와 맞춤
SOLENOID_MAX_DURATION = 5.0

# 세션 종료 후 다음 탭까지 대기(초)
SOLENOID_COOLDOWN = 2.0

# mediapipe 솔루션 초기화
mp_face_mesh = mp.solutions.face_mesh

# 얼굴 메쉬 모델 로드 (최대 1명 탐지, 신뢰도 0.5 이상)
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True, #눈동자 랜드마크 포함
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

#mediapipe 랜드마크 인덱스 (Face Mesh)
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
LEFT_EYE = [362, 385, 387, 263, 373, 380]

# 연결된 COM 포트 목록 출력 후 Arduino 자동 탐지
ports = serial.tools.list_ports.comports()
print("사용 가능한 COM 포트:")
for p in ports:
    print(f"  {p.device} - {p.description}")

arduino = None
for p in ports:
    if 'Arduino' in p.description or 'CH340' in p.description or 'USB' in p.description:
        try:
            arduino = serial.Serial(p.device, 9600, timeout=1)
            print(f"Arduino 연결 성공: {p.device}")
            time.sleep(2)  # Arduino 리셋 대기
            break
        except serial.SerialException:
            continue

if arduino is None:
    print("Arduino를 찾을 수 없습니다. 솔레노이드 제어 없이 실행합니다.")

# 웹캠 영상 처리
cap = cv2.VideoCapture(0)
frame_counter = 0
solenoid_tapping = False
tap_session_start = None
last_tap_stop_time = 0.0


def stop_solenoid():
    global solenoid_tapping, tap_session_start, last_tap_stop_time
    if solenoid_tapping and arduino:
        arduino.write(b'S')
    if solenoid_tapping:
        last_tap_stop_time = time.time()
    solenoid_tapping = False
    tap_session_start = None

def can_start_tap():
    return time.time() - last_tap_stop_time >= SOLENOID_COOLDOWN

def start_solenoid():
    global solenoid_tapping, tap_session_start
    if arduino:
        arduino.write(b'T')
    solenoid_tapping = True
    tap_session_start = time.time()

while cap.isOpened():
    success, image = cap.read()
    if not success:
        print("카메라에서 프레임을 읽을 수 없습니다.")
        break

    # 성능을 위해 이미지를 좌우 반전하고 BGR을 RGB로 변환
    image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)

    #랜드마크 탐지
    results = face_mesh.process(image)
    #다시 BGR로 변환하여 OpenCV에서 사용
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if solenoid_tapping and tap_session_start is not None:
        if time.time() - tap_session_start >= SOLENOID_MAX_DURATION:
            stop_solenoid()

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            #눈 랜드마크 좌표 픽셀화 (normalized -> pixel)
            landmarks = []
            for lm in face_landmarks.landmark:
                x = int(lm.x * image.shape[1])
                y = int(lm.y * image.shape[0])
                landmarks.append((x, y))

            # 왼쪽/오른쪽 눈 좌표 추출
            left_eye = [landmarks[i] for i in LEFT_EYE]
            right_eye = [landmarks[i] for i in RIGHT_EYE]

            # EAR 계산
            left_EAR = calculate_ear(left_eye)
            right_EAR = calculate_ear(right_eye)

            # 평균 EAR
            avg_EAR = (left_EAR + right_EAR) / 2.0

            # --- 눈 감김 판별 및 솔레노이드 제어 로직 ---
            if avg_EAR < EAR_THRESHOLD:
                frame_counter += 1
                state = "CLOSED"
                color = (0, 0, 255) # 빨간색

                if (frame_counter >= CONSECUTIVE_FRAMES
                        and not solenoid_tapping
                        and can_start_tap()):
                    start_solenoid()
            else:
                frame_counter = 0
                state = "OPEN"
                color = (0, 255, 0) # 초록색
                if solenoid_tapping:
                    stop_solenoid()

            # 화면에 랜드마크 및 EAR 값 표시
            for i in range(6):
                cv2.circle(image, left_eye[i], 2, (255, 0, 0), -1)
                cv2.circle(image, right_eye[i], 2, (255, 0, 0), -1)

            cv2.putText(image, f"EAR: {avg_EAR:.2f} - {state}", (30, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            if frame_counter >= CONSECUTIVE_FRAMES:
                cv2.putText(image, "DROWSINESS ALERT! - SOLENOID TAPPING", (30, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    else:
        frame_counter = 0
        if solenoid_tapping:
            stop_solenoid()
        cv2.putText(image, "NO FACE DETECTED", (30, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

    cv2.imshow('EAR Eye Detector', image)

    if cv2.waitKey(5) & 0xFF == ord('q'): #q를 누르면 종료
        break
cap.release()
cv2.destroyAllWindows()

if arduino:
    arduino.write(b'S')  # 종료 시 솔레노이드 정지
    arduino.close()