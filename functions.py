import cv2
import numpy as np
from sklearn.linear_model import LinearRegression

def analyze_image(image_path):
    """
    사진에서 자전거를 추적하고, 자전거 수를 반환합니다.
    """
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    bike_cascade = cv2.CascadeClassifier('haarcascade_bike.xml')
    bikes = bike_cascade.detectMultiScale(gray, 1.1, 4)
    return len(bikes)

def check_off_road(image_path):
    """
    사진에서 자전거가 길을 벗어났는지 감지합니다.
    """
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    road_cascade = cv2.CascadeClassifier('haarcascade_road.xml')
    roads = road_cascade.detectMultiScale(gray, 1.1, 4)
    return len(roads) == 0

def calculate_rain_probability(temperature, humidity):
    """
    온도와 습도를 기반으로 강수확률을 계산합니다.
    """
    # 간단한 선형 회귀 모델을 사용하여 강수확률을 예측합니다.
    X = np.array([[20, 60], [25, 70], [30, 80], [35, 90]])  # 예시 데이터
    y = np.array([10, 30, 60, 90])  # 예시 강수확률
    model = LinearRegression().fit(X, y)
    rain_probability = model.predict(np.array([[temperature, humidity]]))
    return rain_probability[0]

def additional_analysis(data):
    """
    추가적인 데이터 분석 기능을 구현합니다.
    """
    # 예시: 평균 속도 계산
    speeds = [record['speed'] for record in data if 'speed' in record]
    if speeds:
        average_speed = sum(speeds) / len(speeds)
    else:
        average_speed = 0
    return average_speed