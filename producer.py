import time
import requests
import certifi
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datetime import datetime
import zoneinfo

# --- CONFIGURATION ---
API_KEY = "c90455a3a30d4c65a1624052262510"

# Use GPS coordinates to lock Pasig City, Metro Manila, Philippines
CITY_QUERY = "14.5764,121.0851"
DISPLAY_CITY = "Pasig"

# MongoDB Atlas Configuration
MONGO_URI = "mongodb+srv://keonmartinllorin_db_user:BSCPEkeon2024TIP@cluster0.prq2l2r.mongodb.net/?retryWrites=true&w=majority&tls=true&readPreference=primaryPreferred"
DB_NAME = "weather_db"
COLLECTION_NAME = "weather_data"

# Local Timezone Configuration (Manila / PST)
MANILA_TZ = zoneinfo.ZoneInfo("Asia/Manila")

try:
    client = MongoClient(
        MONGO_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000
    )
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print("✓ Connected to MongoDB Atlas (Locked to Pasig City Coordinates: 14.5764, 121.0851)!")
except Exception as e:
    print(f"❌ Connection Error: {e}")

def fetch_weather_data():
    url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={CITY_QUERY}&aqi=yes"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            curr = data.get("current", {})
            loc = data.get("location", {})
            aqi_data = curr.get("air_quality", {})

            now_manila = datetime.now(MANILA_TZ)

            payload = {
                "timestamp": now_manila.isoformat(),
                "local_time_str": now_manila.strftime("%A, %b %d, %Y • %I:%M:%S %p"),
                "value": float(curr.get("temp_c", 0.0)),
                "metric_type": "Temperature_C",
                "sensor_id": "sensor_pasig_01",
                "city": DISPLAY_CITY,
                "country": "Philippines",
                "temp_c": float(curr.get("temp_c", 0.0)),
                "feelslike_c": float(curr.get("feelslike_c", curr.get("temp_c", 0.0))),
                "humidity": int(curr.get("humidity", 0)),
                "condition": curr.get("condition", {}).get("text", "Unknown"),
                "wind_kph": float(curr.get("wind_kph", 0.0)),
                "wind_degree": int(curr.get("wind_degree", curr.get("wind_dir_degree", 90))),
                "wind_dir": curr.get("wind_dir", "E"),
                "wind_gust_kph": float(curr.get("gust_kph", curr.get("wind_kph", 0.0))),
                "precip_mm": float(curr.get("precip_mm", 0.0)),
                "pressure_mb": float(curr.get("pressure_mb", 1013.0)),
                "vis_km": float(curr.get("vis_km", 10.0)),
                "uv_index": float(curr.get("uv", 5.0)),
                "cloud_cover": int(curr.get("cloud", 20)),
                "dewpoint_c": float(curr.get("dewpoint_c", curr.get("temp_c", 0.0) - 4)),
                "aqi": int(aqi_data.get("us-epa-index", 2) * 25),
                "pm2_5": float(aqi_data.get("pm2_5", 15.0))
            }
            return payload
        else:
            print(f"⚠️ WeatherAPI Error HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Ingestion Error: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Ingesting Hyperlocal Real-Time Signals for Pasig, Philippines (30s Cycle)...")
    while True:
        weather_payload = fetch_weather_data()
        if weather_payload:
            try:
                collection.insert_one(weather_payload)
                print(f"[{weather_payload['local_time_str']}] Ingested: {weather_payload['city']}, {weather_payload['country']} | {weather_payload['temp_c']}°C | {weather_payload['condition']}")
            except PyMongoError as e:
                print(f"❌ MongoDB Insert Error: {e}")
        time.sleep(15)