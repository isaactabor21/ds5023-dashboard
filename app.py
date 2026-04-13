import streamlit as st
from datetime import date, timedelta

st.set_page_config(
    page_title="Air Aware - Flight Search",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

        /* ── Global reset & dark base ── */
        [data-testid="collapsedControl"] {display: none;}
        section[data-testid="stSidebar"]  {display: none;}

        .stApp {
            background: #0d1117;
            font-family: 'DM Sans', sans-serif;
        }

        /* ── Main container: dark card on dark bg ── */
        .main .block-container {
            background: #161b22;
            border-radius: 16px;
            padding: 2rem 3rem;
            margin-top: 1rem;
            border: 1px solid #30363d;
            max-width: 1200px;
        }

        /* ── All base text ── */
        .stApp, .stApp p, .stApp li,
        .stApp label, .stApp div { color: #e6edf3; }
        .stApp h1, .stApp h2, .stApp h3,
        .stApp h4, .stApp h5, .stApp h6 { color: #f0f6fc; }

        /* ── Header ── */
        .air-aware-header {
            background: linear-gradient(135deg, #1a2332 0%, #0f2942 50%, #1a2332 100%);
            padding: 25px 40px; border-radius: 14px; margin-bottom: 25px;
            border: 1px solid #30363d;
            box-shadow: 0 8px 40px rgba(0,0,0,0.5);
            display: flex; align-items: center; justify-content: space-between;
        }
        .air-aware-header h1 {
            color: #f0f6fc; margin: 0; font-size: 2.4rem; font-weight: 700;
            font-family: 'DM Sans', sans-serif;
        }
        .air-aware-header .tagline { color: #8b949e; font-size: 0.95rem; margin-top: 5px; }
        .header-stats { display: flex; gap: 30px; }
        .header-stat { text-align: center; }
        .header-stat .number { font-size: 1.8rem; font-weight: 700; color: #58a6ff; font-family: 'Space Mono', monospace; }
        .header-stat .label  { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1.5px; }

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab-list"] {
            background: #0d1117;
            padding: 8px 12px; border-radius: 12px; gap: 6px;
            border: 1px solid #30363d;
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 8px; padding: 10px 22px;
            font-weight: 600; font-size: 0.9rem;
            color: #8b949e;
            border: 1px solid transparent;
            transition: all 0.2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background: #21262d; color: #e6edf3;
        }
        .stTabs [aria-selected="true"] {
            background: #1f6feb !important;
            color: #ffffff !important;
            border-color: #388bfd !important;
            box-shadow: 0 4px 14px rgba(31,111,235,0.4);
        }
        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] { display: none; }

        /* ── Inputs, selects, date pickers ── */
        .stTextInput > div > div > input,
        .stDateInput  > div > div > input {
            background: #0d1117 !important;
            color: #e6edf3 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }
        .stTextInput > div > div > input:focus,
        .stDateInput  > div > div > input:focus {
            border-color: #388bfd !important;
            box-shadow: 0 0 0 3px rgba(56,139,253,0.2) !important;
        }
        /* Selectbox container */
        .stSelectbox > div > div,
        [data-baseweb="select"] > div {
            background: #0d1117 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
            color: #e6edf3 !important;
        }
        /* Selectbox dropdown menu */
        [data-baseweb="popover"] [role="listbox"],
        [data-baseweb="menu"] {
            background: #161b22 !important;
            border: 1px solid #30363d !important;
        }
        [data-baseweb="option"]:hover,
        [data-baseweb="option"][aria-selected="true"] {
            background: #21262d !important;
        }
        [data-baseweb="option"] { color: #e6edf3 !important; }

        /* ── Radio buttons ── */
        .stRadio > div {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 10px 16px;
        }
        .stRadio label { color: #e6edf3 !important; }

        /* ── Form container ── */
        .stForm,
        [data-testid="stForm"] {
            background: #0d1117 !important;
            border: 1px solid #30363d !important;
            border-radius: 12px !important;
            padding: 20px !important;
        }

        /* ── Expander ── */
        .streamlit-expanderHeader {
            background: #0d1117 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
            color: #e6edf3 !important;
        }
        .streamlit-expanderContent {
            background: #0d1117 !important;
            border: 1px solid #30363d !important;
            border-top: none !important;
        }

        /* ── Buttons ── */
        .stButton > button {
            background: #1f6feb;
            color: #ffffff; border: none; border-radius: 8px;
            padding: 10px 24px; font-weight: 600; font-size: 0.95rem;
            transition: all 0.2s ease;
            box-shadow: 0 4px 14px rgba(31,111,235,0.35);
        }
        .stButton > button:hover {
            background: #388bfd;
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(56,139,253,0.45);
        }
        .stButton > button:active { transform: translateY(0); }

        /* ── Alerts ── */
        [data-testid="stAlert"] {
            border-radius: 10px !important;
            border-left-width: 4px !important;
        }
        /* success */
        [data-testid="stAlert"][data-baseweb="notification"][kind="positive"],
        div[data-testid="stSuccessAlert"] {
            background: #0d2818 !important; color: #3fb950 !important;
        }
        /* warning */
        div[data-testid="stWarningAlert"] {
            background: #2d1f00 !important; color: #d29922 !important;
        }
        /* error */
        div[data-testid="stErrorAlert"] {
            background: #2d0f0f !important; color: #f85149 !important;
        }
        /* info */
        div[data-testid="stInfoAlert"] {
            background: #0c2d4e !important; color: #58a6ff !important;
        }

        /* ── Spinner ── */
        .stSpinner > div { border-color: #1f6feb !important; }

        /* ── Metrics ── */
        [data-testid="stMetricValue"] {
            font-size: 2.2rem; font-weight: 700;
            color: #58a6ff !important;
            font-family: 'Space Mono', monospace;
        }
        [data-testid="stMetricLabel"] { color: #8b949e !important; }

        /* ── Markdown text ── */
        .stMarkdown p  { color: #e6edf3; }
        .stMarkdown strong { color: #f0f6fc; }
        caption, .stCaption { color: #8b949e !important; }

        /* ── Divider ── */
        hr {
            border: none; height: 1px;
            background: linear-gradient(90deg, transparent, #30363d, transparent);
            margin: 20px 0;
        }

        /* ── Dataframe / table ── */
        [data-testid="stDataFrame"] {
            border: 1px solid #30363d !important;
            border-radius: 10px !important;
            overflow: hidden;
        }

        /* ── Footer ── */
        .footer {
            text-align: center; padding: 20px;
            color: #8b949e; font-size: 0.85rem;
            margin-top: 30px; border-top: 1px solid #30363d;
        }

        /* ── iframe (radar map) ── */
        iframe { border-radius: 12px; border: 1px solid #30363d; }

        /* ── Slider ── */
        [data-testid="stSlider"] > div > div > div { background: #1f6feb !important; }
    </style>
""", unsafe_allow_html=True)

# ── Session state initialization ──────────────────────────────────────────────
defaults = {
    "recent_searches":  [],
    "search_completed": False,
    "search_params":    {},
    "selected_flight":  None,
    "flight_selected":  False,
    "live_flights":     None,
    "airline_filter":   "All Airlines",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Tab modules ───────────────────────────────────────────────────────────────
from tabs import home, flight_results, flight_risk, weather_map

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
    <div class="air-aware-header">
        <div>
            <h1>✈️ Air Aware</h1>
            <div class="tagline">Predict delays. Travel smarter. Fly confident.</div>
        </div>
        <div class="header-stats">
            <div class="header-stat"><div class="number">98%</div><div class="label">Accuracy</div></div>
            <div class="header-stat"><div class="number">500+</div><div class="label">Airports</div></div>
            <div class="header-stat"><div class="number">Live</div><div class="label">Weather Data</div></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── Mock data banner — shown whenever no API key is configured ────────────────
# This runs once at the app level so it appears on EVERY tab, not just Home.
# st.info() inside individual tabs is too easy to miss on first load.
# Check which API keys are configured
_PLACEHOLDERS = {"YOUR_AVIATIONSTACK_KEY_HERE", "YOUR_OPENWEATHER_KEY_HERE", "YOUR_API_KEY_HERE", ""}
try:
    _av_key  = st.secrets.get("AVIATIONSTACK_KEY", "")
    _ow_key  = st.secrets.get("OPENWEATHER_KEY", "")
    _av_live = bool(_av_key)  and _av_key  not in _PLACEHOLDERS
    _ow_live = bool(_ow_key)  and _ow_key  not in _PLACEHOLDERS
except Exception:
    _av_live = False
    _ow_live = False

# Build per-service status lines for the banner
_missing = []
if not _av_live:
    _missing.append("✈️ <strong>Flight data</strong> (AviationStack) — results are synthetic placeholders")
if not _ow_live:
    _missing.append("🌤️ <strong>Live weather</strong> (OpenWeatherMap) — weather cards show estimated conditions")

if _missing:
    _items = "".join(f"<li style='margin:4px 0;color:#8b949e;'>{m}</li>" for m in _missing)
    st.markdown(f"""
        <div style="background:#2d1f00;border:1px solid #d29922;border-left:5px solid #d29922;
                    border-radius:10px;padding:14px 20px;margin-bottom:18px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                <span style="font-size:1.3rem;">⚠️</span>
                <strong style="color:#d29922;font-size:1rem;">Demo Mode — Some live data sources are not configured</strong>
            </div>
            <ul style="margin:0;padding-left:20px;">{_items}</ul>
            <p style="margin:10px 0 0;color:#8b949e;font-size:0.82rem;">
                Add your API keys to
                <code style="background:#0d1117;padding:2px 6px;border-radius:4px;color:#58a6ff;">.streamlit/secrets.toml</code>
                to enable live data. See the file for sign-up links.
            </p>
        </div>
    """, unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_home, tab_results, tab_risk, tab_weather = st.tabs([
    "🏠 Home", "📋 Flight Results", "⚠️ Risk Analysis", "🌤️ Weather Radar"
])

with tab_home:     
    home.render()
with tab_results:  
    flight_results.render()
with tab_risk:     
    flight_risk.render()
with tab_weather:  
    weather_map.render()

st.markdown("""
    <div class="footer">
        <p>✈️ <strong>Air Aware</strong> · Powered by Machine Learning & Real-Time Data</p>
        <p>© 2026 Air Aware · DS 5023 Project</p>
    </div>
""", unsafe_allow_html=True)
