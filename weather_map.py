import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# 1. Fetch current radar data (API 2.0 structure)
@st.cache_data(ttl=600)
def get_radar_data():
    # Use the version 2 endpoint
    url = "https://api.rainviewer.com/public/weather-maps.json"
    response = requests.get(url).json()
    return response

data = get_radar_data()
# The host and path are now separate in the 2026 API
host = data['host'] 
past_frames = data['radar']['past']

st.title("AirAware Live Radar")

# 2. Scrubber logic
frame_idx = st.slider("Past 2 Hours", 0, len(past_frames)-1, len(past_frames)-1)
selected_path = past_frames[frame_idx]['path'] # This is now a hash, e.g., /v2/radar/72250d5768d7

# 3. Build the Map
# Centered on UVA / Charlottesville
m = folium.Map(location=[38.0336, -78.5080], zoom_start=6)

# 4. Correct 2026 Tile URL Format
# {host}{path}/{size}/{z}/{x}/{y}/{color}/{options}.png
# Using '2' for Universal Blue color and '1_1' for smoothed radar
radar_url = f"{host}{selected_path}/256/{{z}}/{{x}}/{{y}}/2/1_1.png"

folium.TileLayer(
    tiles=radar_url,
    attr='RainViewer.com',
    name='Live Radar',
    overlay=True,
    opacity=0.7
).add_to(m)

st_folium(m, width=700, height=500)