import io
import os
import zoneinfo
from datetime import datetime, timedelta

import certifi
import pandas as pd
import plotly.graph_objects as go
from pymongo import DESCENDING, MongoClient
import streamlit as st

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="MetNet Telemetry Portal • Pasig",
    layout="wide",
    page_icon="🌤️",
    initial_sidebar_state="expanded",
)

# 2. TIME & DATABASE CONFIGURATION (Manila PST Timezone)
MANILA_TZ = zoneinfo.ZoneInfo("Asia/Manila")
MONGO_URI = "mongodb+srv://keonmartinllorin_db_user:BSCPEkeon2024TIP@cluster0.prq2l2r.mongodb.net/?retryWrites=true&w=majority&tls=true&readPreference=primaryPreferred"
DB_NAME = os.getenv("DB_NAME", "weather_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "weather_data")

# 3. DYNAMIC DAY/NIGHT THEME SWITCHER (Day Theme: 6:00 AM to 5:59 PM)
now_pst = datetime.now(MANILA_TZ)
current_hour = now_pst.hour
is_night = current_hour >= 18 or current_hour < 6

if is_night:
    # Soft "Light Dark" Palette (Slate Blue / Charcoal Gray)
    bg_color = "#0f172a"
    card_bg = "#1e293b"
    text_color = "#f8fafc"
    subtext_color = "#94a3b8"
    sidebar_bg = "#1e293b"
    sidebar_text = "#f8fafc"
    border_color = "#334155"
    plotly_template = "plotly_dark"
    tab_text_color = "#cbd5e1"
    tab_active_color = "#38bdf8"
else:
    # Day Theme Palette (Triggers automatically at 6:00 AM)
    bg_color = "#f4f7fc"
    card_bg = "#ffffff"
    text_color = "#0f172a"
    subtext_color = "#475569"
    sidebar_bg = "#e2e8f0"
    sidebar_text = "#0f172a"
    border_color = "#cbd5e1"
    plotly_template = "plotly_white"
    tab_text_color = "#64748b"
    tab_active_color = "#0284c7"

# Full UI Theme CSS Injector
st.markdown(
    f"""
    <style>
    header[data-testid="stHeader"], .stAppHeader {{
        background-color: {bg_color} !important;
        background: {bg_color} !important;
    }}
    
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
    }}
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{
        color: {sidebar_text} !important;
        opacity: 1 !important;
        -webkit-font-smoothing: antialiased;
    }}
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {{
        color: {subtext_color} !important;
    }}

    .weather-card, .hero-card, .metric-card {{
        background-color: {card_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 16px;
        padding: 20px;
        color: {text_color} !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }}

    .subtext, .muted-text {{
        color: {subtext_color} !important;
    }}

    .location-header {{
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 12px;
        color: {text_color};
    }}

    /* Tab Styling Adjustments */
    button[data-baseweb="tab"] p {{
        color: {tab_text_color} !important;
        font-weight: 600 !important;
    }}
    button[aria-selected="true"] p {{
        color: {tab_active_color} !important;
    }}

    div.stDownloadButton > button {{
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 600 !important;
    }}
    div.stDownloadButton > button:hover {{
        background-color: #0369a1 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# --- DATABASE ENGINE ---
@st.cache_resource
def get_mongo_collection():
    if not MONGO_URI:
        return None
    try:
        client = MongoClient(
            MONGO_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            retryWrites=True,
            retryReads=True,
        )
        return client[DB_NAME][COLLECTION_NAME]
    except Exception as exc:
        st.toast(f"MongoDB connection unavailable: {exc}")
        return None


def build_demo_records():
    """Generates real-time telemetry matching Pasig, Metro Manila metrics."""
    now = datetime.now(MANILA_TZ)
    records = []
    for idx in range(48):
        ts = now - timedelta(hours=47 - idx)
        temp = 29.0 + 2.5 * __import__("math").sin((idx - 8) / 3.8)
        feels = temp + 2.0
        humidity = 72 + int(6 * __import__("math").cos(idx / 4))
        wind = 7.0 + (idx % 3)
        pressure = 1014.0 + (idx % 2) * 0.5
        precip = max(0.0, 1.0 * __import__("math").sin(idx / 3.5))
        cloud = 65 + ((idx * 5) % 20)
        uv = max(0.0, 6.0 * __import__("math").sin((idx % 24) / 3.8)) if (ts.hour >= 6 and ts.hour <= 17) else 0.0
        records.append(
            {
                "timestamp": ts.isoformat(),
                "local_time_str": ts.strftime("%A, %b %d, %Y %I:%M:%S %p"),
                "city": "Pasig",
                "country": "Philippines",
                "temp_c": round(temp, 1),
                "feelslike_c": round(feels, 1),
                "humidity": max(40, min(95, humidity)),
                "condition": "Mostly cloudy",
                "wind_kph": round(wind, 1),
                "wind_dir": "◄",
                "wind_gust_kph": round(wind + 4.0, 1),
                "precip_mm": round(precip, 1),
                "pressure_mb": round(pressure, 1),
                "vis_km": 10,
                "uv_index": round(uv, 1),
                "cloud_cover": min(100, cloud),
                "dewpoint_c": 24.0,
                "aqi": 30 + (idx % 15),
                "pm2_5": round(7.0 + (idx % 4) * 0.5, 1),
            }
        )
    return records


def fetch_recent_telemetry(limit_num=200):
    collection = get_mongo_collection()
    if collection is not None:
        try:
            docs = list(
                collection.find({}, {"_id": 0})
                .sort("timestamp", DESCENDING)
                .limit(limit_num)
            )
            if docs:
                return docs
        except Exception:
            pass
    return build_demo_records()[-limit_num:]


def fetch_latest_signal():
    collection = get_mongo_collection()
    if collection is not None:
        try:
            doc = collection.find_one({}, {"_id": 0}, sort=[("timestamp", DESCENDING)])
            if doc:
                return doc
        except Exception:
            pass
    demo = build_demo_records()
    return demo[-1]


def normalize_dataframe(records):
    df = pd.DataFrame(records)
    if df.empty:
        return df
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    numeric_cols = [
        "temp_c",
        "feelslike_c",
        "humidity",
        "wind_kph",
        "wind_gust_kph",
        "precip_mm",
        "pressure_mb",
        "vis_km",
        "uv_index",
        "cloud_cover",
        "dewpoint_c",
        "aqi",
        "pm2_5",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "metric_type" in df.columns and "value" in df.columns:
        pivoted = df.pivot_table(
            index="timestamp",
            columns="metric_type",
            values="value",
            aggfunc="first",
        ).reset_index()
        df = pd.merge_ordered(df, pivoted, on="timestamp", fill_method="ffill")

    return df


def get_weather_icon(condition_str):
    cond = str(condition_str).lower()
    if "clear" in cond or "sun" in cond:
        return "☀️" if not is_night else "🌙"
    if "rain" in cond or "drizzle" in cond:
        return "🌧️"
    if "cloud" in cond or "overcast" in cond:
        return "⛅" if not is_night else "🌙☁️"
    if "thunder" in cond:
        return "⛈️"
    return "🌤️" if not is_night else "🌙"


def get_base_chart_layout(title_text):
    return {
        "margin": {"l": 30, "r": 30, "t": 30, "b": 30},
        "height": 340,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "template": plotly_template,
        "font": {"color": text_color},
        "xaxis": {
            "showgrid": True,
            "gridcolor": "#334155" if is_night else "#e2e8f0",
            "zeroline": False,
        },
        "yaxis": {
            "title": title_text,
            "showgrid": True,
            "gridcolor": "#334155" if is_night else "#e2e8f0",
            "zeroline": False,
        },
        "hovermode": "x unified",
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    }


# --- SIDEBAR UI ---
st.sidebar.title("🌤️ Weather Hub Portal")
page = st.sidebar.radio(
    "View Navigation",
    [
        "Live Station Overview",
        "Weather Details & Metrics",
        "Historical Trends",
        "Telemetry Logs & Export",
    ],
)

try:
    collection = get_mongo_collection()
    total_docs = collection.estimated_document_count() if collection is not None else 0
except Exception:
    total_docs = 0

st.sidebar.metric("Streamed Telemetry Docs", total_docs)
st.sidebar.caption(f"PST Local Time: {datetime.now(MANILA_TZ).strftime('%I:%M:%S %p')}")
st.sidebar.caption("Big Data Engineering | Weather API → MongoDB Atlas → Streamlit")

latest = fetch_latest_signal() or {}
raw_records = fetch_recent_telemetry(200)
df = normalize_dataframe(raw_records)

# Direct live Manila time binding
live_time_str = datetime.now(MANILA_TZ).strftime("%I:%M %p")

# --- PAGE ROUTING ---
if page == "Live Station Overview":
    temp = float(latest.get("temp_c", 29.0))
    feels = float(latest.get("feelslike_c", 31.0))
    cond = latest.get("condition", "Mostly cloudy")
    wind_spd = float(latest.get("wind_kph", 7.0))
    wind_dir = latest.get("wind_dir", "◄")
    hum_val = int(latest.get("humidity", 72))
    vis_val = float(latest.get("vis_km", 10.0))
    press_val = float(latest.get("pressure_mb", 1014.0))
    dew_val = float(latest.get("dewpoint_c", 24.0))
    icon = get_weather_icon(cond)

    st.markdown('<div class="location-header">Pasig, Metro Manila 🏠</div>', unsafe_allow_html=True)

    col_hero, col_map = st.columns([1.8, 1.2])

    with col_hero:
        st.markdown(
            f"""
            <div class="hero-card">
                <div style="font-size: 0.9rem; color: {subtext_color}; font-weight: 700;">Current weather</div>
                <div style="font-size: 0.85rem; color: {subtext_color}; margin-bottom: 12px;">{live_time_str}</div>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="font-size: 4.5rem;">{icon}</div>
                    <div>
                        <div style="font-size: 4.2rem; font-weight: 800; line-height: 1;">{temp:.0f}°C</div>
                    </div>
                    <div style="margin-left: 10px;">
                        <div style="font-size: 1.3rem; font-weight: 700;">{cond}</div>
                        <div style="font-size: 0.95rem; color: {subtext_color};">Feels like <b>{feels:.0f}°</b></div>
                    </div>
                </div>
                <div style="margin-top: 16px; color: {subtext_color}; font-size: 0.95rem;">
                    The skies will be partly cloudy. The low will be 26°.
                </div>
                <hr style="margin: 16px 0; border: none; border-top: 1px solid {border_color};">
                <div style="display: flex; justify-content: space-between; font-size: 0.88rem; color: {subtext_color}; flex-wrap: wrap; gap: 12px;">
                    <div>Wind ℹ️<br><b>{wind_spd:.0f} km/h {wind_dir}</b></div>
                    <div>Humidity ℹ️<br><b>{hum_val}%</b></div>
                    <div>Visibility ℹ️<br><b>{vis_val:.0f} km</b></div>
                    <div>Pressure ℹ️<br><b>{press_val:.0f} mb</b></div>
                    <div>Dew point ℹ️<br><b>{dew_val:.0f}°</b></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_map:
        # EXACT GPS COORDINATES: 14°36'45.1"N 121°05'58.9"E
        map_df = pd.DataFrame(
            {
                "lat": [14.612528],
                "lon": [121.099694],
            }
        )
        st.map(map_df, zoom=13, size=150, height=280)

    st.subheader("Hourly Forecast & Parameter Profiles")

    overview_tabs = st.tabs(
        [
            "Overview",
            "Precipitation",
            "Wind",
            "Air Quality",
            "Humidity",
            "Cloud Cover",
            "Pressure",
            "UV Index",
            "Visibility",
        ]
    )

    if not df.empty:
        df_hourly = df.copy()
        if "timestamp" in df_hourly.columns:
            df_hourly = (
                df_hourly.set_index("timestamp")
                .resample("1h")
                .mean(numeric_only=True)
                .reset_index()
            )

        with overview_tabs[0]:  # Overview
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("temp_c", pd.Series([temp] * len(df_hourly))),
                    mode="lines+markers",
                    name="Temperature (°C)",
                    line={"color": "#ef4444", "width": 3, "shape": "spline"},
                    fill="tozeroy",
                    fillcolor="rgba(239, 68, 68, 0.15)",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get(
                        "feelslike_c",
                        df_hourly.get("temp_c", pd.Series([feels] * len(df_hourly))),
                    ),
                    mode="lines",
                    name="Feels like (°C)",
                    line={"color": "#f97316", "width": 2, "dash": "dash"},
                )
            )
            fig.update_layout(**get_base_chart_layout("°C"))
            st.plotly_chart(fig, use_container_width=True)

        with overview_tabs[1]:  # Precipitation
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("precip_mm", pd.Series([0.0] * len(df_hourly))),
                    name="Precipitation (mm)",
                    marker={"color": "#3b82f6"},
                )
            )
            fig.update_layout(**get_base_chart_layout("Precipitation (mm)"))
            st.plotly_chart(fig, use_container_width=True)

        with overview_tabs[2]:  # Wind
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("wind_kph", pd.Series([7.0] * len(df_hourly))),
                    mode="lines+markers",
                    name="Wind Speed (km/h)",
                    line={"color": "#0ea5e9", "width": 3},
                )
            )
            fig.update_layout(**get_base_chart_layout("km/h"))
            st.plotly_chart(fig, use_container_width=True)

        with overview_tabs[3]:  # Air Quality
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("aqi", pd.Series([30] * len(df_hourly))),
                    mode="lines+markers",
                    name="Air Quality Index (AQI)",
                    line={"color": "#eab308", "width": 3},
                )
            )
            fig.update_layout(**get_base_chart_layout("AQI"))
            st.plotly_chart(fig, use_container_width=True)

        with overview_tabs[4]:  # Humidity
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("humidity", pd.Series([72] * len(df_hourly))),
                    mode="lines+markers",
                    name="Humidity (%)",
                    line={"color": "#06b6d4", "width": 3},
                )
            )
            fig.update_layout(**get_base_chart_layout("%"))
            st.plotly_chart(fig, use_container_width=True)

        with overview_tabs[5]:  # Cloud Cover
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("cloud_cover", pd.Series([65] * len(df_hourly))),
                    mode="lines+markers",
                    name="Cloud Cover (%)",
                    line={"color": "#64748b", "width": 3},
                )
            )
            fig.update_layout(**get_base_chart_layout("%"))
            st.plotly_chart(fig, use_container_width=True)

        with overview_tabs[6]:  # Pressure
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("pressure_mb", pd.Series([1014] * len(df_hourly))),
                    mode="lines+markers",
                    name="Pressure (mb)",
                    line={"color": "#8b5cf6", "width": 3},
                )
            )
            fig.update_layout(**get_base_chart_layout("mb"))
            st.plotly_chart(fig, use_container_width=True)

        with overview_tabs[7]:  # UV Index
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("uv_index", pd.Series([0.0] * len(df_hourly))),
                    name="UV Index",
                    marker={"color": "#f97316"},
                )
            )
            fig.update_layout(**get_base_chart_layout("UV Index"))
            st.plotly_chart(fig, use_container_width=True)

        with overview_tabs[8]:  # Visibility
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("vis_km", pd.Series([10.0] * len(df_hourly))),
                    mode="lines+markers",
                    name="Visibility (km)",
                    line={"color": "#10b981", "width": 3},
                )
            )
            fig.update_layout(**get_base_chart_layout("km"))
            st.plotly_chart(fig, use_container_width=True)

elif page == "Weather Details & Metrics":
    st.title("Weather details (Pasig, Metro Manila)")
    st.caption("Granular metric inspection across active telemetry channels")

    cloud_val = float(latest.get("cloud_cover", 65))
    cloud_status = "Mostly Cloudy"

    precip_val = float(latest.get("precip_mm", 0.0))
    precip_status = "Chance of Rain"

    uv_val = float(latest.get("uv_index", 0.0))
    uv_status = "Low / Night"

    aqi_val = float(latest.get("aqi", 30))
    aqi_status = "Good"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""<div class="metric-card"><div style="font-size:0.8rem;color:{subtext_color};font-weight:700;">Temperature</div>
            <div style="font-size:2.4rem;font-weight:800;">{float(latest.get('temp_c', 29)):.0f}°</div>
            <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#fef3c7;color:#92400e;font-size:0.75rem;font-weight:700;">Steady</span>
            <p style="font-size:0.85rem;color:{subtext_color};margin-top:8px;">Live conditions for Pasig, Metro Manila.</p></div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="metric-card"><div style="font-size:0.8rem;color:{subtext_color};font-weight:700;">Feels like</div>
            <div style="font-size:2.4rem;font-weight:800;">{float(latest.get('feelslike_c', 31)):.0f}°</div>
            <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#fde68a;color:#78350f;font-size:0.75rem;font-weight:700;">Warm</span>
            <p style="font-size:0.85rem;color:{subtext_color};margin-top:8px;">Comfort index based on humidity.</p></div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""<div class="metric-card"><div style="font-size:0.8rem;color:{subtext_color};font-weight:700;">Cloud cover</div>
            <div style="font-size:2.4rem;font-weight:800;">{cloud_val:.0f}%</div>
            <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#e0f2fe;color:#075985;font-size:0.75rem;font-weight:700;">{cloud_status}</span>
            <p style="font-size:0.85rem;color:{subtext_color};margin-top:8px;">Dominant cloud density around station.</p></div>""",
            unsafe_allow_html=True,
        )

    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(
            f"""<div class="metric-card"><div style="font-size:0.8rem;color:{subtext_color};font-weight:700;">Precipitation</div>
            <div style="font-size:2.4rem;font-weight:800;">{precip_val:.1f} mm</div>
            <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#fef3c7;color:#92400e;font-size:0.75rem;font-weight:700;">{precip_status}</span>
            <p style="font-size:0.85rem;color:{subtext_color};margin-top:8px;">Short-term rainfall accumulation.</p></div>""",
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            f"""<div class="metric-card"><div style="font-size:0.8rem;color:{subtext_color};font-weight:700;">Wind</div>
            <div style="font-size:2.4rem;font-weight:800;">{float(latest.get('wind_kph', 7)):.0f} <span style="font-size:1rem;">km/h</span></div>
            <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#dbeafe;color:#1d4ed8;font-size:0.75rem;font-weight:700;">Light breeze</span>
            <p style="font-size:0.85rem;color:{subtext_color};margin-top:8px;">Gusts up to {float(latest.get('wind_gust_kph', 12)):.0f} km/h.</p></div>""",
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            f"""<div class="metric-card"><div style="font-size:0.8rem;color:{subtext_color};font-weight:700;">Humidity</div>
            <div style="font-size:2.4rem;font-weight:800;">{int(latest.get('humidity', 72))}%</div>
            <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#e0f2fe;color:#075985;font-size:0.75rem;font-weight:700;">Dew point: 24°</span>
            <p style="font-size:0.85rem;color:{subtext_color};margin-top:8px;">Moisture level is elevated.</p></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    c7, c8, c9 = st.columns(3)
    with c7:
        st.markdown(
            f"""<div class="metric-card"><div style="font-size:0.8rem;color:{subtext_color};font-weight:700;">UV index</div>
            <div style="font-size:2.4rem;font-weight:800;">{uv_val:.0f}</div>
            <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#fef3c7;color:#92400e;font-size:0.75rem;font-weight:700;">{uv_status}</span>
            <p style="font-size:0.85rem;color:{subtext_color};margin-top:8px;">Daily exposure rating.</p></div>""",
            unsafe_allow_html=True,
        )
    with c8:
        st.markdown(
            f"""<div class="metric-card"><div style="font-size:0.8rem;color:{subtext_color};font-weight:700;">AQI</div>
            <div style="font-size:2.4rem;font-weight:800;">{aqi_val:.0f}</div>
            <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#dcfce7;color:#166534;font-size:0.75rem;font-weight:700;">{aqi_status}</span>
            <p style="font-size:0.85rem;color:{subtext_color};margin-top:8px;">Air quality index for the area.</p></div>""",
            unsafe_allow_html=True,
        )
    with c9:
        st.markdown(
            f"""<div class="metric-card"><div style="font-size:0.8rem;color:{subtext_color};font-weight:700;">Visibility</div>
            <div style="font-size:2.4rem;font-weight:800;">10 km</div>
            <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#dcfce7;color:#166534;font-size:0.75rem;font-weight:700;">Good</span>
            <p style="font-size:0.85rem;color:{subtext_color};margin-top:8px;">Conditions persist across the station.</p></div>""",
            unsafe_allow_html=True,
        )

elif page == "Historical Trends":
    st.title("Historical trends")
    if df.empty:
        st.info("No historical data is available yet.")
    else:
        chart_tabs = st.tabs(
            ["Temperature", "Humidity", "Wind & Pressure", "Air quality"]
        )
        with chart_tabs[0]:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df.get("temp_c", pd.Series([29.0] * len(df))),
                    mode="lines+markers",
                    name="Temperature (°C)",
                    line={"color": "#ef4444", "width": 3},
                    marker={"size": 5},
                )
            )
            fig.update_layout(**get_base_chart_layout("°C"))
            st.plotly_chart(fig, use_container_width=True)

        with chart_tabs[1]:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df.get("humidity", pd.Series([72] * len(df))),
                    mode="lines+markers",
                    name="Humidity (%)",
                    line={"color": "#06b6d4", "width": 3},
                    marker={"size": 5},
                )
            )
            fig.update_layout(**get_base_chart_layout("%"))
            st.plotly_chart(fig, use_container_width=True)

        with chart_tabs[2]:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df.get("wind_kph", pd.Series([7.0] * len(df))),
                    mode="lines+markers",
                    name="Wind speed (km/h)",
                    line={"color": "#0ea5e9", "width": 3},
                    marker={"size": 5},
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df.get("pressure_mb", pd.Series([1014] * len(df))),
                    mode="lines+markers",
                    name="Pressure (mb)",
                    line={"color": "#8b5cf6", "width": 2},
                    marker={"size": 4},
                    yaxis="y2",
                )
            )
            layout = get_base_chart_layout("km/h")
            layout["yaxis2"] = {
                "overlaying": "y",
                "side": "right",
                "title": "Pressure (mb)",
                "showgrid": False,
            }
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True)

        with chart_tabs[3]:
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=df["timestamp"],
                    y=df.get("aqi", pd.Series([30] * len(df))),
                    name="AQI",
                    marker={"color": "#eab308"},
                )
            )
            fig.update_layout(**get_base_chart_layout("AQI"))
            st.plotly_chart(fig, use_container_width=True)

else:
    st.title("Telemetry logs & export")
    st.caption("Latest sensor records from the weather data stream")
    if df.empty:
        st.info("No telemetry rows are available yet.")
    else:
        st.dataframe(df.tail(50), use_container_width=True)

        col_csv, col_excel = st.columns([1, 1])

        with col_csv:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Export Telemetry as CSV",
                data=csv_buffer.getvalue(),
                file_name="pasig_weather_telemetry.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_excel:
            df_excel = df.copy()
            for col in df_excel.select_dtypes(include=["datetimetz"]).columns:
                df_excel[col] = df_excel[col].dt.tz_localize(None)

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df_excel.to_excel(writer, index=False, sheet_name="Telemetry_Data")
            st.download_button(
                label="📊 Export Telemetry as Excel",
                data=excel_buffer.getvalue(),
                file_name="pasig_weather_telemetry.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )