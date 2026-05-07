import serial
import time

#아두이노와 연결 [포트 번호는 환경에 맞게 설정]
arudino = serial.Serial('COM9', 9600, timeout=2)

try:
    while True:
        #LED 켜기
        arudino.write(b'1') #아두이노로 '1' 전송
        print("LED ON")
        time.sleep(1) #1초 대기
        #LED 끄기
        arudino.write(b'0') #아두이노로 '0' 전
        print("LED OFF")
        time.sleep(1) #1초 대기

except KeyboardInterrupt:
    arudino.close() #프로그램 종료시 시리얼 포트 닫기
    print("프로그램 종료")