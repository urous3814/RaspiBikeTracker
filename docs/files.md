# 파일 설명

## RaspiMain.py

라즈베리파이에서 센서 데이터를 수집하고 처리하는 메인 파일입니다.

### 주요 함수

- `read_light_sensor()`: 조도센서 데이터를 읽습니다.
- `read_ultrasonic_sensor()`: 초음파센서 데이터를 읽습니다.
- `read_dht_sensor()`: 온습도센서 데이터를 읽습니다.
- `on_button_press(channel)`: 버튼이 눌렸을 때 호출되는 콜백 함수입니다.
- `save_sensor_data(light, distance, humidity, temperature)`: 센서 데이터를 CSV 파일에 저장합니다.

## app.py

플라스크 웹서버를 설정하고, 운동 기록을 통계로 보여주거나 지도에 경로를 표시하며, 경로 클릭 시 센서 정보와 사진을 볼 수 있도록 합니다.

### 주요 함수

- `read_sensor_data()`: CSV 파일에서 센서 데이터를 읽습니다.
- `save_combined_data(light, distance, humidity, temperature, latitude, longitude, speed, altitude)`: 센서 데이터를 CSV 파일에 저장합니다.

## functions.py

복잡한 기능들을 처리하는 파일입니다. 사진 분석, 자전거 추적, 길 벗어남 감지, 강수확률 측정 등의 기능이 포함됩니다.

### 주요 함수

- `analyze_image(image_path)`: 사진에서 자전거를 추적하고, 자전거 수를 반환합니다.
- `check_off_road(image_path)`: 사진에서 자전거가 길을 벗어났는지 감지합니다.
- `calculate_rain_probability(temperature, humidity)`: 온도와 습도를 기반으로 강수확률을 계산합니다.
- `additional_analysis(data)`: 추가적인 데이터 분석 기능을 구현합니다.