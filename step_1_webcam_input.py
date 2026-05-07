import cv2

#내장 카메라 연결
cap = cv2.VideoCapture(0)

#카메라가 정상적으로 연결이 되었는지 확인
if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

while True:
    #카메라 프레임 읽기
    ret, frame = cap.read()

    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break

    fliipped_frame = cv2.flip(frame, 1)

    #화면에 웹캠 영상을 출력
    cv2.imshow('Webcam', frame)

    # 'q'키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()