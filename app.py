import streamlit as st
import time

st.set_page_config(
    page_title="Air Aware - Flight Search",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

        /* ── Global reset & dark base ── */
        section[data-testid="stSidebar"]  {
            background: #11161e;
            border-right: 1px solid #30363d;
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 1.4rem;
        }

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
            padding: 22px 34px; border-radius: 14px; margin-bottom: 22px;
            border: 1px solid #30363d;
            box-shadow: 0 6px 28px rgba(0,0,0,0.38);
            display: flex; align-items: center; justify-content: space-between;
        }
        .air-aware-header h1 {
            color: #f0f6fc; margin: 0; font-size: 2.15rem; font-weight: 700;
            font-family: 'DM Sans', sans-serif;
        }
        .air-aware-header .tagline { color: #8b949e; font-size: 0.92rem; margin-top: 4px; }
        .header-stats { display: flex; gap: 18px; }
        .header-stat {
            text-align: center;
            background: rgba(13,17,23,0.35);
            border: 1px solid rgba(139,148,158,0.15);
            border-radius: 12px;
            min-width: 90px;
            padding: 10px 12px;
        }
        .header-stat .number { font-size: 1.35rem; font-weight: 700; color: #79c0ff; font-family: 'Space Mono', monospace; }
        .header-stat .label  { font-size: 0.65rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1.2px; }

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
            background: #f85149;
            color: #ffffff;
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(248,81,73,0.4);
        }
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="stBaseButton-primary"] {
            background: #1f6feb;
            color: #ffffff;
            border: 1px solid rgba(121, 192, 255, 0.28);
            box-shadow: 0 10px 22px rgba(31,111,235,0.32);
        }
        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="stBaseButton-primary"]:hover {
            background: #388bfd;
            color: #ffffff;
            box-shadow: 0 12px 24px rgba(56,139,253,0.38);
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

        .page-transition-overlay {
            position: fixed;
            inset: 0;
            z-index: 999999;
            background: rgba(6, 10, 15, 0.82);
            backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }
        .page-transition-card {
            min-width: 320px;
            max-width: 460px;
            padding: 30px 34px;
            border-radius: 20px;
            border: 1px solid rgba(121, 192, 255, 0.18);
            background: linear-gradient(180deg, rgba(22,27,34,0.96) 0%, rgba(13,17,23,0.98) 100%);
            box-shadow: 0 20px 55px rgba(0, 0, 0, 0.42);
            text-align: center;
        }
        .page-transition-plane {
            font-size: 2.8rem;
            display: inline-block;
            animation: plane-float 1.1s ease-in-out infinite;
            transform-origin: center;
            margin-bottom: 12px;
        }
        .page-transition-title {
            color: #f0f6fc;
            font-size: 1.12rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .page-transition-copy {
            color: #8b949e;
            font-size: 0.93rem;
            line-height: 1.45;
        }
        .page-transition-track {
            width: 100%;
            height: 6px;
            border-radius: 999px;
            overflow: hidden;
            background: rgba(48, 54, 61, 0.9);
            margin-top: 18px;
        }
        .page-transition-bar {
            width: 38%;
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #1f6feb, #79c0ff);
            animation: plane-progress 1.2s ease-in-out infinite;
        }
        @keyframes plane-float {
            0%, 100% { transform: translateY(0px) rotate(-5deg); }
            50% { transform: translateY(-6px) rotate(2deg); }
        }
        @keyframes plane-progress {
            0% { transform: translateX(-140%); }
            100% { transform: translateX(360%); }
        }

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
    "risk_filter_select": "All",
    "time_filter_select": "All",
    "price_filter_select": "All",
    "sort_by_select": "On-Time Probability",
    "results_airline_filter": "All Airlines",
    "active_view":      "home",
    "nav_view":         "home",
    "transition_active": False,
    "transition_phase": None,
    "transition_target": None,
    "transition_message": "",
    "transition_action": None,
    "transition_payload": None,
    "transition_started_at": None,
    "transition_hold_until": None,
    "transition_error": None,
    "assistant_messages": [],  # persists SkyAssist chat history across reruns
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Tab modules ───────────────────────────────────────────────────────────────
from tabs import home, flight_results, flight_risk, weather_map, assistant
from booking import render_continue_to_airline


def render_transition_overlay():
    message = st.session_state.get("transition_message") or "Preparing your next step..."
    st.markdown(
        f"""
        <div class="page-transition-overlay">
            <div class="page-transition-card">
                <div class="page-transition-plane">✈️</div>
                <div class="page-transition-title">{message}</div>
                <div class="page-transition-copy">
                    Air Aware is processing your selection and loading the next screen.
                </div>
                <div class="page-transition-track">
                    <div class="page-transition-bar"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def clear_transition_state():
    st.session_state.transition_active = False
    st.session_state.transition_phase = None
    st.session_state.transition_target = None
    st.session_state.transition_message = ""
    st.session_state.transition_action = None
    st.session_state.transition_payload = None
    st.session_state.transition_started_at = None
    st.session_state.transition_hold_until = None


def fail_transition(message):
    clear_transition_state()
    st.session_state.transition_error = message
    st.session_state.active_view = "home"


def process_transition():
    if not st.session_state.get("transition_active"):
        return

    render_transition_overlay()

    now = time.monotonic()
    started_at = st.session_state.get("transition_started_at") or now
    st.session_state.transition_started_at = started_at
    if now - started_at >= 10:
        fail_transition("That took too long to load, so you were returned to Home. Please try again.")
        st.rerun()

    phase = st.session_state.get("transition_phase") or "show"

    if phase == "show":
        st.session_state.transition_phase = "run"
        st.rerun()

    if phase == "run":
        try:
            transition_action = st.session_state.get("transition_action")
            transition_payload = st.session_state.get("transition_payload") or {}

            if transition_action == "search_flights":
                home.execute_search(
                    transition_payload.get("search_params", {}),
                    save_recent=transition_payload.get("save_recent", True),
                )
            elif transition_action == "reset_search_state":
                home.reset_search()

            st.session_state.transition_phase = "finish"
            st.session_state.transition_hold_until = time.monotonic() + 0.8
        except Exception:
            fail_transition("Something went wrong while loading the next page, so you were returned to Home.")
        st.rerun()

    hold_until = st.session_state.get("transition_hold_until") or now
    remaining = hold_until - now
    if remaining > 0:
        time.sleep(min(remaining, 0.8))

    target_view = st.session_state.get("transition_target") or st.session_state.get("active_view", "home")
    clear_transition_state()
    st.session_state.active_view = target_view
    st.rerun()


process_transition()

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

transition_error = st.session_state.pop("transition_error", None)
if transition_error:
    st.error(transition_error)


# ── Tabs ──────────────────────────────────────────────────────────────────────
NAV_OPTIONS = ["home", "results", "risk", "weather", "assistant"]
NAV_LABELS = {
    "home": "Home",
    "results": "Flight Results",
    "risk": "Risk Analysis",
    "weather": "Weather Radar",
    "assistant": "AI Assistant",
}
NAV_ICONS = {
    "home": "🏠",
    "results": "📋",
    "risk": "⚠️",
    "weather": "🌤️",
    "assistant": "🤖",
}


def sync_active_view():
    st.session_state.active_view = st.session_state.nav_view
if st.session_state.get("nav_view") != st.session_state.get("active_view"):
    st.session_state.nav_view = st.session_state.active_view

with st.sidebar:
    st.markdown("## Air Aware")
    st.caption("Move through search, comparison, and risk review without losing your place.")
    st.radio(
        "Navigate",
        NAV_OPTIONS,
        format_func=lambda view: f"{NAV_ICONS[view]} {NAV_LABELS[view]}",
        label_visibility="collapsed",
        key="nav_view",
        on_change=sync_active_view,
    )
    st.markdown("---")
    st.markdown("### Trip Snapshot")
    params = st.session_state.get("search_params", {})
    if params:
        dep = params.get("departure_date")
        dep_str = dep.strftime("%b %d, %Y") if hasattr(dep, "strftime") else str(dep)
        st.markdown(f"**Route**  \n{params.get('origin', '?')} → {params.get('destination', '?')}")
        st.markdown(f"**Departure**  \n{dep_str}")
        st.markdown(f"**Passengers**  \n{params.get('passengers', 'Not set')}")
    else:
        st.caption("No search yet. Start from Home to find flight options.")

    selected = st.session_state.get("selected_flight")
    if selected:
        st.markdown("### Selected Flight")
        st.markdown(f"**{selected['airline']} {selected['flight_num']}**")
        st.caption(
            f"{selected['departure']} – {selected['arrival']} · "
            f"{selected['on_time_prob']}% on-time"
        )
        st.markdown("### Booking")
        render_continue_to_airline(selected, compact=True)
    elif st.session_state.get("search_completed"):
        st.caption("Choose a flight on the results page to unlock the risk breakdown.")

active_view = st.session_state.get("active_view", "home")
if active_view == "home":
    home.render()
elif active_view == "results":
    flight_results.render()
elif active_view == "risk":
    flight_risk.render()
elif active_view == "assistant":
    assistant.render()
else:
    weather_map.render()

st.markdown("""
    <div class="footer">
        <p>✈️ <strong>Air Aware</strong> · Powered by Machine Learning & Real-Time Data</p>
        <p>© 2026 Air Aware · DS 5023 Project</p>
    </div>
""", unsafe_allow_html=True)
