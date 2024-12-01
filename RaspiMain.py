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

# GPIO 핀 설정
ULTRASONIC_TRIG_PIN = 20
ULTRASONIC_ECHO_PIN = 16

BUTTON_PIN = 27
# LED들
LED_PIN = 18
FRONT_LED_PIN = 22  # 전면 LED 핀
REAR_LED_PIN = 5    # 후면 LED 핀
# 조도
SPI_SCLK_PIN = 11
SPI_MISO_PIN = 9
SPI_MOSI_PIN = 10
SPI_CE0_PIN = 8
# 온습도
I2C_SDA_PIN = 2
I2C_SCL_PIN = 3

# MQTT 설정
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "bike/tracker"

MQTT_SENSOR_TOPIC = "sensor/data"

DATA_DIR = "./data"

# Flask 서버 설정
FLASK_SERVER_URL = "http://localhost:5000/phone_data"

# 센서 초기화
GPIO.setmode(GPIO.BCM)
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

recording = False  # 기록 상태 변수 추가

def on_button_press(channel):
    global recording
    if recording:
        client.publish(MQTT_TOPIC, "stop")
        recording = False
        print("Recording stopped")
    else:
        client.publish(MQTT_TOPIC, "start")
        recording = True
        print("Recording started")

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

def on_message(client, userdata, msg):
    global recording
    print(msg.topic + " " + str(msg.payload))
    if msg.payload.decode() == "start":
        recording = True
        print("Recording started")
        client.publish("bike/tracker", "start")  # 웹으로 start 메시지 전송
    elif msg.payload.decode() == "stop":
        recording = False
        print("Recording stopped")
        client.publish("bike/tracker", "stop")  # 웹으로 stop 메시지 전송

# MQTT 클라이언트 설정
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# 버튼 이벤트 설정
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=on_button_press, bouncetime=300)

def send_sensor_data(light, distance, humidity, temperature):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    # 이미지 저장
    image_path = os.path.join(DATA_DIR, f"{timestamp.replace(':', '-')}_image.jpg")
    camera.capture(image_path)
    
    data = {
        "light": light,
        "distance": distance,
        "humidity": humidity,
        "temperature": temperature,
        "timestamp": timestamp
    }
    
    # MQTT로 데이터 전송
    client.publish(MQTT_SENSOR_TOPIC, json.dumps(data))

try:
    camera_start_time = time.time()
    while True:
        if recording:  # 기록 중일 때만 센서 데이터 읽기 및 전송
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
            
            
            # 카메라로 자전거 수 기록 (10초마다)
            current_time = time.time()
            if current_time - camera_start_time >= 10:
                timestamp = int(current_time)
                image_path = os.path.join(DATA_DIR, f"{timestamp}_image.jpg")
                camera.capture(image_path)
                print("Image captured")
                bike_count = analyze_image(image_path)
                off_road = check_off_road(image_path)
                print(f"Bikes detected: {bike_count}, Off-road: {off_road}")
                camera_start_time = current_time
            

            send_sensor_data(light, distance, humidity, temperature)

        time.sleep(1)

except KeyboardInterrupt:
    print("Program terminated")
    GPIO.cleanup()
