import streamlit as st
import pandas as pd
from pymongo import MongoClient, DESCENDING
import certifi
import io
import time

# --- MONGODB CONFIGURATION ---
MONGO_URI = "mongodb+srv://keonmartinllorin_db_user:BSCPEkeon2024TIP@cluster0.prq2l2r.mongodb.net/?retryWrites=true&w=majority&tls=true&readPreference=primaryPreferred"
DB_NAME = "weather_db"
COLLECTION_NAME = "weather_data"

st.set_page_config(
    page_title="Meteorological Live Telemetry", 
    layout="wide", 
    page_icon="🌤️",
    initial_sidebar_state="expanded"
)

# --- ATMOSPHERIC WEATHER THEME CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #f0f4f8 0%, #e2e8f0 100%); }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    .weather-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(8px);
        border: 1px solid #cbd5e1;
        border-left: 5px solid #0284c7;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
        transition: all 0.2s ease;
    }
    .weather-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(14, 165, 233, 0.15);
        border-left: 5px solid #38bdf8;
    }
    .weather-label {
        font-size: 0.8rem;
        font-weight: 700;
        color: #0369a1;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }
    .weather-value { font-size: 1.8rem; font-weight: 800; color: #0f172a; }
    .sky-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff;
        box-shadow: 0 2px 8px rgba(3, 105, 161, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# --- HIGH-PERFORMANCE DATABASE CONNECTION ---
@st.cache_resource
def get_mongo_db():
    client = MongoClient(
        MONGO_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
        retryWrites=True,
        retryReads=True
    )
    return client[DB_NAME]

try:
    db = get_mongo_db()
    collection = db[COLLECTION_NAME]
except Exception as e:
    st.error(f"MongoDB Connection Timeout: {e}")

# High-speed cached query functions
@st.cache_data(ttl=5)
def fetch_recent_telemetry(limit_num):
    cursor = collection.find({}, {"_id": 0}).sort("timestamp", DESCENDING).limit(limit_num)
    return list(cursor)

@st.cache_data(ttl=5)
def fetch_latest_signal():
    return collection.find_one({}, {"_id": 0}, sort=[("timestamp", DESCENDING)])

def get_weather_icon(condition_str):
    cond = str(condition_str).lower()
    if "clear" in cond or "sun" in cond: return "☀️"
    elif "rain" in cond or "drizzle" in cond: return "🌧️"
    elif "cloud" in cond or "overcast" in cond: return "☁️"
    elif "thunder" in cond: return "🌩️"
    elif "snow" in cond or "ice" in cond: return "❄️"
    return "🌤️"

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("## 🌤️ Atmospheric Navigation")
page = st.sidebar.radio("Go to View", ["Live Streaming View", "History & Analytics"])
st.sidebar.divider()

# Ultra-fast metadata document count (<2ms)
try:
    total_docs = collection.estimated_document_count()
except Exception:
    total_docs = "N/A"

st.sidebar.markdown("### 📡 Radar Telemetry")
st.sidebar.metric("Database Stream Records", total_docs)
st.sidebar.caption("Big Data Engineering Project | Weather API → MongoDB Atlas → Streamlit")

# ==========================================
# PAGE 1: LIVE STREAMING VIEW
# ==========================================
if page == "Live Streaming View":
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.title("🌤️ Real-Time Atmospheric Station")
        st.caption("Live streaming weather data feed directly integrated into MongoDB Atlas")
    with header_col2:
        st.markdown("<br><span class='sky-badge'>📡 Station Online</span>", unsafe_allow_html=True)

    st.divider()

    latest = fetch_latest_signal()

    if latest:
        col1, col2, col3, col4 = st.columns(4)
        
        city_name = latest.get('city', 'N/A')
        country_name = latest.get('country', 'N/A')
        temp_val = latest.get('temp_c', latest.get('value', 'N/A'))
        humidity_val = latest.get('humidity', 'N/A')
        cond_val = latest.get('condition', 'N/A')
        cond_icon = get_weather_icon(cond_val)

        col1.markdown(f"""
            <div class="weather-card">
                <div class="weather-label">📍 Station Location</div>
                <div class="weather-value">{city_name}, {country_name}</div>
            </div>
        """, unsafe_allow_html=True)

        col2.markdown(f"""
            <div class="weather-card">
                <div class="weather-label">🌡️ Ambient Temp</div>
                <div class="weather-value">{temp_val} °C</div>
            </div>
        """, unsafe_allow_html=True)

        col3.markdown(f"""
            <div class="weather-card">
                <div class="weather-label">💧 Relative Humidity</div>
                <div class="weather-value">{humidity_val}%</div>
            </div>
        """, unsafe_allow_html=True)

        col4.markdown(f"""
            <div class="weather-card">
                <div class="weather-label">{cond_icon} Sky Condition</div>
                <div class="weather-value" style="font-size: 1.4rem;">{cond_val}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📡 Live Stream Ingest Log (Last 10 Signals)")
    
    data = fetch_recent_telemetry(10)

    if data:
        df_live = pd.DataFrame(data)
        display_cols = [c for c in ["timestamp", "city", "country", "temp_c", "humidity", "condition", "wind_kph", "value", "sensor_id"] if c in df_live.columns]
        st.dataframe(df_live[display_cols], use_container_width=True, height=380)
    else:
        st.info("No records found in streaming pipeline.")

    st.markdown("<br>", unsafe_allow_html=True)
    btn_col, auto_col = st.columns([1, 2])
    
    with btn_col:
        if st.button("🔄 Sync Live Feed", type="primary"):
            st.cache_data.clear()
            st.rerun()
            
    with auto_col:
        auto_refresh = st.checkbox("⏱️ Auto-Sync Stream (Every 15s)")
        if auto_refresh:
            time.sleep(15)
            st.cache_data.clear()
            st.rerun()

# ==========================================
# PAGE 2: HISTORY & ANALYTICS
# ==========================================
elif page == "History & Analytics":
    st.title("📊 Meteorological Historical Logs & Analytics")
    st.caption("Perform climate trend analysis, inspect aggregated statistical metrics, and export data logs")

    st.sidebar.markdown("### 🎛️ Station Controls")
    record_limit = st.sidebar.slider("Select Historic Record Limit", min_value=10, max_value=1000, value=100, step=10)
    
    data = fetch_recent_telemetry(record_limit)

    if data:
        df_hist = pd.DataFrame(data)
        
        # Safe ISO8601 parsing to fix timestamp format error
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"], format='ISO8601', errors='coerce')
        df_hist = df_hist.sort_values("timestamp")

        temp_col = "temp_c" if "temp_c" in df_hist.columns and df_hist["temp_c"].notna().any() else "value"

        # --- ACCURATE AGGREGATION CALCULATIONS ---
        st.divider()
        st.subheader("📈 Climate Summary Aggregations")
        
        agg_col1, agg_col2, agg_col3, agg_col4 = st.columns(4)
        
        clean_temp = df_hist[temp_col].dropna().astype(float)
        avg_temp = round(clean_temp.mean(), 2) if not clean_temp.empty else 0.0
        max_temp = round(clean_temp.max(), 2) if not clean_temp.empty else 0.0
        min_temp = round(clean_temp.min(), 2) if not clean_temp.empty else 0.0
        
        agg_col1.markdown(f"""
            <div class="weather-card">
                <div class="weather-label">Mean Temperature</div>
                <div class="weather-value">{avg_temp} °C</div>
            </div>
        """, unsafe_allow_html=True)

        agg_col2.markdown(f"""
            <div class="weather-card">
                <div class="weather-label">Peak Temperature</div>
                <div class="weather-value">{max_temp} °C</div>
            </div>
        """, unsafe_allow_html=True)

        agg_col3.markdown(f"""
            <div class="weather-card">
                <div class="weather-label">Lowest Temperature</div>
                <div class="weather-value">{min_temp} °C</div>
            </div>
        """, unsafe_allow_html=True)

        if "humidity" in df_hist.columns and df_hist["humidity"].notna().any():
            clean_hum = df_hist["humidity"].dropna().astype(float)
            avg_hum = round(clean_hum.mean(), 2) if not clean_hum.empty else 0.0
            agg_col4.markdown(f"""
                <div class="weather-card">
                    <div class="weather-label">Mean Humidity</div>
                    <div class="weather-value">{avg_hum}%</div>
                </div>
            """, unsafe_allow_html=True)

        # --- MULTI-METRIC TREND CHARTS ---
        st.divider()
        st.subheader("📉 Historical Weather Trends")
        
        tab1, tab2, tab3 = st.tabs(["🌡️ Temperature Profile", "💧 Humidity Profile", "💨 Wind Speed Profile"])
        
        with tab1:
            chart_df_temp = df_hist.set_index("timestamp")[[temp_col]]
            st.line_chart(chart_df_temp, height=300)
            
        with tab2:
            if "humidity" in df_hist.columns and df_hist["humidity"].notna().any():
                chart_df_hum = df_hist.set_index("timestamp")[["humidity"]]
                st.line_chart(chart_df_hum, height=300)
            else:
                st.info("Humidity history not available in current records.")
                
        with tab3:
            if "wind_kph" in df_hist.columns and df_hist["wind_kph"].notna().any():
                chart_df_wind = df_hist.set_index("timestamp")[["wind_kph"]]
                st.line_chart(chart_df_wind, height=300)
            else:
                st.info("Wind speed history not available in current records.")

        # --- FILTER & EXPORT ---
        st.divider()
        st.subheader("📋 Complete Telemetry Archive Log")
        
        if "condition" in df_hist.columns and df_hist["condition"].notna().any():
            unique_conditions = ["All Conditions"] + list(df_hist["condition"].dropna().unique())
            selected_condition = st.selectbox("🔍 Filter Log by Weather Condition", unique_conditions)
            
            if selected_condition != "All Conditions":
                df_filtered = df_hist[df_hist["condition"] == selected_condition]
            else:
                df_filtered = df_hist
        else:
            df_filtered = df_hist

        display_cols = [c for c in ["timestamp", "city", "country", "temp_c", "humidity", "condition", "wind_kph", "value", "metric_type", "sensor_id"] if c in df_filtered.columns]
        st.dataframe(df_filtered[display_cols], use_container_width=True, height=350)

        st.divider()
        st.subheader("📥 Export Telemetry Archives")
        
        exp_col1, exp_col2, _ = st.columns([1, 1, 2])
        
        # CSV Export
        csv_bytes = df_filtered.to_csv(index=False).encode('utf-8')
        exp_col1.download_button(
            label="📄 Export as CSV Log",
            data=csv_bytes,
            file_name="weather_telemetry_report.csv",
            mime="text/csv",
            use_container_width=True
        )

        # Excel Export with Timezone Fix
        excel_buffer = io.BytesIO()
        df_excel = df_filtered.copy()
        
        # Strip timezones for openpyxl compatibility
        if "timestamp" in df_excel.columns and pd.api.types.is_datetime64_any_dtype(df_excel["timestamp"]):
            df_excel["timestamp"] = df_excel["timestamp"].dt.tz_localize(None)

        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Weather_Telemetry')
        
        exp_col2.download_button(
            label="📊 Export as Excel (.xlsx)",
            data=excel_buffer.getvalue(),
            file_name="weather_telemetry_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    else:
        st.warning("No historical records returned from MongoDB query.")