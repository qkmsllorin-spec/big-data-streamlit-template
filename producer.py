import time
import json
import requests
import certifi
from pymongo import MongoClient
from pymongo.errors import PyMongoError, OperationFailure
from datetime import datetime

# Optional Kafka import
try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

# --- CONFIGURATION ---
API_KEY = "c90455a3a30d4c65a1624052262510"  # Your WeatherAPI key
CITY = "Manila"
KAFKA_TOPIC = "weather_stream"

# MongoDB Configuration
MONGO_URI = "mongodb+srv://keonmartinllorin_db_user:BSCPEkeon2024TIP@cluster0.prq2l2r.mongodb.net/?retryWrites=true&w=majority&tls=true&readPreference=primaryPreferred"
DB_NAME = "weather_db"
COLLECTION_NAME = "weather_data"

# Initialize MongoDB Client with SSL/TLS Settings
try:
    client = MongoClient(
        MONGO_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000
    )
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print("Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"Error connecting to MongoDB Atlas: {e}")

# Fetch Weather Data Function
def fetch_weather_data():
    url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={CITY}&aqi=no"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            payload = {
                "city": data["location"]["name"],
                "country": data["location"]["country"],
                "temp_c": data["current"]["temp_c"],
                "humidity": data["current"]["humidity"],
                "condition": data["current"]["condition"]["text"],
                "wind_kph": data["current"]["wind_kph"],
                "timestamp": datetime.utcnow().isoformat()
            }
            return payload
        else:
            print(f"Failed to fetch weather data: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

# Main Execution Loop
if __name__ == "__main__":
    print("Starting Weather Data Producer...")
    while True:
        weather_payload = fetch_weather_data()
        if weather_payload:
            try:
                collection.insert_one(weather_payload)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Saved data to MongoDB Atlas: {weather_payload['city']} - {weather_payload['temp_c']}°C")
            except PyMongoError as e:
                print(f"MongoDB Insert Error: {e}")
        time.sleep(15)  # Fetch update every 15 seconds