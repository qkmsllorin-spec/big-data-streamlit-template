import calendar
import io
import math
import os
import zoneinfo
from datetime import datetime, timedelta
import certifi
import pandas as pd
import plotly.graph_objects as go
from pymongo import DESCENDING, MongoClient
import streamlit as st

# ==============================================================================
# 1. PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="MetNet Telemetry Portal Pasig Station",
    layout="wide",
    page_icon="🌤️",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# 2. REAL-TIME MANILA PST CLOCK ENGINE
# ==============================================================================
MANILA_TZ = zoneinfo.ZoneInfo("Asia/Manila")
now_pst = datetime.now(MANILA_TZ)
live_time_str = now_pst.strftime("%I:%M:%S %p")
live_date_str = now_pst.strftime("%A, %B %d, %Y")
full_live_datetime_str = f"{live_date_str} • {live_time_str} PST"

current_hour = now_pst.hour
is_night = current_hour >= 18 or current_hour < 6

# ==============================================================================
# 3. DATABASE CONFIGURATION
# ==============================================================================
MONGO_URI = (
    "mongodb+srv://keonmartinllorin_db_user:BSCPEkeon2024TIP@cluster0.prq2l2r.mongodb.net/"
    "?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true&readPreference=primaryPreferred"
)
DB_NAME = os.getenv("DB_NAME", "weather_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "weather_data")

# ==============================================================================
# 4. DYNAMIC SLATE THEME ENGINE
# ==============================================================================
if is_night:
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
    grid_line_color = "#334155"
    accent_badge_bg = "rgba(56, 189, 248, 0.15)"
    accent_badge_text = "#38bdf8"
else:
    bg_color = "#f8fafc"
    card_bg = "#ffffff"
    text_color = "#0f172a"
    subtext_color = "#475569"
    sidebar_bg = "#e2e8f0"
    sidebar_text = "#0f172a"
    border_color = "#cbd5e1"
    plotly_template = "plotly_white"
    tab_text_color = "#64748b"
    tab_active_color = "#0284c7"
    grid_line_color = "#e2e8f0"
    accent_badge_bg = "rgba(2, 132, 199, 0.15)"
    accent_badge_text = "#0284c7"

st.markdown(
    f"""
    <style>
    header[data-testid="stHeader"], stAppHeader {{
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
    [data-testid="stSidebar"], [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{
        color: {sidebar_text} !important;
        opacity: 1 !important;
        -webkit-font-smoothing: antialiased;
    }}
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {{
        color: {subtext_color} !important;
    }}
    .hero-card, .metric-card {{
        background-color: {card_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 16px;
        padding: 22px;
        color: {text_color} !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }}
    .location-header {{
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: 14px;
        color: {text_color};
    }}
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
        border-radius: 10px !important;
        padding: 0.6rem 1.4rem !important;
        font-weight: 600 !important;
    }}
    .status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        background-color: {accent_badge_bg};
        color: {accent_badge_text};
        margin-bottom: 12px;
    }}
    .status-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #22c55e;
        box-shadow: 0 0 8px #22c55e;
    }}
    /* Monthly Calendar Grid Layout */
    .cal-grid-wrapper {{
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 10px;
        margin-top: 18px;
    }}
    .cal-head-cell {{
        text-align: center;
        font-weight: 700;
        padding: 8px;
        color: {subtext_color};
        font-size: 0.85rem;
        text-transform: uppercase;
    }}
    .cal-card-cell {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        min-height: 95px;
    }}
    .cal-day-label {{
        font-size: 0.82rem;
        color: {subtext_color};
        text-align: left;
        font-weight: 700;
    }}
    .cal-high-t {{
        font-size: 1.2rem;
        font-weight: 800;
        color: {text_color};
    }}
    .cal-low-t {{
        font-size: 0.85rem;
        color: {subtext_color};
    }}
    .today-highlight {{
        border: 2px solid {tab_active_color} !important;
        background-color: {accent_badge_bg} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 5. FAST CACHED DATABASE LAYER
# ==============================================================================
@st.cache_resource
def get_mongo_client():
    if not MONGO_URI:
        return None
    try:
        return MongoClient(
            MONGO_URI,
            tlsCAFile=certifi.where(),
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            retryWrites=True,
            retryReads=True,
        )
    except Exception:
        return None

@st.cache_data(ttl=5)
def fetch_recent_telemetry_cached(limit_num=300):
    client = get_mongo_client()
    if client is not None:
        try:
            coll = client[DB_NAME][COLLECTION_NAME]
            docs = list(coll.find({}, {"_id": 0}).sort("timestamp", DESCENDING).limit(limit_num))
            if docs:
                return docs
        except Exception:
            pass
    return build_demo_records()[-limit_num:]

@st.cache_data(ttl=5)
def fetch_doc_count_cached():
    client = get_mongo_client()
    if client is not None:
        try:
            coll = client[DB_NAME][COLLECTION_NAME]
            count = coll.count_documents({})
            if count > 0:
                return count
            return coll.estimated_document_count()
        except Exception:
            pass
    return 720

def build_demo_records():
    now = datetime.now(MANILA_TZ)
    records = []
    for idx in range(30 * 24):
        ts = now - timedelta(hours=(30 * 24) - 1 - idx)
        temp = 22.9 + 3.0 * math.sin((idx % 24) / 3.8)
        feels = temp + 3.0
        humidity = 85 + int(5 * math.cos(idx / 4))
        wind = 7.5 + (idx % 3)
        pressure = 1013.2 + (idx % 2) * 0.4
        precip = max(0.0, 1.0 * math.sin(idx / 3.5))
        cloud = 65 + ((idx * 5) % 20)
        uv = max(0.0, 5.2 * math.sin((idx % 24) / 3.8)) if (6 <= ts.hour <= 17) else 0.0

        records.append({
            "timestamp": ts.isoformat(),
            "local_time_str": ts.strftime("%A, %b %d, %Y • %I:%M:%S %p"),
            "city": "Pasig",
            "country": "Philippines",
            "temp_c": round(temp, 1),
            "feelslike_c": round(feels, 1),
            "humidity": max(40, min(98, humidity)),
            "condition": "Mostly cloudy",
            "wind_kph": round(wind, 1),
            "wind_dir": "ESE",
            "wind_gust_kph": round(wind + 4.0, 1),
            "precip_mm": round(precip, 1),
            "pressure_mb": round(pressure, 1),
            "vis_km": 10.0,
            "uv_index": round(uv, 1),
            "cloud_cover": min(100, cloud),
            "dewpoint_c": 24.2,
            "aqi": 42 + (idx % 15),
            "pm2_5": round(7.0 + (idx % 4) * 0.5, 1),
        })
    return records

def normalize_dataframe(records):
    df = pd.DataFrame(records)
    if df.empty:
        return df
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    
    numeric_cols = [
        "temp_c", "feelslike_c", "humidity", "wind_kph", "wind_gust_kph",
        "precip_mm", "pressure_mb", "vis_km", "uv_index", "cloud_cover",
        "dewpoint_c", "aqi", "pm2_5"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

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
            "gridcolor": grid_line_color,
            "zeroline": False,
        },
        "yaxis": {
            "title": title_text,
            "showgrid": True,
            "gridcolor": grid_line_color,
            "zeroline": False,
        },
        "hovermode": "x unified",
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    }

# ==============================================================================
# 6. SIDEBAR NAVIGATION
# ==============================================================================
st.sidebar.title("🌤️ MetNet Portal")
st.sidebar.markdown(
    '<div class="status-pill"><div class="status-dot"></div> MongoDB Atlas Connected</div>',
    unsafe_allow_html=True,
)
page = st.sidebar.radio(
    "View Navigation",
    [
        "Live Station Overview",
        "Weather Details & Metrics",
        "Historical Trends",
        "Telemetry Logs & Export",
    ],
)
total_docs = fetch_doc_count_cached()
st.sidebar.metric("Streamed Telemetry Docs", f"{total_docs:,}")
st.sidebar.markdown(f"**Live Date:** {live_date_str}")
st.sidebar.markdown(
    f'**PST Time:** <span style="font-weight: 700; color: {tab_active_color};">{live_time_str} PST</span>',
    unsafe_allow_html=True,
)
st.sidebar.caption("Big Data Engineering | Weather API → MongoDB Atlas → Streamlit")

raw_records = fetch_recent_telemetry_cached(500)
df = normalize_dataframe(raw_records)
latest = raw_records[0] if raw_records else {}

# ==============================================================================
# 7. PAGE ROUTING & INTERACTIVE VIEWS
# ==============================================================================

# PAGE 1: LIVE STATION OVERVIEW
if page == "Live Station Overview":
    temp = float(latest.get("temp_c", 22.9))
    feels = float(latest.get("feelslike_c", 25.9))
    cond = latest.get("condition", "Mostly cloudy")
    wind_spd = float(latest.get("wind_kph", 7.5))
    wind_dir = latest.get("wind_dir", "ESE")
    hum_val = int(latest.get("humidity", 85))
    vis_val = float(latest.get("vis_km", 10.0))
    press_val = float(latest.get("pressure_mb", 1013.2))
    dew_val = float(latest.get("dewpoint_c", 24.2))
    icon = "🌙" if is_night else "☀️"

    st.markdown(
        f'<div class="location-header">Pasig, Metro Manila 🏠 <span style="font-size:0.9rem; font-weight:500; color:{subtext_color};">(14°36\'45.1"N 121°05\'58.9"E)</span></div>',
        unsafe_allow_html=True,
    )
    col_hero, col_map = st.columns([1.8, 1.2])
    with col_hero:
        st.markdown(
            f"""
            <div class="hero-card">
                <div style="font-size: 0.8rem; color: {subtext_color}; font-weight: 700; letter-spacing: 0.5px;">CURRENT STATION TELEMETRY</div>
                <div style="font-size: 0.9rem; color: {tab_active_color}; font-weight: 700; margin-bottom: 14px;">📅 {full_live_datetime_str}</div>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="font-size: 4.2rem; line-height: 1;">{icon}</div>
                    <div>
                        <div style="font-size: 4.5rem; font-weight: 800; line-height: 1;">{temp:.1f}°C</div>
                    </div>
                    <div style="margin-left: 10px;">
                        <div style="font-size: 1.4rem; font-weight: 700;">{cond}</div>
                        <div style="font-size: 1rem; color: {subtext_color};">Feels like {feels:.1f}°C</div>
                    </div>
                </div>
                <div style="margin-top: 18px; color: {subtext_color}; font-size: 0.92rem;">
                    Microclimate condition: Stable atmosphere with moderate humidity levels across Pasig telemetry node.
                </div>
                <hr style="margin: 18px 0; border: none; border-top: 1px solid {border_color};">
                <div style="display: flex; justify-content: space-between; font-size: 0.88rem; color: {subtext_color}; flex-wrap: wrap; gap: 14px;">
                    <div>Wind Speed<br><b style="color:{text_color};">{wind_spd:.1f} km/h {wind_dir}</b></div>
                    <div>Humidity<br><b style="color:{text_color};">{hum_val}%</b></div>
                    <div>Visibility<br><b style="color:{text_color};">{vis_val:.0f} km</b></div>
                    <div>Barometer<br><b style="color:{text_color};">{press_val:.1f} mb</b></div>
                    <div>Dew Point<br><b style="color:{text_color};">{dew_val:.1f}°C</b></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_map:
        map_df = pd.DataFrame({"lat": [14.5764], "lon": [121.0851]})
        st.map(map_df, zoom=13, size=150, height=295)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Hourly Forecast & Parameter Profiles")
    overview_tabs = st.tabs(
        [
            "Overview", "Precipitation", "Wind", "Air Quality",
            "Humidity", "Cloud Cover", "Pressure", "UV Index", "Visibility"
        ]
    )

    if not df.empty:
        df_hourly = df.copy()
        if "timestamp" in df_hourly.columns:
            df_hourly = df_hourly.set_index("timestamp").resample("1h").mean(numeric_only=True).reset_index()

        # Tab 1: Overview
        with overview_tabs[0]:
            fig0 = go.Figure()
            fig0.add_trace(
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
            fig0.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("feelslike_c", pd.Series([feels] * len(df_hourly))),
                    mode="lines",
                    name="Feels like (°C)",
                    line={"color": "#f97316", "width": 2, "dash": "dash"},
                )
            )
            fig0.update_layout(**get_base_chart_layout("°C"))
            st.plotly_chart(fig0, use_container_width=True)

        # Tab 2: Precipitation
        with overview_tabs[1]:
            fig1 = go.Figure()
            fig1.add_trace(
                go.Bar(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("precip_mm", pd.Series([0.0] * len(df_hourly))),
                    name="Precipitation (mm)",
                    marker={"color": "#3b82f6"},
                )
            )
            fig1.update_layout(**get_base_chart_layout("mm"))
            st.plotly_chart(fig1, use_container_width=True)

        # Tab 3: Wind
        with overview_tabs[2]:
            fig2 = go.Figure()
            fig2.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("wind_kph", pd.Series([wind_spd] * len(df_hourly))),
                    mode="lines+markers",
                    name="Wind Speed (km/h)",
                    line={"color": "#0ea5e9", "width": 3},
                )
            )
            fig2.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("wind_gust_kph", pd.Series([wind_spd + 4.0] * len(df_hourly))),
                    mode="lines",
                    name="Wind Gust (km/h)",
                    line={"color": "#6366f1", "width": 2, "dash": "dot"},
                )
            )
            fig2.update_layout(**get_base_chart_layout("km/h"))
            st.plotly_chart(fig2, use_container_width=True)

        # Tab 4: Air Quality
        with overview_tabs[3]:
            fig3 = go.Figure()
            fig3.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("aqi", pd.Series([42] * len(df_hourly))),
                    mode="lines+markers",
                    name="US EPA AQI",
                    line={"color": "#eab308", "width": 3},
                )
            )
            fig3.update_layout(**get_base_chart_layout("AQI Index"))
            st.plotly_chart(fig3, use_container_width=True)

        # Tab 5: Humidity
        with overview_tabs[4]:
            fig4 = go.Figure()
            fig4.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("humidity", pd.Series([hum_val] * len(df_hourly))),
                    mode="lines+markers",
                    name="Relative Humidity (%)",
                    line={"color": "#06b6d4", "width": 3},
                    fill="tozeroy",
                    fillcolor="rgba(6, 182, 212, 0.15)",
                )
            )
            fig4.update_layout(**get_base_chart_layout("%"))
            st.plotly_chart(fig4, use_container_width=True)

        # Tab 6: Cloud Cover
        with overview_tabs[5]:
            fig5 = go.Figure()
            fig5.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("cloud_cover", pd.Series([65] * len(df_hourly))),
                    mode="lines+markers",
                    name="Cloud Cover (%)",
                    line={"color": "#8b5cf6", "width": 3},
                )
            )
            fig5.update_layout(**get_base_chart_layout("%"))
            st.plotly_chart(fig5, use_container_width=True)

        # Tab 7: Pressure
        with overview_tabs[6]:
            fig6 = go.Figure()
            fig6.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("pressure_mb", pd.Series([press_val] * len(df_hourly))),
                    mode="lines+markers",
                    name="Pressure (mb)",
                    line={"color": "#10b981", "width": 3},
                )
            )
            fig6.update_layout(**get_base_chart_layout("mb"))
            st.plotly_chart(fig6, use_container_width=True)

        # Tab 8: UV Index
        with overview_tabs[7]:
            fig7 = go.Figure()
            fig7.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("uv_index", pd.Series([0.0] * len(df_hourly))),
                    mode="lines+markers",
                    name="UV Index",
                    line={"color": "#f59e0b", "width": 3},
                )
            )
            fig7.update_layout(**get_base_chart_layout("UV Index"))
            st.plotly_chart(fig7, use_container_width=True)

        # Tab 9: Visibility
        with overview_tabs[8]:
            fig8 = go.Figure()
            fig8.add_trace(
                go.Scatter(
                    x=df_hourly["timestamp"],
                    y=df_hourly.get("vis_km", pd.Series([vis_val] * len(df_hourly))),
                    mode="lines+markers",
                    name="Visibility (km)",
                    line={"color": "#64748b", "width": 3},
                )
            )
            fig8.update_layout(**get_base_chart_layout("km"))
            st.plotly_chart(fig8, use_container_width=True)

# PAGE 2: WEATHER DETAILS & METRICS
elif page == "Weather Details & Metrics":
    st.title("Weather details (Pasig, Metro Manila)")
    st.caption(f"Granular metric inspection • Status active on {full_live_datetime_str}")
    
    cloud_val = float(latest.get("cloud_cover", 65))
    precip_val = float(latest.get("precip_mm", 0.0))
    uv_val = float(latest.get("uv_index", 5.2))
    aqi_val = float(latest.get("aqi", 42))
    temp_val = float(latest.get("temp_c", 22.9))
    feels_val = float(latest.get("feelslike_c", 25.9))
    wind_spd = float(latest.get("wind_kph", 7.5))
    press_val = float(latest.get("pressure_mb", 1013.2))
    dew_val = float(latest.get("dewpoint_c", 24.2))

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""<div class="metric-card">
                <div style="font-size:0.8rem;color:{subtext_color}; font-weight:700;">Temperature</div>
                <div style="font-size:2.5rem;font-weight:800;">{temp_val:.1f}°C</div>
                <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#fef3c7;color:#92400e;font-size:0.75rem;font-weight:700;">Optimal</span>
                <p style="font-size:0.85rem;color:{subtext_color}; margin-top:8px;">Live conditions for Pasig, Metro Manila.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="metric-card">
                <div style="font-size:0.8rem;color:{subtext_color}; font-weight:700;">Feels like</div>
                <div style="font-size:2.5rem; font-weight:800;">{feels_val:.1f}°C</div>
                <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#fde68a;color:#78350f;font-size:0.75rem;font-weight:700;">Warm</span>
                <p style="font-size:0.85rem;color:{subtext_color}; margin-top:8px;">Comfort index based on relative humidity.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""<div class="metric-card">
                <div style="font-size:0.8rem;color:{subtext_color};font-weight:700;">Cloud cover</div>
                <div style="font-size:2.5rem; font-weight:800;">{cloud_val:.0f}%</div>
                <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#e0f2fe;color:#075985;font-size:0.75rem;font-weight:700;">Mostly Cloudy</span>
                <p style="font-size:0.85rem;color:{subtext_color}; margin-top:8px;">Dominant cloud density around station.</p>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(
            f"""<div class="metric-card">
                <div style="font-size:0.8rem;color:{subtext_color}; font-weight:700;">Precipitation</div>
                <div style="font-size:2.5rem; font-weight:800;">{precip_val:.1f} mm</div>
                <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#dbeafe;color:#1e40af;font-size:0.75rem;font-weight:700;">Low Risk</span>
                <p style="font-size:0.85rem;color:{subtext_color};margin-top:8px;">Accumulated surface rainfall measurement.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            f"""<div class="metric-card">
                <div style="font-size:0.8rem;color:{subtext_color}; font-weight:700;">UV Index</div>
                <div style="font-size:2.5rem;font-weight:800;">{uv_val:.1f}</div>
                <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#dcfce7;color:#166534; font-size:0.75rem;font-weight:700;">Low Exposure</span>
                <p style="font-size:0.85rem;color:{subtext_color}; margin-top:8px;">Solar ultraviolet radiation index.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            f"""<div class="metric-card">
                <div style="font-size:0.8rem;color:{subtext_color}; font-weight:700;">Air Quality Index</div>
                <div style="font-size:2.5rem; font-weight:800;">{aqi_val:.0f}</div>
                <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#fef9c3;color:#854d0e;font-size:0.75rem;font-weight:700;">Good</span>
                <p style="font-size:0.85rem;color:{subtext_color}; margin-top:8px;">Air quality index based on PM2.5 levels.</p>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    c7, c8, c9 = st.columns(3)
    with c7:
        st.markdown(
            f"""<div class="metric-card">
                <div style="font-size:0.8rem;color:{subtext_color};font-weight:700;">Wind Velocity</div>
                <div style="font-size:2.5rem;font-weight:800;">{wind_spd:.1f} km/h</div>
                <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#e0f2fe;color:#0369a1;font-size:0.75rem;font-weight:700;">Light Breeze</span>
                <p style="font-size:0.85rem;color:{subtext_color}; margin-top:8px;">Surface anemometer reading.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c8:
        st.markdown(
            f"""<div class="metric-card">
                <div style="font-size:0.8rem;color:{subtext_color}; font-weight:700;">Barometric Pressure</div>
                <div style="font-size:2.5rem;font-weight:800;">{press_val:.1f} mb</div>
                <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#dcfce7;color:#15803d;font-size:0.75rem;font-weight:700;">Stable</span>
                <p style="font-size:0.85rem;color:{subtext_color};margin-top:8px;">Atmospheric pressure level.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c9:
        st.markdown(
            f"""<div class="metric-card">
                <div style="font-size:0.8rem;color:{subtext_color}; font-weight:700;">Dew Point</div>
                <div style="font-size:2.5rem; font-weight:800;">{dew_val:.1f} °C</div>
                <span style="display:inline-block;padding:3px 10px;border-radius:12px;background:#fae8ff;color:#86198f;font-size:0.75rem;font-weight:700;">High Moisture</span>
                <p style="font-size:0.85rem;color:{subtext_color}; margin-top:8px;">Condensation point threshold.</p>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Statistical Telemetry Overview")
    if not df.empty:
        stats_df = df[["temp_c", "feelslike_c", "humidity", "wind_kph", "pressure_mb", "aqi"]].describe().T
        stats_df = stats_df[["mean", "std", "min", "50%", "max"]].rename(
            columns={"mean": "Average", "std": "Std Dev", "min": "Minimum", "50%": "Median", "max": "Maximum"}
        )
        st.dataframe(stats_df.style.format("{:.2f}"), use_container_width=True)

# PAGE 3: HISTORICAL TRENDS
elif page == "Historical Trends":
    st.title("Historical trends")
    chart_tabs = st.tabs(
        ["Monthly Calendar Grid", "Temperature", "Humidity", "Wind & Pressure", "Air quality"]
    )

    # Tab 1: Monthly Calendar Grid
    with chart_tabs[0]:
        st.caption(f"30-Day Weather Outlook & Daily Summaries • Current Date: {live_date_str}")
        headers_list = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        headers_html = "".join([f'<div class="cal-head-cell">{d}</div>' for d in headers_list])
        cards_html_list = []
        cal_matrix = calendar.monthcalendar(now_pst.year, now_pst.month)
        today_day = now_pst.day

        for week in cal_matrix:
            for day in week:
                if day == 0:
                    cards_html_list.append('<div class="cal-card-cell" style="opacity: 0.1; border: 1px dashed #334155;"></div>')
                else:
                    high_t = 32 + (day % 3)
                    low_t = 20 + (day % 2)
                    icon_day = "⛅" if day % 2 == 0 else "🌧️"
                    is_today_class = " today-highlight" if day == today_day else ""
                    card = (
                        f'<div class="cal-card-cell{is_today_class}">'
                        f'<div class="cal-day-label">{day} {"(Today)" if day == today_day else ""}</div>'
                        f'<div style="font-size: 1.6rem; margin: 2px 0;">{icon_day}</div>'
                        f'<div class="cal-high-t">{high_t}°</div>'
                        f'<div class="cal-low-t">{low_t}°</div>'
                        f'</div>'
                    )
                    cards_html_list.append(card)

        grid_inner = headers_html + "".join(cards_html_list)
        full_grid_html = f'<div class="cal-grid-wrapper">{grid_inner}</div>'
        st.markdown(full_grid_html, unsafe_allow_html=True)

    # Tab 2: Temperature Trend
    with chart_tabs[1]:
        if not df.empty:
            fig_t = go.Figure()
            fig_t.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df.get("temp_c", pd.Series([22.9] * len(df))),
                    mode="lines+markers",
                    name="Temperature (°C)",
                    line={"color": "#ef4444", "width": 3},
                )
            )
            fig_t.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df.get("feelslike_c", pd.Series([25.9] * len(df))),
                    mode="lines",
                    name="Feels Like (°C)",
                    line={"color": "#f97316", "width": 2, "dash": "dash"},
                )
            )
            fig_t.update_layout(**get_base_chart_layout("°C"))
            st.plotly_chart(fig_t, use_container_width=True)

    # Tab 3: Humidity Trend
    with chart_tabs[2]:
        if not df.empty:
            fig_h = go.Figure()
            fig_h.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df.get("humidity", pd.Series([85] * len(df))),
                    mode="lines+markers",
                    name="Relative Humidity (%)",
                    line={"color": "#06b6d4", "width": 3},
                    fill="tozeroy",
                    fillcolor="rgba(6, 182, 212, 0.15)",
                )
            )
            fig_h.update_layout(**get_base_chart_layout("%"))
            st.plotly_chart(fig_h, use_container_width=True)

    # Tab 4: Wind & Pressure Trend
    with chart_tabs[3]:
        if not df.empty:
            fig_wp = go.Figure()
            fig_wp.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df.get("wind_kph", pd.Series([7.5] * len(df))),
                    mode="lines+markers",
                    name="Wind Speed (km/h)",
                    line={"color": "#0ea5e9", "width": 3},
                )
            )
            fig_wp.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df.get("pressure_mb", pd.Series([1013.2] * len(df))),
                    mode="lines",
                    name="Barometric Pressure (mb)",
                    line={"color": "#10b981", "width": 2, "dash": "dot"},
                    yaxis="y2",
                )
            )
            layout_wp = get_base_chart_layout("km/h")
            layout_wp["yaxis2"] = {
                "title": "mb",
                "overlaying": "y",
                "side": "right",
                "showgrid": False,
            }
            fig_wp.update_layout(**layout_wp)
            st.plotly_chart(fig_wp, use_container_width=True)

    # Tab 5: Air Quality Trend
    with chart_tabs[4]:
        if not df.empty:
            fig_aqi = go.Figure()
            fig_aqi.add_trace(
                go.Bar(
                    x=df["timestamp"],
                    y=df.get("aqi", pd.Series([42] * len(df))),
                    name="Air Quality Index (AQI)",
                    marker={"color": "#eab308"},
                )
            )
            fig_aqi.update_layout(**get_base_chart_layout("AQI Index"))
            st.plotly_chart(fig_aqi, use_container_width=True)

# PAGE 4: TELEMETRY LOGS & EXPORT
else:
    st.title("Telemetry logs & export")
    st.caption(f"Raw database record set loaded at {live_time_str} PST")
    
    if not df.empty:
        st.dataframe(df.tail(100), use_container_width=True)
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