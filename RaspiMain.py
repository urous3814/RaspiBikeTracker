import RPi.GPIO as GPIO
import time
import Adafruit_DHT
import paho.mqtt.client as mqtt
from picamera import PiCamera
import csv
import os
import json
from functions import analyze_image, check_off_road, calculate_rain_probability

# GPIO 핀 설정
LIGHT_SENSOR_PIN = 17
ULTRASONIC_TRIG_PIN = 23
ULTRASONIC_ECHO_PIN = 24
DHT_SENSOR_PIN = 4
LED_PIN = 18
BUTTON_PIN = 27
FRONT_LED_PIN = 22  # 전면 LED 핀
REAR_LED_PIN = 5    # 후면 LED 핀

# MQTT 설정
MQTT_BROKER = "mqtt.example.com"
MQTT_PORT = 1883
MQTT_TOPIC = "bike/tracker"
MQTT_SENSOR_TOPIC = "sensor/data"

# Flask 서버 설정
FLASK_SERVER_URL = "http://localhost:5000/phone_data"

# 센서 초기화
GPIO.setmode(GPIO.BCM)
GPIO.setup(LIGHT_SENSOR_PIN, GPIO.IN)
GPIO.setup(ULTRASONIC_TRIG_PIN, GPIO.OUT)
GPIO.setup(ULTRASONIC_ECHO_PIN, GPIO.IN)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(FRONT_LED_PIN, GPIO.OUT)
GPIO.setup(REAR_LED_PIN, GPIO.OUT)
camera = PiCamera()

# 데이터 저장 디렉토리 설정
DATA_DIR = "./data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# CSV 파일 초기화
csv_file_path = os.path.join(DATA_DIR, "sensor_data.csv")
with open(csv_file_path, mode='w') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Light", "Distance", "Humidity", "Temperature"])

def read_light_sensor():
    return GPIO.input(LIGHT_SENSOR_PIN)

def read_ultrasonic_sensor():
    GPIO.output(ULTRASONIC_TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(ULTRASONIC_TRIG_PIN, False)
    start_time = time.time()
    stop_time = time.time()
    while GPIO.input(ULTRASONIC_ECHO_PIN) == 0:
        start_time = time.time()
    while GPIO.input(ULTRASONIC_ECHO_PIN) == 1:
        stop_time = time.time()
    time_elapsed = stop_time - start_time
    distance = (time_elapsed * 34300) / 2
    return distance

def read_dht_sensor():
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, DHT_SENSOR_PIN)
    return humidity, temperature

def on_button_press(channel):
    print("Button pressed, switching to rest mode")
    # ...휴식 모드 전환 로직...

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

# MQTT 클라이언트 설정
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# 버튼 이벤트 설정
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=on_button_press, bouncetime=300)

def save_sensor_data(light, distance, humidity, temperature):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(csv_file_path, mode='a') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, light, distance, humidity, temperature])

try:
    camera_start_time = time.time()
    while True:
        light = read_light_sensor()
        distance = read_ultrasonic_sensor()
        humidity, temperature = read_dht_sensor()
        
        # 조도센서 경고
        if light < 100:  # 어두운 정도 조정
            GPIO.output(FRONT_LED_PIN, GPIO.HIGH)
            GPIO.output(REAR_LED_PIN, GPIO.HIGH)
            print("Tunnel detected, warning!")
        else:
            GPIO.output(FRONT_LED_PIN, GPIO.LOW)
            GPIO.output(REAR_LED_PIN, GPIO.LOW)
        
        # 초음파센서 경고
        if distance < 30:
            print("Obstacle detected, warning!")
        
        # 온습도센서 경고
        rain_probability = calculate_rain_probability(temperature, humidity)
        if rain_probability > 50:
            GPIO.output(LED_PIN, GPIO.HIGH)
            print("High rain probability detected, warning!")
        else:
            GPIO.output(LED_PIN, GPIO.LOW)
        
        # 센서 데이터 저장
        save_sensor_data(light, distance, humidity, temperature)
        
        # 카메라로 자전거 수 기록 (10초마다)
        current_time = time.time()
        if current_time - camera_start_time >= 10:
            image_path = os.path.join(DATA_DIR, f"bike_image_{int(current_time)}.jpg")
            camera.capture(image_path)
            print("Image captured")
            bike_count = analyze_image(image_path)
            off_road = check_off_road(image_path)
            print(f"Bikes detected: {bike_count}, Off-road: {off_road}")
            camera_start_time = current_time
        
        # Flask 서버로 데이터 전송
        data = {
            "light": light,
            "distance": distance,
            "humidity": humidity,
            "temperature": temperature
        }
        requests.post(FLASK_SERVER_URL, json=data)
        
        # MQTT로 데이터 전송
        client.publish(MQTT_SENSOR_TOPIC, json.dumps(data))
        
        time.sleep(1)

except KeyboardInterrupt:
    print("Program terminated")
    GPIO.cleanup()
