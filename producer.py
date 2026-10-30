import time
import requests
import certifi
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datetime import datetime, timezone

# --- CONFIGURATION ---
API_KEY = "c90455a3a30d4c65a1624052262510"
CITY = "Manila"

# MongoDB Atlas Configuration
MONGO_URI = "mongodb+srv://keonmartinllorin_db_user:BSCPEkeon2024TIP@cluster0.prq2l2r.mongodb.net/?retryWrites=true&w=majority&tls=true&readPreference=primaryPreferred"
DB_NAME = "weather_db"
COLLECTION_NAME = "weather_data"

# Initialize MongoDB Client with strict timeouts
try:
    client = MongoClient(
        MONGO_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000
    )
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print("✓ Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ Connection Error: {e}")

def fetch_weather_data():
    url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={CITY}&aqi=no"
    try:
        # Enforce 5-second timeout for rapid API response
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            curr = data.get("current", {})
            loc = data.get("location", {})

            payload = {
                # Standardized UTC ISO Timestamp for high accuracy sorting
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "value": float(curr.get("temp_c", 0.0)),
                "metric_type": "Temperature_C",
                "sensor_id": f"sensor_{CITY.lower()}_01",
                "city": loc.get("name", CITY),
                "country": loc.get("country", "Philippines"),
                "temp_c": float(curr.get("temp_c", 0.0)),
                "humidity": int(curr.get("humidity", 0)),
                "condition": curr.get("condition", {}).get("text", "Unknown"),
                "wind_kph": float(curr.get("wind_kph", 0.0))
            }
            return payload
        else:
            print(f"⚠️ WeatherAPI Error HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Data Retrieval Timeout/Error: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Ingestion Pipeline Started (30s Cycle)...")
    while True:
        weather_payload = fetch_weather_data()
        if weather_payload:
            try:
                collection.insert_one(weather_payload)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Ingested: {weather_payload['city']} | {weather_payload['temp_c']}°C | {weather_payload['condition']}")
            except PyMongoError as e:
                print(f"❌ MongoDB Insert Failed: {e}")
        time.sleep(30)