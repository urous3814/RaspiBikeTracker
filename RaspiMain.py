import RPi.GPIO as GPIO
import time
import Adafruit_DHT
import paho.mqtt.client as mqtt
from picamera import PiCamera
import csv
import os
import json
from functions import analyze_image, check_off_road, calculate_rain_probability
import busio
from adafruit_htu21d import HTU21D
import Adafruit_MCP3008
import pymysql

# GPIO 핀 설정
LIGHT_SENSOR_PIN = 17
ULTRASONIC_TRIG_PIN = 23
ULTRASONIC_ECHO_PIN = 24
DHT_SENSOR_PIN = 4
LED_PIN = 18
BUTTON_PIN = 27
FRONT_LED_PIN = 22  # 전면 LED 핀
REAR_LED_PIN = 5    # 후면 LED 핀
SPI_SCLK_PIN = 11
SPI_MISO_PIN = 9
SPI_MOSI_PIN = 10
SPI_CE0_PIN = 8
I2C_SDA_PIN = 2
I2C_SCL_PIN = 3

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

# I2C 설정
i2c = busio.I2C(I2C_SCL_PIN, I2C_SDA_PIN)
htu21d_sensor = HTU21D(i2c)

# SPI 설정
mcp = Adafruit_MCP3008.MCP3008(clk=SPI_SCLK_PIN, cs=SPI_CE0_PIN, miso=SPI_MISO_PIN, mosi=SPI_MOSI_PIN)

# 데이터 저장 디렉토리 설정
DATA_DIR = "./data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 데이터베이스 설정
DB_HOST = 'your_host'
DB_USER = 'your_user'
DB_PASSWORD = 'your_password'
DB_NAME = 'your_database'
conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sensor_data (
                timestamp VARCHAR(255),
                light FLOAT,
                distance FLOAT,
                humidity FLOAT,
                temperature FLOAT,
                latitude FLOAT,
                longitude FLOAT,
                speed FLOAT,
                altitude FLOAT
            )''')
conn.commit()

# 데이터 동기화 버퍼
data_buffer = {}

def read_light_sensor():
    return mcp.read_adc(0)

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
    humidity = htu21d_sensor.relative_humidity
    temperature = htu21d_sensor.temperature
    return humidity, temperature

def on_button_press(channel):
    print("Button pressed, switching to rest mode")
    # ...휴식 모드 전환 로직...

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    data_buffer[timestamp] = {
        "latitude": data.get('latitude'),
        "longitude": data.get('longitude'),
        "speed": data.get('speed'),
        "altitude": data.get('altitude')
    }
    sync_data()

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
    data_buffer[timestamp] = {
        "light": light,
        "distance": distance,
        "humidity": humidity,
        "temperature": temperature
    }
    sync_data()

def sync_data():
    for timestamp, data in list(data_buffer.items()):
        if "latitude" in data and "longitude" in data and "speed" in data and "altitude" in data:
            c.execute("INSERT INTO sensor_data (timestamp, light, distance, humidity, temperature, latitude, longitude, speed, altitude) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                      (timestamp, data["light"], data["distance"], data["humidity"], data["temperature"], data["latitude"], data["longitude"], data["speed"], data["altitude"]))
            conn.commit()
            del data_buffer[timestamp]

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
    conn.close()
