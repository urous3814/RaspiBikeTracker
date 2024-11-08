### [index.md](file:///c:/dev/Univ/모스시/MiniProject/docs/index.md)

프로젝트의 개요를 작성합니다.

```markdown
# RaspiBikeTracker

이 프로젝트는 모바일스마트시스템 수업에서 사용할 미니프로젝트로, 라즈베리파이, 윈도우, 웹을 이용하여 자전거 추적 및 경고 시스템을 구현합니다. 이 시스템은 다음과 같은 기능들을 제공합니다:

## 기능

1. **자전거 추적**
   - 핸드폰의 가속도센서와 GPS 데이터를 MQTT를 통해 전송하여 자전거의 위치와 속도를 추적합니다.

2. **조도센서**
   - 조도센서를 이용하여 자전거가 터널 안에 있는지 밖에 있는지 여부를 감지합니다.
   - 만약 터널 안에 있다면 시야확보를 위해 전후면 LED를 켜줍니다.

3. **초음파센서**
   - 초음파센서를 이용하여 충돌 위험을 감지하고 경고합니다.

4. **온습도센서**
   - 온습도센서를 이용하여 강수확률을 계산하고, 비가 올 것 같으면 LED로 경고합니다.

5. **카메라**
   - 카메라를 이용하여 운동 중 마주친 자전거 수를 기록합니다.
   - 자전거가 도로를 벗어나는 경우 경고를 제공합니다.

6. **버튼**
   - 버튼을 이용하여 휴식 모드로 전환할 수 있습니다.

7. **플라스크 웹서버**
   - 플라스크 웹서버를 통해 통계와 운동 기록 등을 볼 수 있습니다.
```

### [setup.md](file:///c:/dev/Univ/모스시/MiniProject/docs/setup.md)

설치 및 실행 방법을 작성합니다.

```markdown
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
```

### [files.md](file:///c:/dev/Univ/모스시/MiniProject/docs/files.md)

각 파일의 역할과 함수들을 소개합니다.

```markdown
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
```

### [navigation.yml](file:///c:/dev/Univ/모스시/MiniProject/docs/_data/navigation.yml)

네비게이션 메뉴를 설정합니다.

```yaml


main:
  - title: "Home"
    url: "/docs/"
  - title: "Setup"
    url: "/docs/setup"
  - title: "Files"
    url: "/docs/files"
```

### [config.yml](file:///c:/dev/Univ/모스시/MiniProject/docs/_config.yml)

프로젝트에 맞게 설정합니다.

```yaml


title: "RaspiBikeTracker"
description: "라즈베리파이와 자전거 추적 시스템을 위한 문서"
baseurl: "/docs"
url: "https://yourusername.github.io"
theme: jekyll-theme-cayman
```

### GitHub Pages 설정

GitHub 리포지토리 설정에서 GitHub Pages를 활성화하고, `docs` 폴더를 소스로 설정합니다.

### Jekyll 사이트 빌드 및 배포

Jekyll 사이트를 빌드하고 GitHub에 푸시합니다.

```bash
bundle exec jekyll build
git add .
git commit -m "Add documentation"
git push origin main
```

이제 GitHub Pages를 통해 프로젝트의 문서를 확인할 수 있습니다.

변경했습니다.

변경했습니다.