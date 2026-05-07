import cv2
import mediapipe as mp

#mediapipe 솔류션 초기화
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

#웸캠 캡쳐 시작
cap = cv2.VideoCapture(0)

#face mesh 모델 설정 (정밀도 높임)
with mp_face_mesh.FaceMesh(
    max_num_faces = 1, #최대 감지할 얼굴 수
    refine_landmarks = True, #눈,입술,눈썹 랜드마크 추가(478개)
    min_detection_confidence = 0.5, #얼굴 감지 신뢰도 임계값
    min_tracking_confidence = 0.5) as face_mesh: #얼굴 랜드마크 추적 신뢰도 임계값

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("카메라에서 프레임을 읽을 수 없습니다.")
            break
        
        #성능을 위해 이미지를 작성 불가 상태로 설정
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image)

        #이미지에 얼굴 랜드마크를 그림
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                #랜드마크를 그리기
                mp_drawing.draw_landmarks(
                    image = image,
                    landmark_list = face_landmarks,
                    connections = mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec = None,
                    connection_drawing_spec = mp_drawing_styles.get_default_face_mesh_tesselation_style())
                
                #눈썹 및 눈동자 윤곽 그리기
                mp_drawing.draw_landmarks(
                    image = image,
                    landmark_list = face_landmarks,
                    connections = mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec = None,
                    connection_drawing_spec = mp_drawing_styles.get_default_face_mesh_contours_style())
            
        #결과 이미지 출력
        cv2.imshow('MediaPipe Face Mesh', cv2.flip(image, 1))
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break
cap.release()
cv2.destroyAllWindows()