"""
data.py
=======
Shared flight data, AviationStack API integration, and helper functions.
API: AviationStack  |  Base URL: http://api.aviationstack.com/v1
Auth: API key via st.secrets["AVIATIONSTACK_KEY"]  |  Rate limit: 100 req/month (free)
Value for persona: Provides real-time flight status and delay info so users
see actual conditions, not just historical estimates.
"""

import streamlit as st
import requests

# =============================================================================
# FALLBACK MOCK DATA
# =============================================================================

flights_data = [
    {"id": 1, "airline": "United", "flight_num": "441", "origin": "MSP", "destination": "DCA",
     "departure": "9:15 AM", "arrival": "12:20 PM", "duration": "3h 05m", "stops": "Nonstop",
     "on_time_prob": 91, "price": 342, "risk_factors": ["Clear weather expected"], "status": "Scheduled"},
    {"id": 2, "airline": "American", "flight_num": "882", "origin": "MSP", "destination": "DCA",
     "departure": "2:30 PM", "arrival": "5:28 PM", "duration": "2h 58m", "stops": "Nonstop",
     "on_time_prob": 32, "price": 298, "risk_factors": ["Winter storm warning", "Historical delays"], "status": "Delayed"},
    {"id": 3, "airline": "Delta", "flight_num": "1205", "origin": "MSP", "destination": "DCA",
     "departure": "6:45 AM", "arrival": "9:50 AM", "duration": "3h 05m", "stops": "Nonstop",
     "on_time_prob": 78, "price": 315, "risk_factors": ["Minor wind advisory"], "status": "Scheduled"},
    {"id": 4, "airline": "Southwest", "flight_num": "2341", "origin": "MSP", "destination": "DCA",
     "departure": "11:20 AM", "arrival": "2:35 PM", "duration": "3h 15m", "stops": "Nonstop",
     "on_time_prob": 45, "price": 276, "risk_factors": ["Aircraft arriving from delayed route"], "status": "Scheduled"},
    {"id": 5, "airline": "United", "flight_num": "892", "origin": "MSP", "destination": "DCA",
     "departure": "4:10 PM", "arrival": "7:15 PM", "duration": "3h 05m", "stops": "Nonstop",
     "on_time_prob": 94, "price": 389, "risk_factors": ["Clear conditions"], "status": "Scheduled"},
]

# Airlines available per origin airport — drives dependent dropdown in home.py
AIRLINES_BY_ORIGIN = {
    "MSP": ["United", "Delta", "American", "Southwest", "Spirit"],
    "DCA": ["United", "American", "Delta", "Southwest", "JetBlue"],
    "ORD": ["United", "American", "Delta", "Spirit", "Frontier"],
    "ATL": ["Delta", "United", "American", "Southwest", "Spirit"],
    "LAX": ["United", "Delta", "American", "Southwest", "Alaska", "JetBlue"],
    "JFK": ["Delta", "American", "JetBlue", "United", "Spirit"],
    "BOS": ["JetBlue", "Delta", "American", "United", "Southwest"],
    "MIA": ["American", "Delta", "United", "Spirit", "JetBlue"],
}

ALL_AIRPORTS = sorted(AIRLINES_BY_ORIGIN.keys())


# =============================================================================
# AVIATIONSTACK API
# =============================================================================

@st.cache_data(ttl=300)  # Cache 5 min: free tier is 100 req/month so we cache
                          # aggressively to avoid burning quota on repeated searches.
def fetch_live_flights(origin: str, destination: str):
    """
    Fetch live flight data from AviationStack free tier.
    Free tier limitation: arr_iata (destination filter) is a paid-only parameter.
    Workaround: fetch by dep_iata only (up to 100 results), then filter
    client-side by destination so the user still gets route-specific results.
    Returns: list of flight dicts | empty list if no results | None on error.
    Handles: 401, 404, 429, 500, timeout, connection error, empty results.
    """
    try:
        api_key = st.secrets["AVIATIONSTACK_KEY"]
    except (KeyError, FileNotFoundError):
        return None  # No key — caller falls back to mock data

    # NOTE: arr_iata is excluded intentionally — it requires a paid AviationStack plan.
    # We fetch all departures from origin and filter by destination client-side below.
    params = {
        "access_key": api_key,
        "dep_iata": origin.upper().strip(),
        "limit": 100,  # fetch more so client-side destination filter has enough to work with
    }

    try:
        response = requests.get(
            "http://api.aviationstack.com/v1/flights",
            params=params,
            timeout=10
        )

        if response.status_code == 401:
            st.error("🔑 API key is missing or invalid. Please check your secrets configuration.")
            return None

        if response.status_code == 404:
            st.warning("🔍 No results found for your search. Try different airport codes.")
            return []

        if response.status_code == 429:
            st.warning("⏱️ API limit reached. Showing estimated data. Please wait a minute and try again.")
            return None

        if response.status_code == 500:
            st.error("🛠️ The flight data service is temporarily unavailable. Please try again later.")
            return None

        if response.status_code != 200:
            st.error(f"❌ Unexpected error (HTTP {response.status_code}). Please try again.")
            return None

        all_flights = response.json().get("data", [])

        if not all_flights:
            st.warning("📭 No live flights found for this departure airport. Showing estimated data.")
            return []

        # Client-side destination filter (workaround for free tier arr_iata restriction)
        dest = destination.upper().strip()
        flights = [
            f for f in all_flights
            if f.get("arrival", {}).get("iata", "").upper() == dest
        ]

        if not flights:
            st.warning(f"📭 No flights found from {origin.upper()} to {dest} in live data. Showing estimated data.")
            return []

        # Parse API response into app-friendly dicts
        parsed = []
        for i, f in enumerate(flights):
            dep = f.get("departure", {})
            arr = f.get("arrival", {})
            delay_min = dep.get("delay") or 0

            if delay_min == 0:
                prob = 88
            elif delay_min < 15:
                prob = 72
            elif delay_min < 45:
                prob = 45
            else:
                prob = 22

            parsed.append({
                "id": i + 1,
                "airline": f.get("airline", {}).get("name", "Unknown"),
                "flight_num": f.get("flight", {}).get("iata", f"FL{i+1}"),
                "origin": dep.get("iata", origin),
                "destination": arr.get("iata", destination),
                "departure": dep.get("scheduled", "N/A"),
                "arrival": arr.get("scheduled", "N/A"),
                "duration": "N/A",
                "stops": "Nonstop",
                "on_time_prob": prob,
                "price": 0,
                "risk_factors": [f"Delay: {delay_min} min"] if delay_min else ["On schedule"],
                "status": f.get("flight_status", "Scheduled").capitalize(),
            })

        return parsed

    except requests.exceptions.Timeout:
        st.error("🌐 Could not connect. Check your internet connection.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🌐 Could not connect. Check your internet connection.")
        return None
    except ValueError:
        st.error("⚠️ Received an unexpected response from the flight data service.")
        return None


# =============================================================================
# HELPERS
# =============================================================================

def get_probability_color(prob: int):
    """Return (hex_color, emoji) based on on-time probability."""
    if prob >= 67:
        return "#28a745", "🟢"
    elif prob >= 33:
        return "#ffc107", "🟡"
    else:
        return "#dc3545", "🔴"


def get_airlines_for_origin(origin: str):
    """Return airlines that serve a given origin — used for dependent dropdown."""
    return AIRLINES_BY_ORIGIN.get(origin.upper(), ["United", "Delta", "American", "Southwest"])


# =============================================================================
# OPENWEATHERMAP API
# =============================================================================
# API: OpenWeatherMap — Current Weather + 5-Day Forecast
# Base URLs:
#   Current:  https://api.openweathermap.org/data/2.5/weather
#   Forecast: https://api.openweathermap.org/data/2.5/forecast
# Auth: API key via st.secrets["OPENWEATHER_KEY"]
# Rate limit: 1,000 calls/day free — no credit card required
# Value for persona: shows weather forecasted for the ACTUAL departure date/time
# (up to 5 days out), so the risk score reflects what conditions will be like
# when the user travels — not just what the weather is right now.
# Beyond 5 days: falls back gracefully with a clear explanation.

# IATA airport code → (lat, lon) for OpenWeatherMap geo lookup
AIRPORT_COORDS = {
    "MSP": (44.8848, -93.2223),
    "DCA": (38.8521, -77.0377),
    "ORD": (41.9742, -87.9073),
    "ATL": (33.6407, -84.4277),
    "LAX": (33.9425, -118.4081),
    "JFK": (40.6413, -73.7781),
    "BOS": (42.3656, -71.0096),
    "MIA": (25.7959, -80.2870),
    "DEN": (39.8561, -104.6737),
    "SEA": (47.4502, -122.3088),
    "SFO": (37.6213, -122.3790),
    "LAS": (36.0840, -115.1537),
    "PHX": (33.4373, -112.0078),
    "IAH": (29.9902, -95.3368),
    "CLT": (35.2140, -80.9431),
    "EWR": (40.6895, -74.1745),
    "MCO": (28.4312, -81.3081),
    "DTW": (42.2162, -83.3554),
    "PHL": (39.8744, -75.2424),
    "LGA": (40.7772, -73.8726),
}


@st.cache_data(ttl=1800)  # Cache 30 min: forecasts update every 3 hrs on OWM free tier;
                           # 30 min TTL conserves our 1,000 calls/day while staying fresh enough.
def fetch_airport_weather(iata: str, departure_date=None, departure_time_str: str = None):
    """
    Smart weather fetch for an airport:
      - If departure_date is today or None  → current weather endpoint
      - If departure_date is within 5 days  → 5-day/3-hr forecast, picks the
        slot closest to the actual departure time so the score reflects
        forecasted conditions at flight time, not just "today"
      - If departure_date is beyond 5 days  → returns None with an explanatory
        message; caller shows a "forecast not yet available" fallback card

    Returns a dict with temp, wind, visibility, description, weather_risk_penalty,
    and a `source` field ("current", "forecast", or "unavailable").
    Returns None on any error — caller should use hardcoded fallback.
    """
    from datetime import date, datetime, timedelta

    try:
        api_key = st.secrets["OPENWEATHER_KEY"]
    except (KeyError, FileNotFoundError):
        return None

    coords = AIRPORT_COORDS.get(iata.upper())
    if not coords:
        return None

    lat, lon = coords
    today = date.today()

    # Decide which endpoint to use based on how far out the departure is
    if departure_date is None:
        departure_date = today

    days_out = (departure_date - today).days

    if days_out > 5:
        # Beyond free forecast range — return a sentinel so UI can explain this
        return {"source": "unavailable", "iata": iata.upper(), "days_out": days_out}

    use_forecast = days_out >= 1  # today → current weather; future → forecast

    if use_forecast:
        return _fetch_forecast(iata, lat, lon, api_key, departure_date, departure_time_str)
    else:
        return _fetch_current(iata, lat, lon, api_key)


def _fetch_current(iata, lat, lon, api_key):
    """Fetch current weather from /data/2.5/weather."""
    params = {
        "lat": lat, "lon": lon,
        "appid": api_key,
        "units": "imperial",
    }
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params=params, timeout=8
        )
        if not _check_status(r, "weather"): return None
        data = r.json()
        if not data:
            st.warning(f"📭 No weather data returned for {iata}.")
            return None
        result = _parse_weather_slot(data.get("weather", [{}])[0].get("id", 800),
                                     data.get("weather", [{}])[0].get("description", "clear sky"),
                                     data.get("main", {}).get("temp", 60),
                                     data.get("main", {}).get("feels_like", 60),
                                     data.get("main", {}).get("humidity", 50),
                                     data.get("wind", {}).get("speed", 0),
                                     data.get("visibility", 10000))
        result["iata"]   = iata.upper()
        result["source"] = "current"
        return result
    except requests.exceptions.Timeout:
        st.error("🌐 Could not connect to weather service. Check your internet connection.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🌐 Could not connect to weather service. Check your internet connection.")
        return None
    except ValueError:
        st.error("⚠️ Unexpected response from weather service.")
        return None


@st.cache_data(ttl=10800)  # Cache forecast 3 hrs: OWM forecast updates every 3 hrs,
                            # so there's no benefit re-fetching more often than that.
def _fetch_forecast(iata, lat, lon, api_key, departure_date, departure_time_str):
    """
    Fetch 5-day/3-hr forecast and pick the slot closest to departure time.
    The forecast endpoint returns up to 40 slots (5 days × 8 slots/day).
    We find the slot whose timestamp is nearest to the actual departure datetime,
    so a 6am flight gets early-morning conditions, not afternoon ones.
    """
    from datetime import datetime, time as dtime
    params = {
        "lat": lat, "lon": lon,
        "appid": api_key,
        "units": "imperial",
        "cnt": 40,  # max slots (5 days)
    }
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params=params, timeout=8
        )
        if not _check_status(r, "forecast"): return None

        slots = r.json().get("list", [])
        if not slots:
            st.warning(f"📭 No forecast data available for {iata}.")
            return None

        # Parse departure datetime — combine date with time if provided
        if departure_time_str:
            try:
                # departure_time_str comes in like "9:15 AM"
                dep_time = datetime.strptime(departure_time_str.strip(), "%I:%M %p").time()
            except ValueError:
                dep_time = dtime(12, 0)  # default to noon if parsing fails
        else:
            dep_time = dtime(12, 0)

        target_dt = datetime.combine(departure_date, dep_time)

        # Find the forecast slot with the smallest time difference from target
        best_slot = min(
            slots,
            key=lambda s: abs(datetime.fromtimestamp(s["dt"]) - target_dt)
        )

        result = _parse_weather_slot(
            best_slot.get("weather", [{}])[0].get("id", 800),
            best_slot.get("weather", [{}])[0].get("description", "clear sky"),
            best_slot.get("main", {}).get("temp", 60),
            best_slot.get("main", {}).get("feels_like", 60),
            best_slot.get("main", {}).get("humidity", 50),
            best_slot.get("wind", {}).get("speed", 0),
            best_slot.get("visibility", 10000),
        )
        result["iata"]        = iata.upper()
        result["source"]      = "forecast"
        result["forecast_dt"] = datetime.fromtimestamp(best_slot["dt"]).strftime("%b %d %-I%p")
        return result

    except requests.exceptions.Timeout:
        st.error("🌐 Could not connect to weather service. Check your internet connection.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🌐 Could not connect to weather service. Check your internet connection.")
        return None
    except ValueError:
        st.error("⚠️ Unexpected response from weather service.")
        return None


def _check_status(response, service_name: str) -> bool:
    """Check HTTP status and show appropriate error. Returns True if OK."""
    if response.status_code == 401:
        st.error(f"🔑 Weather API key is missing or invalid.")
        return False
    if response.status_code == 404:
        st.warning(f"🔍 Weather data not found.")
        return False
    if response.status_code == 429:
        st.warning("⏱️ Weather API limit reached. Showing estimated conditions.")
        return False
    if response.status_code == 500:
        st.error("🛠️ Weather service temporarily unavailable.")
        return False
    if response.status_code != 200:
        st.error(f"❌ Weather API error (HTTP {response.status_code}).")
        return False
    return True


def _parse_weather_slot(weather_id, description, temp_f, feels_like, humidity, wind_speed, visibility_m):
    """Parse a weather data slot (current or forecast) into a standard dict."""
    temp_f        = round(temp_f)
    feels_like    = round(feels_like)
    wind_mph      = round(wind_speed)
    visibility_mi = round(visibility_m * 0.000621371, 1)

    if   200 <= weather_id < 300: icon = "⛈️"
    elif 300 <= weather_id < 400: icon = "🌦️"
    elif 500 <= weather_id < 600: icon = "🌧️"
    elif 600 <= weather_id < 700: icon = "❄️"
    elif 700 <= weather_id < 800: icon = "🌫️"
    elif weather_id == 800:       icon = "☀️"
    else:                         icon = "⛅"

    # Risk penalty: 0–30 pts subtracted from on-time probability
    penalty = 0
    if weather_id < 700:                        penalty += 20  # any precipitation
    if 600 <= weather_id < 700:                 penalty += 10  # snow (extra)
    if 200 <= weather_id < 300:                 penalty += 10  # thunderstorm (extra)
    if wind_mph > 30:                           penalty += 10
    elif wind_mph > 20:                         penalty += 5
    if visibility_mi < 1:                       penalty += 10
    elif visibility_mi < 3:                     penalty += 5
    if temp_f < 20:                             penalty += 5   # icing risk

    return {
        "description":          description.title(),
        "icon":                 icon,
        "temp_f":               temp_f,
        "feels_like":           feels_like,
        "humidity":             humidity,
        "wind_mph":             wind_mph,
        "visibility_mi":        visibility_mi,
        "weather_risk_penalty": min(penalty, 30),
    }


def compute_weather_adjusted_prob(base_prob: int, origin_weather, dest_weather) -> int:
    """
    Adjust the base on-time probability using real weather penalties.
    origin_weather and dest_weather are dicts from fetch_airport_weather(),
    or None if weather data is unavailable (base_prob returned unchanged).
    Skips adjustment if source is "unavailable" (beyond 5-day forecast window).
    """
    def valid(w):
        return w is not None and w.get("source") not in (None, "unavailable")

    if not valid(origin_weather) and not valid(dest_weather):
        return base_prob

    origin_penalty = origin_weather["weather_risk_penalty"] if valid(origin_weather) else 0
    dest_penalty   = dest_weather["weather_risk_penalty"]   if valid(dest_weather)   else 0

    # Destination weather weighted more heavily — arrival delays dominate
    total_penalty = origin_penalty * 0.4 + dest_penalty * 0.6
    adjusted = int(base_prob - total_penalty)
    return max(5, min(99, adjusted))  # clamp to 5–99%
