import streamlit as st
import pandas as pd
from pymongo import MongoClient
import certifi

# Configuration
MONGO_URI = "mongodb+srv://keonmartinllorin_db_user:BSCPEkeon2024TIP@cluster0.prq2l2r.mongodb.net/?retryWrites=true&w=majority&tls=true&readPreference=primaryPreferred"
DB_NAME = "weather_db"
COLLECTION_NAME = "weather_data"

st.set_page_config(page_title="Live Weather Dashboard", layout="wide")

@st.cache_resource
def get_mongo_client():
    return MongoClient(
        MONGO_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=20000,  # Extended to 20s to handle connection delays
        connectTimeoutMS=20000,
        retryWrites=True,
        retryReads=True
    )

# Page Layout & Header
st.title("Real-Time Weather Monitoring Dashboard")

try:
    client = get_mongo_client()
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Fetch latest record for KPI metrics
    latest_record = collection.find_one(sort=[("timestamp", -1)])

    if latest_record:
        col1, col2, col3 = st.columns(3)
        col1.metric("Location", f"{latest_record.get('city', 'N/A')}, {latest_record.get('country', 'N/A')}")
        col2.metric("Temperature", f"{latest_record.get('temp_c', 'N/A')} °C")
        col3.metric("Humidity", f"{latest_record.get('humidity', 'N/A')}%")

    st.subheader("Recent Updates")
    # Fetch recent records for the data table
    cursor = collection.find().sort("timestamp", -1).limit(10)
    data = list(cursor)

    if data:
        # Convert MongoDB ObjectId to string for PyArrow compatibility
        for row in data:
            if "_id" in row:
                row["_id"] = str(row["_id"])

        df = pd.DataFrame(data)
        st.dataframe(df)
    else:
        st.warning("No weather data found in MongoDB Atlas yet.")

except Exception as e:
    st.error(f"Failed to connect to MongoDB Atlas: {e}")

if st.button("Refresh Data"):
    st.rerun()