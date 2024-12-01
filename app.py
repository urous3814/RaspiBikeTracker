from flask import Flask, render_template, jsonify, send_file, request
import csv
import os
import paho.mqtt.client as mqtt
import time
import json
import pymysql

app = Flask(__name__)

DATA_DIR = "./data"
# CSV 파일 초기화 제거
# CSV_FILE_PATH = os.path.join(DATA_DIR, "combined_data.csv")

# 데이터베이스 설정
DB_HOST = 'localhost'
DB_USER = 'pi'
DB_PASSWORD = 'your_password'
DB_NAME = 'your_database'
conn = pymysql.connect(host='localhost', user='pi', password='pi', db='TrackData')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS combined_data (
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

# MQTT 설정
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "bike/tracker"
MQTT_PHONE_TOPIC = "phone/tracker"
MQTT_SENSOR_TOPIC = "sensor/data"

# MQTT 클라이언트 설정
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(MQTT_SENSOR_TOPIC)

def find_closest_timestamp(target_timestamp):
    closest_timestamp = None
    min_diff = float('inf')
    for ts in data_buffer.keys():
        diff = abs(time.mktime(time.strptime(ts, "%Y-%m-%d %H:%M:%S")) - time.mktime(time.strptime(target_timestamp, "%Y-%m-%d %H:%M:%S")))
        if diff < min_diff:
            min_diff = diff
            closest_timestamp = ts
    return closest_timestamp

def sync_data():
    for timestamp, data in list(data_buffer.items()):
        if all(key in data for key in ["light", "distance", "humidity", "temperature", "latitude", "longitude", "speed", "altitude"]):
            c.execute("INSERT INTO combined_data (timestamp, light, distance, humidity, temperature, latitude, longitude, speed, altitude) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                      (timestamp, data["light"], data["distance"], data["humidity"], data["temperature"], data["latitude"], data["longitude"], data["speed"], data["altitude"]))
            conn.commit()
            del data_buffer[timestamp]

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    closest_timestamp = find_closest_timestamp(timestamp)
    if closest_timestamp:
        data_buffer[closest_timestamp].update({
            "latitude": data.get('latitude'),
            "longitude": data.get('longitude'),
            "speed": data.get('speed'),
            "altitude": data.get('altitude')
        })
    else:
        data_buffer[timestamp] = {
            "latitude": data.get('latitude'),
            "longitude": data.get('longitude'),
            "speed": data.get('speed'),
            "altitude": data.get('altitude')
        }
    sync_data()

client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# CSV 파일 초기화 제거
# if not os.path.exists(DATA_DIR):
#     os.makedirs(DATA_DIR)

# with open(CSV_FILE_PATH, mode='w') as file:
#     writer = csv.writer(file)
#     writer.writerow(["Timestamp", "Light", "Distance", "Humidity", "Temperature", "Latitude", "Longitude", "Speed", "Altitude"])

def read_sensor_data():
    c.execute("SELECT * FROM combined_data")
    data = c.fetchall()
    return data

def save_combined_data(light, distance, humidity, temperature, latitude, longitude, speed, altitude):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    data_buffer[timestamp] = {
        "light": light,
        "distance": distance,
        "humidity": humidity,
        "temperature": temperature,
        "latitude": latitude,
        "longitude": longitude,
        "speed": speed,
        "altitude": altitude
    }
    sync_data()

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
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    data_buffer[timestamp] = {
        "latitude": data.get('latitude'),
        "longitude": data.get('longitude'),
        "speed": data.get('speed'),
        "altitude": data.get('altitude')
    }
    sync_data()
    client.publish(MQTT_PHONE_TOPIC, str(data))
    return "Data received"

if __name__ == '__main__':
    app.run(debug=True)
    conn.close()