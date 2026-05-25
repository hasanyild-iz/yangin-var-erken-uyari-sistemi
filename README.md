# 🔥 YangınVar! | Satellite-Based Real-Time Wildfire Early Warning System

YangınVar! is an automated, cloud-based microservice designed for early wildfire detection and regional risk mitigation. By scraping thermal anomaly data from NASA's satellites and combining it with localized live meteorological conditions, the system evaluates real-time danger scores and dispatches localized emergency alerts directly to first responders and civil volunteers via Telegram.

## 🚀 Key Features
* **Live Satellite Telemetry:** Ingests active fire hotspots globally within a 24-hour window directly via NASA FIRMS (VIIRS S-NPP satellite sensors).
* **Dynamic Meteorological Enrichment:** Real-time geolocated polling of wind speed, wind direction, and relative humidity utilizing the OpenWeatherMap API.
* **Algorithmic Risk Scoring:** Calculates an automated danger level (LOW, MEDIUM, HIGH) by combining brightness temperature with local atmospheric vulnerability indicators (e.g., high wind speeds or critical humidity drops).
* **Smart Deduplication & Anti-Spam Filter:** Implements an spatial memory system (`.json` cache) with coordinates rounded to a ~1.1km radius, ensuring identical anomalies do not trigger redundant alerts.
* **Cloud-Native Automation:** Fully optimized for lightweight, headless execution as a scheduled cron job (PythonAnywhere/GitHub Actions), operating 24/7 without local machine dependencies.

---

## 🛠️ Tech Stack & Libraries
* **Language:** Python 3.x
* **Data Processing & Analytics:** `pandas`
* **API Integration:** `requests`
* **Configuration & Security:** `python-dotenv` (for secret masking)
* **Visualization (Optional Dashboard):** `streamlit`, `plotly`

---

## 📦 System Architecture & Workflow

1. **Data Ingestion:** The script triggers and pulls the latest CSV telemetry from NASA FIRMS.
2. **Geofencing:** Isolates global thermal points specifically to Turkey's geographic bounding coordinates.
3. **Weather Polling:** Queries real-time meteorological conditions for each validated hotspot.
4. **Deduplication Check:** Checks the localized cache memory to prevent spamming previous alerts.
5. **Alerting:** Formats an emergency dispatch with a Google Maps routing link and broadcasts it to the dedicated Telegram broadcast channel.

---

## 🔧 Setup & Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/yangin-var-erken-uyari.git](https://github.com/YOUR_USERNAME/yangin-var-erken-uyari.git)
cd yangin-var-erken-uyari