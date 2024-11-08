# 설치 및 실행 방법

## 라즈베리파이 설정

1. **필요한 라이브러리 설치**
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip
   pip3 install RPi.GPIO Adafruit_DHT paho-mqtt picamera opencv-python-headless scikit-learn
   ```

2. **센서 및 카메라 모듈 연결**
   - 라즈베리파이에 조도센서, 초음파센서, 온습도센서, 카메라 모듈, LED, 버튼을 연결합니다.

3. **`RaspiMain.py` 실행하여 데이터 수집 시작**
   ```bash
   python3 RaspiMain.py
   ```

## 윈도우 설정

1. **MQTT 클라이언트 설치**
   - MQTT 클라이언트를 설치하고, `app.py`에서 설정한 MQTT 브로커 주소를 사용하여 연결합니다.

2. **데이터 시각화 및 분석 프로그램 실행**
   - 플라스크 웹서버를 실행하여 통계 및 운동 기록을 확인합니다.

## 웹 서버 설정

1. **플라스크 설치**
   ```bash
   pip install flask
   ```

2. **웹 서버 실행하여 통계 및 운동 기록 확인**
   ```bash
   python app.py
   ```