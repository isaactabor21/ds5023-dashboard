"""
Weather Radar Tab
=================
Live radar via RainViewer API (no key required).
Milestone 3: added full error handling, caching with TTL comment, input validation,
st.spinner, st.error/warning feedback patterns.
"""

import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from navigation import start_view_transition


@st.cache_data(ttl=600)  # Cache 10 minutes: radar frames update every 10 min on RainViewer,
                          # so re-fetching more often wastes requests without new data.
def get_radar_data():
    """
    Fetch available radar frame paths from RainViewer.
    Handles: network timeout, connection error, bad JSON, empty frame list.
    """
    try:
        response = requests.get(
            "https://api.rainviewer.com/public/weather-maps.json",
            timeout=8,
        )

        if response.status_code == 429:
            st.warning("⏱️ Radar API limit reached. Please wait a minute and try again.")
            return None

        if response.status_code == 500:
            st.error("🛠️ Radar service is temporarily unavailable. Please try again later.")
            return None

        if response.status_code != 200:
            st.error(f"❌ Could not load radar data (HTTP {response.status_code}).")
            return None

        data = response.json()

        # Validate response structure
        if "radar" not in data or "past" not in data.get("radar", {}):
            st.error("⚠️ Radar data format was unexpected. Please try again later.")
            return None

        if not data["radar"]["past"]:
            st.warning("📭 No radar frames available right now. Try again shortly.")
            return None

        return data

    except requests.exceptions.Timeout:
        st.error("🌐 Could not connect to radar service. Check your internet connection.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🌐 Could not connect to radar service. Check your internet connection.")
        return None
    except ValueError:
        st.error("⚠️ Received an unexpected response from the radar service.")
        return None


def render():
    st.subheader("🌤️ Live Weather Radar")
    st.caption("Radar data from RainViewer · Updates every 10 minutes")

    can_view_results = st.session_state.get("search_completed", False)
    can_view_risk = st.session_state.get("selected_flight") is not None

    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1.15, 1.2, 1.35, 2.8])
    with nav_col1:
        if st.button("Back to Home", key="weather_back_home", use_container_width=True):
            start_view_transition(
                "home",
                "Returning you to the search page...",
                action="reset_search_state",
            )
    with nav_col2:
        if st.button(
            "Flight Results",
            key="weather_to_results",
            use_container_width=True,
            disabled=not can_view_results,
        ):
            start_view_transition("results", "Returning to your flight options...")
    with nav_col3:
        if st.button(
            "Risk Analysis",
            key="weather_to_risk",
            use_container_width=True,
            disabled=not can_view_risk,
        ):
            start_view_transition("risk", "Returning to your risk breakdown...")
    with nav_col4:
        if can_view_results and can_view_risk:
            st.caption("Switch between radar, results, and risk analysis without losing your current trip.")
        elif can_view_results:
            st.caption("Flight Results is available. Risk Analysis unlocks after you select a flight.")
        else:
            st.caption("Start with a search to unlock Flight Results and Risk Analysis.")

    with st.spinner("📡 Loading radar data..."):
        data = get_radar_data()

    # Validation: stop gracefully if data unavailable
    if data is None:
        st.info("Radar is temporarily unavailable. The rest of Air Aware still works normally.")
        st.stop()

    host        = data["host"]
    past_frames = data["radar"]["past"]

    st.success(f"✅ Loaded {len(past_frames)} radar frames")

    # Frame slider with key=
    frame_idx = st.slider(
        "⏱️ Scrub through past 2 hours of radar",
        min_value=0,
        max_value=len(past_frames) - 1,
        value=len(past_frames) - 1,
        key="radar_frame_slider",  # key= lets us reset this widget externally if needed
        help="Slide left to see earlier radar, right for most recent",
    )

    selected_path = past_frames[frame_idx]["path"]
    radar_url = f"{host}{selected_path}/256/{{z}}/{{x}}/{{y}}/2/1_1.png"

    # Build map centered on mid-US
    m = folium.Map(location=[38.0336, -78.5080], zoom_start=5)
    folium.TileLayer(
        tiles=radar_url,
        attr="RainViewer.com",
        name="Live Radar",
        overlay=True,
        opacity=0.65,
    ).add_to(m)

    st_folium(m, width=None, height=500, key="radar_map")  # key= prevents folium widget
                                                             # duplication when tab re-renders
