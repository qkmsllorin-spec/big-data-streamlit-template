# 🚀 Streaming Data Dashboard: Project Guide

This project requires building a big data streaming dashboard using **Kafka** and **Streamlit**, featuring separate real-time and historical data views.

## 🎯 Architecture & Components

A **dual-pipeline** architecture separates live streaming from long-term storage and analysis.

| Pipeline | Flow | Output |
| :--- | :--- | :--- |
| **Real-time** | Kafka $\rightarrow$ Streamlit (Live Consumer) | `📈 Real-time Streaming View` |
| **Historical** | Kafka $\rightarrow$ **HDFS OR MongoDB** $\rightarrow$ Streamlit (Query) | `📊 Historical Data View` |

### Mandatory Components
- Kafka Producer/Consumer.
- **HDFS or MongoDB** integration.
- Two-page Streamlit dashboard with charts.
- Robust error handling.

---

## 🗄️ Database Document Schema

The following schema defines the JSON document structure ingested by `producer.py` and stored inside MongoDB Atlas (`weather_db.weather_data` collection):

```json
{
  "_id": {"\$oid": "672322a1b9f8a8470c123456"},
  "timestamp": "2026-10-31T14:54:12+08:00",
  "local_time_str": "Saturday, Oct 31, 2026 • 02:54:12 PM",
  "metric_type": "Temperature_C",
  "value": 31.2,
  "sensor_id": "sensor_pasig_01",
  "city": "Pasig",
  "country": "Philippines",
  "temp_c": 31.2,
  "feelslike_c": 35.4,
  "humidity": 60,
  "condition": "Patchy rain nearby",
  "wind_kph": 9.7,
  "wind_degree": 87,
  "wind_dir": "E",
  "wind_gust_kph": 23.0,
  "precip_mm": 0.0,
  "pressure_mb": 1012.0,
  "vis_km": 10.0,
  "uv_index": 6.0,
  "cloud_cover": 98,
  "dewpoint_c": 23.0,
  "aqi": 25,
  "pm2_5": 3.5
}