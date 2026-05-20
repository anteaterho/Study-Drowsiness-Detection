import cv2  # OpenCV 라이브러리: 웹캠 영상 읽기, 화면 출력, 그림 그리기에 사용한다.
import mediapipe as mp  # MediaPipe 라이브러리: 얼굴 랜드마크(Face Mesh)를 찾는 데 사용한다.
import numpy as np  # NumPy 라이브러리: 두 점 사이의 거리 계산 등 수학 연산에 사용한다.
import serial  # pyserial 라이브러리: Python에서 Arduino로 시리얼 데이터를 보내는 데 사용한다.
import serial.tools.list_ports  # 연결된 COM 포트를 자동으로 찾기 위해 사용한다.
import time  # 시간 측정, Arduino 리셋 대기, 솔레노이드 동작 시간 제한에 사용한다.


# EAR(Eye Aspect Ratio)를 계산하는 함수이다.
# EAR은 눈이 얼마나 열려 있는지 숫자로 표현하는 값이다.
def calculate_ear(eye):
    # eye에는 눈 주변 6개 랜드마크 좌표가 들어온다.
    # eye[1]과 eye[5]는 눈의 첫 번째 세로 거리 계산에 쓰는 점이다.
    A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))

    # eye[2]와 eye[4]는 눈의 두 번째 세로 거리 계산에 쓰는 점이다.
    B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))

    # eye[0]과 eye[3]은 눈의 가로 길이 계산에 쓰는 점이다.
    C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))

    # EAR 공식: 세로 거리 2개의 합을 가로 거리의 2배로 나눈다.
    # 눈을 감으면 A와 B가 작아져 EAR 값도 작아진다.
    ear = (A + B) / (2.0 * C)

    # 계산된 EAR 값을 함수 밖으로 돌려준다.
    return ear


# -------------------- 파라미터 설정 --------------------

# 눈 감김으로 판단할 EAR 임계값이다.
# 평균 EAR이 이 값보다 작으면 눈을 감았다고 판단한다.
EAR_THRESHOLD = 0.25

# 눈 감김이 몇 프레임 연속으로 유지되어야 졸음/눈감음으로 볼지 정한다.
# 현재 4프레임이라 빠르게 반응하지만, 일반 깜빡임에도 민감할 수 있다.
CONSECUTIVE_FRAMES = 4

# Python 쪽에서 솔레노이드 한 세션을 최대 몇 초까지 허용할지 정한다.
# Arduino의 MAX_TAP_DURATION_MS = 5000과 맞춘 값이다.
SOLENOID_MAX_DURATION = 5.0

# 솔레노이드가 한 번 멈춘 뒤 다시 시작하기 전까지 기다리는 시간이다.
# 눈을 계속 감고 있어도 5초 동작 후 2초 쉬고 다시 동작하게 만든다.
SOLENOID_COOLDOWN = 2.0


# -------------------- MediaPipe Face Mesh 초기화 --------------------

# MediaPipe의 Face Mesh 모듈을 mp_face_mesh라는 이름으로 꺼내 둔다.
mp_face_mesh = mp.solutions.face_mesh

# 얼굴 랜드마크 탐지 객체를 만든다.
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,  # 한 번에 최대 1명의 얼굴만 추적한다.
    refine_landmarks=True,  # 눈동자 주변처럼 더 정밀한 랜드마크도 포함한다.
    min_detection_confidence=0.5,  # 얼굴을 처음 찾을 때 필요한 최소 신뢰도이다.
    min_tracking_confidence=0.5)  # 찾은 얼굴을 계속 추적할 때 필요한 최소 신뢰도이다.


# MediaPipe Face Mesh에서 오른쪽 눈 6개 점의 인덱스이다.
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# MediaPipe Face Mesh에서 왼쪽 눈 6개 점의 인덱스이다.
LEFT_EYE = [362, 385, 387, 263, 373, 380]


# -------------------- Arduino 자동 연결 --------------------

# 현재 PC에 연결된 모든 시리얼 포트 목록을 가져온다.
ports = serial.tools.list_ports.comports()

# 사용자가 어떤 COM 포트가 잡혔는지 볼 수 있게 출력한다.
print("사용 가능한 COM 포트:")

# 연결된 포트들을 하나씩 확인한다.
for p in ports:
    # 포트 이름과 설명을 출력한다. 예: COM3 - USB-SERIAL CH340
    print(f"  {p.device} - {p.description}")

# Arduino 연결 객체를 저장할 변수이다. 처음에는 연결 전이라 None으로 둔다.
arduino = None

# 연결된 포트들 중 Arduino 또는 호환 보드로 보이는 포트를 찾는다.
for p in ports:
    # 설명에 Arduino, CH340, USB 중 하나가 들어 있으면 Arduino 후보로 본다.
    if 'Arduino' in p.description or 'CH340' in p.description or 'USB' in p.description:
        try:
            # 해당 포트를 9600 baud로 연다. Arduino 코드의 Serial.begin(9600)과 같아야 한다.
            arduino = serial.Serial(p.device, 9600, timeout=1)

            # 연결에 성공하면 어떤 포트에 연결됐는지 출력한다.
            print(f"Arduino 연결 성공: {p.device}")

            # Arduino는 시리얼 포트가 열리면 리셋될 수 있으므로 2초 기다린다.
            time.sleep(2)

            # Arduino를 찾았으므로 더 이상 다른 포트를 찾지 않고 반복을 끝낸다.
            break
        except serial.SerialException:
            # 포트를 열다가 실패하면 다음 후보 포트를 계속 확인한다.
            continue

# 끝까지 찾지 못했다면 Arduino 없이 영상 인식만 실행한다.
if arduino is None:
    print("Arduino를 찾을 수 없습니다. 솔레노이드 제어 없이 실행합니다.")


# -------------------- 웹캠 및 상태 변수 초기화 --------------------

# 0번 웹캠을 연다. 노트북 기본 카메라나 첫 번째 USB 웹캠이 보통 0번이다.
cap = cv2.VideoCapture(0)

# 눈을 감은 프레임이 연속으로 몇 번 나왔는지 세는 변수이다.
frame_counter = 0

# 현재 Python이 솔레노이드 탭 동작 중이라고 인식하는지 저장한다.
solenoid_tapping = False

# 솔레노이드 탭 세션이 시작된 시간을 저장한다. 아직 시작 전이면 None이다.
tap_session_start = None

# 마지막으로 솔레노이드를 멈춘 시간을 저장한다. 쿨다운 계산에 사용한다.
last_tap_stop_time = 0.0


def stop_solenoid():
    # 이 함수 안에서 전역 상태 변수를 수정하겠다고 Python에 알려준다.
    global solenoid_tapping, tap_session_start, last_tap_stop_time

    # 현재 탭 중이고 Arduino도 연결되어 있으면 Arduino에 정지 명령 'S'를 보낸다.
    if solenoid_tapping and arduino:
        arduino.write(b'S')

    # 실제로 탭 중이던 상태에서 멈추는 경우에만 마지막 정지 시간을 기록한다.
    if solenoid_tapping:
        last_tap_stop_time = time.time()

    # Python 내부 상태를 "탭 중 아님"으로 바꾼다.
    solenoid_tapping = False

    # 탭 세션 시작 시간도 비워 둔다.
    tap_session_start = None


def can_start_tap():
    # 마지막 정지 이후 SOLENOID_COOLDOWN초가 지났는지 확인한다.
    return time.time() - last_tap_stop_time >= SOLENOID_COOLDOWN


def start_solenoid():
    # 이 함수 안에서 전역 상태 변수를 수정하겠다고 Python에 알려준다.
    global solenoid_tapping, tap_session_start

    # Arduino가 연결되어 있으면 탭 시작 명령 'T'를 보낸다.
    if arduino:
        arduino.write(b'T')

    # Python 내부 상태를 "탭 중"으로 바꾼다.
    solenoid_tapping = True

    # 탭 세션이 시작된 현재 시간을 저장한다. 5초 제한 계산에 사용한다.
    tap_session_start = time.time()


# -------------------- 메인 반복문 --------------------

# 웹캠이 정상적으로 열려 있는 동안 계속 반복한다.
while cap.isOpened():
    # 웹캠에서 프레임 1장을 읽는다.
    success, image = cap.read()

    # 프레임을 읽지 못하면 오류 메시지를 출력하고 반복문을 종료한다.
    if not success:
        print("카메라에서 프레임을 읽을 수 없습니다.")
        break

    # 좌우 반전해서 거울처럼 보이게 만든 뒤, OpenCV의 BGR 이미지를 MediaPipe용 RGB로 바꾼다.
    image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)

    # MediaPipe Face Mesh로 얼굴 랜드마크를 탐지한다.
    results = face_mesh.process(image)

    # 화면 출력과 OpenCV 그리기 함수 사용을 위해 RGB 이미지를 다시 BGR로 바꾼다.
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Python 쪽에서도 솔레노이드가 5초 이상 동작하지 않도록 한 번 더 감시한다.
    if solenoid_tapping and tap_session_start is not None:
        # 현재 시간에서 탭 시작 시간을 뺀 값이 최대 허용 시간 이상이면 정지한다.
        if time.time() - tap_session_start >= SOLENOID_MAX_DURATION:
            stop_solenoid()

    # 얼굴 랜드마크가 하나 이상 탐지되었는지 확인한다.
    if results.multi_face_landmarks:
        # 탐지된 얼굴들을 하나씩 처리한다. max_num_faces=1이라 보통 한 번만 돈다.
        for face_landmarks in results.multi_face_landmarks:
            # MediaPipe 랜드마크는 0~1 사이 비율 좌표라서 화면 픽셀 좌표로 변환해야 한다.
            landmarks = []

            # 얼굴의 모든 랜드마크를 하나씩 가져온다.
            for lm in face_landmarks.landmark:
                # x 비율 좌표에 이미지 너비를 곱해서 실제 픽셀 x 좌표로 바꾼다.
                x = int(lm.x * image.shape[1])

                # y 비율 좌표에 이미지 높이를 곱해서 실제 픽셀 y 좌표로 바꾼다.
                y = int(lm.y * image.shape[0])

                # 변환한 픽셀 좌표를 리스트에 저장한다.
                landmarks.append((x, y))

            # 왼쪽 눈에 해당하는 6개 랜드마크 좌표만 뽑아낸다.
            left_eye = [landmarks[i] for i in LEFT_EYE]

            # 오른쪽 눈에 해당하는 6개 랜드마크 좌표만 뽑아낸다.
            right_eye = [landmarks[i] for i in RIGHT_EYE]

            # 왼쪽 눈 EAR 값을 계산한다.
            left_EAR = calculate_ear(left_eye)

            # 오른쪽 눈 EAR 값을 계산한다.
            right_EAR = calculate_ear(right_eye)

            # 양쪽 눈 EAR 평균을 사용해 최종 눈 감김 정도를 판단한다.
            avg_EAR = (left_EAR + right_EAR) / 2.0

            # 평균 EAR이 임계값보다 작으면 눈을 감은 상태로 판단한다.
            if avg_EAR < EAR_THRESHOLD:
                # 눈 감김이 연속으로 몇 프레임 이어졌는지 증가시킨다.
                frame_counter += 1

                # 화면에 표시할 상태 문자열을 CLOSED로 설정한다.
                state = "CLOSED"

                # 눈 감김 상태는 빨간색으로 표시한다. OpenCV 색상 순서는 BGR이다.
                color = (0, 0, 255)

                # 충분한 프레임 동안 눈이 감겼고, 현재 탭 중이 아니며, 쿨다운도 끝났는지 확인한다.
                if (frame_counter >= CONSECUTIVE_FRAMES
                        and not solenoid_tapping
                        and can_start_tap()):
                    # 조건이 맞으면 Arduino에 'T'를 보내 솔레노이드 탭을 시작한다.
                    start_solenoid()
            else:
                # EAR이 임계값 이상이면 눈을 뜬 상태로 보고 카운터를 초기화한다.
                frame_counter = 0

                # 화면에 표시할 상태 문자열을 OPEN으로 설정한다.
                state = "OPEN"

                # 눈 뜬 상태는 초록색으로 표시한다. OpenCV 색상 순서는 BGR이다.
                color = (0, 255, 0)

                # 눈을 떴는데 솔레노이드가 동작 중이면 즉시 멈춘다.
                if solenoid_tapping:
                    stop_solenoid()

            # 왼쪽/오른쪽 눈 6개 점을 화면에 작은 파란 점으로 표시한다.
            for i in range(6):
                # 왼쪽 눈 랜드마크 점을 그린다.
                cv2.circle(image, left_eye[i], 2, (255, 0, 0), -1)

                # 오른쪽 눈 랜드마크 점을 그린다.
                cv2.circle(image, right_eye[i], 2, (255, 0, 0), -1)

            # 화면 왼쪽 위에 EAR 값과 OPEN/CLOSED 상태를 표시한다.
            cv2.putText(image, f"EAR: {avg_EAR:.2f} - {state}", (30, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # 눈 감김이 기준 프레임 이상이면 졸음 알림 문구를 표시한다.
            if frame_counter >= CONSECUTIVE_FRAMES:
                cv2.putText(image, "DROWSINESS ALERT! - SOLENOID TAPPING", (30, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    else:
        # 얼굴을 찾지 못하면 눈 감김 카운터를 초기화한다.
        frame_counter = 0

        # 얼굴이 사라졌는데 솔레노이드가 동작 중이면 안전을 위해 즉시 멈춘다.
        if solenoid_tapping:
            stop_solenoid()

        # 화면에 얼굴이 감지되지 않았다는 메시지를 표시한다.
        cv2.putText(image, "NO FACE DETECTED", (30, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

    # 처리된 영상을 창에 표시한다.
    cv2.imshow('EAR Eye Detector', image)

    # 5ms 동안 키 입력을 확인하고, q 키가 눌리면 프로그램을 종료한다.
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

# 반복문이 끝나면 웹캠 장치를 해제한다.
cap.release()

# OpenCV로 만든 모든 창을 닫는다.
cv2.destroyAllWindows()

# Arduino가 연결되어 있으면 종료 직전에 솔레노이드 정지 명령을 한 번 더 보낸다.
if arduino:
    # 혹시 탭 중인 상태로 프로그램이 끝나는 것을 방지하기 위해 'S'를 보낸다.
    arduino.write(b'S')

    # 시리얼 포트를 닫아 Arduino 연결을 정리한다.
    arduino.close()