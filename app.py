from flask import Flask, render_template, jsonify, send_file, request
import csv
import os
import paho.mqtt.client as mqtt
import time
import json

app = Flask(__name__)

DATA_DIR = "./data"
CSV_FILE_PATH = os.path.join(DATA_DIR, "combined_data.csv")

# MQTT 설정
MQTT_BROKER = "mqtt.example.com"
MQTT_PORT = 1883
MQTT_TOPIC = "bike/tracker"
MQTT_PHONE_TOPIC = "phone/tracker"
MQTT_SENSOR_TOPIC = "sensor/data"

# MQTT 클라이언트 설정
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(MQTT_SENSOR_TOPIC)

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    speed = data.get('speed')
    altitude = data.get('altitude')
    light = data.get('light', 0)
    distance = data.get('distance', 0)
    humidity = data.get('humidity', 0)
    temperature = data.get('temperature', 0)
    save_combined_data(light, distance, humidity, temperature, latitude, longitude, speed, altitude)

client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# CSV 파일 초기화
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

with open(CSV_FILE_PATH, mode='w') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Light", "Distance", "Humidity", "Temperature", "Latitude", "Longitude", "Speed", "Altitude"])

def read_sensor_data():
    data = []
    with open(CSV_FILE_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    return data

def save_combined_data(light, distance, humidity, temperature, latitude, longitude, speed, altitude):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILE_PATH, mode='a') as file):
        writer = csv.writer(file)
        writer.writerow([timestamp, light, distance, humidity, temperature, latitude, longitude, speed, altitude])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/records')
def records():
    sensor_data = read_sensor_data()
    return render_template('records.html', data=sensor_data)

@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

@app.route('/map')
def map_view():
    return render_template('map.html')

@app.route('/control')
def control():
    return render_template('control.html')

@app.route('/data')
def data():
    sensor_data = read_sensor_data()
    return jsonify(sensor_data)

@app.route('/image/<timestamp>')
def image(timestamp):
    image_path = os.path.join(DATA_DIR, f"bike_image_{timestamp}.jpg")
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/jpeg')
    else:
        return "Image not found", 404

@app.route('/start', methods=['POST'])
def start():
    client.publish(MQTT_TOPIC, "start")
    return "Recording started"

@app.route('/stop', methods=['POST'])
def stop():
    client.publish(MQTT_TOPIC, "stop")
    return "Recording stopped"

@app.route('/phone_data', methods=['POST'])
def phone_data():
    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    speed = data.get('speed')
    altitude = data.get('altitude')
    # 라즈베리파이에서 수집된 센서 데이터와 합쳐서 저장
    light = data.get('light', 0)
    distance = data.get('distance', 0)
    humidity = data.get('humidity', 0)
    temperature = data.get('temperature', 0)
    save_combined_data(light, distance, humidity, temperature, latitude, longitude, speed, altitude)
    client.publish(MQTT_PHONE_TOPIC, str(data))
    return "Data received"

if __name__ == '__main__':
    app.run(debug=True)