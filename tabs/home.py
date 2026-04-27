
"""
Home Tab — Air Aware
====================
Search form with full Milestone 3 adaptive interactivity:
  - Dynamic UI: trip type radio shows/hides return date (1);
                "Advanced Options" expander shows airline + class filters (2)
  - Widget keys: all interactive widgets have key= with comments on 3+
  - Callbacks: on_click reset button; on_change origin clears airline selection
  - Dependent dropdowns: airline list updates based on selected origin airport
"""

import streamlit as st
from datetime import date, timedelta
from data import ALL_AIRPORTS, get_airlines_for_origin, fetch_live_flights, flights_data
from navigation import start_view_transition

RESULTS_FILTER_DEFAULTS = {
    "risk_filter_select": "All",
    "time_filter_select": "All",
    "price_filter_select": "All",
    "sort_by_select": "On-Time Probability",
    "results_airline_filter": "All Airlines",
}

# Fancy advanced CSS
HOME_PLANNER_CSS = """
<style>
div[data-testid="stVerticalBlock"]:has(.planner-main-anchor) {
    background: linear-gradient(180deg, rgba(18, 26, 38, 0.96) 0%, rgba(13, 17, 23, 0.98) 100%);
    border: 1px solid rgba(121, 192, 255, 0.16);
    border-radius: 20px;
    padding: 1.35rem 1.35rem 1.15rem;
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.24);
    margin-bottom: 1rem;
}

div[data-testid="stVerticalBlock"]:has(.planner-recent-anchor) {
    background: rgba(13, 17, 23, 0.72);
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 1rem 1.15rem 0.7rem;
}

.planner-main-anchor,
.planner-recent-anchor {
    display: none;
}

.trip-planner-eyebrow {
    color: #79c0ff;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 0.45rem;
}

.trip-planner-title {
    color: #f0f6fc;
    font-size: 1.65rem;
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 0.45rem;
}

.trip-planner-copy {
    color: #8b949e;
    font-size: 0.95rem;
    max-width: 720px;
    margin-bottom: 1rem;
    line-height: 1.5;
}

.trip-planner-steps {
    display: flex;
    gap: 0.55rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.trip-planner-step {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.45rem 0.8rem;
    border-radius: 999px;
    background: rgba(13, 17, 23, 0.72);
    border: 1px solid #30363d;
    color: #8b949e;
    font-size: 0.82rem;
    font-weight: 600;
}

.trip-planner-step.is-active {
    background: rgba(31, 111, 235, 0.18);
    border-color: rgba(121, 192, 255, 0.34);
    color: #e6edf3;
}

.trip-planner-step.is-complete {
    background: rgba(63, 185, 80, 0.14);
    border-color: rgba(63, 185, 80, 0.28);
    color: #c9f8d2;
}

.trip-planner-step-index {
    width: 1.2rem;
    height: 1.2rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.06);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    font-weight: 700;
}

.trip-planner-section-label {
    color: #79c0ff;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin: 0.55rem 0 0.25rem;
}

.trip-planner-section-copy {
    color: #8b949e;
    font-size: 0.88rem;
    margin-bottom: 0.75rem;
}

.trip-planner-divider {
    height: 1px;
    background: linear-gradient(90deg, rgba(48,54,61,0), rgba(48,54,61,0.95), rgba(48,54,61,0));
    margin: 0.9rem 0 1rem;
}

.trip-planner-submit-note {
    color: #8b949e;
    font-size: 0.85rem;
    margin: 0 0 0.5rem;
}

div[data-testid="stVerticalBlock"]:has(.planner-main-anchor) .stRadio > div {
    background: rgba(13, 17, 23, 0.6);
    border: 1px solid rgba(48, 54, 61, 0.95);
    padding: 0.55rem 0.85rem;
}

div[data-testid="stVerticalBlock"]:has(.planner-main-anchor) [data-testid="stForm"] {
    background: rgba(13, 17, 23, 0.55) !important;
    border: 1px solid rgba(48, 54, 61, 0.95) !important;
    border-radius: 16px !important;
    padding: 1.15rem 1.15rem 1rem !important;
}

div[data-testid="stVerticalBlock"]:has(.planner-main-anchor) .streamlit-expanderHeader {
    background: rgba(13, 17, 23, 0.55) !important;
    border-radius: 14px !important;
    border-color: rgba(48, 54, 61, 0.95) !important;
}

div[data-testid="stVerticalBlock"]:has(.planner-main-anchor) .streamlit-expanderContent {
    background: rgba(13, 17, 23, 0.35) !important;
    border-color: rgba(48, 54, 61, 0.95) !important;
}

div[data-testid="stVerticalBlock"]:has(.planner-main-anchor) div[data-testid="stFormSubmitButton"] button {
    width: 100%;
    background: linear-gradient(135deg, #1f6feb 0%, #2f81f7 55%, #79c0ff 100%);
    border: 1px solid rgba(121, 192, 255, 0.26);
    box-shadow: 0 14px 28px rgba(31, 111, 235, 0.34);
    padding: 0.95rem 1.2rem;
    font-size: 1rem;
    font-weight: 700;
}

div[data-testid="stVerticalBlock"]:has(.planner-main-anchor) div[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #388bfd 0%, #58a6ff 55%, #9cd7ff 100%);
    box-shadow: 0 16px 30px rgba(56, 139, 253, 0.42);
}
</style>
"""

STEP_LABELS = ["Search", "Select Flight", "View Risk"]


# =============================================================================
# CALLBACKS
# =============================================================================

def reset_search():
    """
    on_click callback: resets all search filters and results.
    A callback is needed here (not just an if-block) because we must clear
    multiple independent session_state keys atomically before re-render.
    """
    st.session_state.search_completed = False
    st.session_state.search_params = {}
    st.session_state.selected_flight = None
    st.session_state.flight_selected = False
    st.session_state.live_flights = None
    st.session_state.airline_filter = "All Airlines"
    st.session_state.active_view = "home"
    for key, value in RESULTS_FILTER_DEFAULTS.items():
        st.session_state[key] = value
    st.toast("🔄 Search cleared!", icon="✅")


def on_origin_change():
    """
    on_change callback: when origin changes, reset the dependent airline
    dropdown so stale selections from the previous origin don't carry over.
    Without this, a user who had 'Alaska Airlines' selected for LAX would
    see a broken selection after switching to MSP (where Alaska doesn't fly).
    """
    st.session_state.airline_filter = "All Airlines"


def reset_results_filters():
    for key, value in RESULTS_FILTER_DEFAULTS.items():
        st.session_state[key] = value


def sync_search_widgets(search_params):
    origin = search_params.get("origin", "MSP")
    if origin not in ALL_AIRPORTS:
        origin = ALL_AIRPORTS[0]

    destination_options = [airport for airport in ALL_AIRPORTS if airport != origin]
    destination = search_params.get("destination", destination_options[0] if destination_options else origin)
    if destination_options and destination not in destination_options:
        destination = destination_options[0]

    departure_date = search_params.get("departure_date", date.today() + timedelta(days=7))
    return_date = search_params.get("return_date") or (departure_date + timedelta(days=7))

    available_airlines = ["All Airlines"] + get_airlines_for_origin(origin)
    preferred_airline = search_params.get("preferred_airline", "All Airlines")
    if preferred_airline not in available_airlines:
        preferred_airline = "All Airlines"

    st.session_state.trip_type_radio = search_params.get("trip_type", "One-Way")
    st.session_state.origin_select = origin
    st.session_state.destination_select = destination
    st.session_state.departure_date_input = departure_date
    st.session_state.return_date_input = return_date
    st.session_state.passengers_select = search_params.get("passengers", "1 Adult")
    st.session_state.airline_filter = preferred_airline
    st.session_state.cabin_class_select = search_params.get("cabin_class", "Economy")


def make_recent_search_record(search_params):
    label = (
        f"{search_params['origin']} → {search_params['destination']} — "
        f"{search_params['departure_date'].strftime('%b %d')}"
    )
    return {
        "label": label,
        "params": dict(search_params),
    }


def save_recent_search(search_params):
    record = make_recent_search_record(search_params)
    recent = st.session_state.get("recent_searches", [])
    deduped = [
        item for item in recent
        if not isinstance(item, dict) or item.get("label") != record["label"]
    ]
    deduped.insert(0, record)
    st.session_state.recent_searches = deduped[:5]


def execute_search(search_params, save_recent=True):
    st.session_state.search_params = search_params
    st.session_state.selected_flight = None
    st.session_state.flight_selected = False
    reset_results_filters()

    live = fetch_live_flights(search_params["origin"], search_params["destination"])

    if live is None or len(live) == 0:
        st.session_state.live_flights = flights_data
    else:
        st.session_state.live_flights = live

    if save_recent:
        save_recent_search(search_params)

    st.session_state.search_completed = True


def render_recent_searches():
    with st.expander("Recent Searches", expanded=False):
        st.caption("Reopen a saved route without re-entering the trip details.")
        recent = st.session_state.get("recent_searches", [])
        if recent:
            for i, search in enumerate(recent):
                record = search if isinstance(search, dict) else {"label": str(search), "params": None}
                if st.button(f"🔄 {record['label']}", key=f"recent_{i}"):
                    if record.get("params"):
                        st.toast(f"Re-running {record['label']}", icon="✈️")
                        start_view_transition(
                            "results",
                            "Re-loading your saved flight options...",
                            action="search_flights",
                            payload={"search_params": record["params"], "save_recent": False},
                        )
                    else:
                        start_view_transition("results", "Opening your saved flight options...")
        else:
            st.info("No recent searches yet. Your searches will appear here.")


def render_planner_header(step):
    steps_html = "".join(
        [
            (
                f"<span class='trip-planner-step {'is-complete' if i + 1 < step else 'is-active' if i + 1 == step else ''}'>"
                f"<span class='trip-planner-step-index'>{'✓' if i + 1 < step else i + 1}</span>"
                f"{label}</span>"
            )
            for i, label in enumerate(STEP_LABELS)
        ]
    )
    st.markdown(
        f"""
        <div class="trip-planner-eyebrow">Trip Planner</div>
        <div class="trip-planner-title">Search once and compare safer flight options faster.</div>
        <div class="trip-planner-copy">
            Start with your route here, jump straight into flight results, and open risk analysis only when you are ready to inspect a specific option.
        </div>
        <div class="trip-planner-steps">{steps_html}</div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# RENDER
# =============================================================================

def render():
    st.markdown(HOME_PLANNER_CSS, unsafe_allow_html=True)

    # ── Step indicator (user feedback: multi-step workflow tracker) ──────────
    step = 1
    if st.session_state.get("search_completed"):
        step = 2
    if st.session_state.get("selected_flight"):
        step = 3

    with st.container():
        st.markdown("<div class='planner-main-anchor'></div>", unsafe_allow_html=True)
        render_planner_header(step)

        st.markdown("<div class='trip-planner-section-label'>Trip Type</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='trip-planner-section-copy'>Choose the shape of this trip before you set the route.</div>",
            unsafe_allow_html=True,
        )
        trip_type = st.radio(
            "Select trip type:",
            ["One-Way", "Round-Trip", "Multi-City"],
            horizontal=True,
            label_visibility="collapsed",
            key="trip_type_radio",  # key= ensures reset callback can target this widget
        )

        st.markdown("<div class='trip-planner-divider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='trip-planner-section-label'>Route</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='trip-planner-section-copy'>Pick where you are leaving from and where you want to land.</div>",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**From**")
            origin = st.selectbox(
                "Origin Airport",
                ALL_AIRPORTS,
                index=ALL_AIRPORTS.index("MSP") if "MSP" in ALL_AIRPORTS else 0,
                label_visibility="collapsed",
                key="origin_select",      # key= lets on_change and reset_search target this widget;
                                          # without a stable key Streamlit can't identify it across reruns
                on_change=on_origin_change,  # clears dependent airline dropdown when origin changes
            )

        with col2:
            st.markdown("**To**")
            dest_options = [a for a in ALL_AIRPORTS if a != origin]
            destination = st.selectbox(
                "Destination Airport",
                dest_options,
                label_visibility="collapsed",
                key="destination_select",
            )

        st.markdown("<div class='trip-planner-divider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='trip-planner-section-label'>Preferences</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='trip-planner-section-copy'>Optional filters to narrow the results before you compare flights.</div>",
            unsafe_allow_html=True,
        )

        with st.expander("Airline and cabin preferences", expanded=False):
            adv_col1, adv_col2 = st.columns(2)
            with adv_col1:
                available_airlines = ["All Airlines"] + get_airlines_for_origin(origin)
                preferred_airline = st.selectbox(
                    "Preferred Airline",
                    available_airlines,
                    key="airline_filter",  # key= is essential: reset_search() and on_origin_change()
                                           # both write to this key to clear the selection
                )
            with adv_col2:
                cabin_class = st.selectbox(
                    "Cabin Class",
                    ["Economy", "Premium Economy", "Business", "First"],
                    key="cabin_class_select",
                )

        st.markdown("<div class='trip-planner-divider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='trip-planner-section-label'>Travel Details</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='trip-planner-section-copy'>Set your dates and traveler count. Results open immediately after search.</div>",
            unsafe_allow_html=True,
        )

        with st.form("flight_search_form"):
            if trip_type == "Round-Trip":
                col3, col4, col5 = st.columns(3)
            else:
                col3, col5 = st.columns(2)

            with col3:
                st.markdown("**Departure Date**")
                departure_date = st.date_input(
                    "Departure",
                    min_value=date.today(),
                    value=date.today() + timedelta(days=7),
                    label_visibility="collapsed",
                    key="departure_date_input",  # key= required so reset_search() can target it
                                                  # and return date min_value stays in sync
                )

            return_date = None
            if trip_type == "Round-Trip":
                with col4:
                    st.markdown("**Return Date**")
                    return_date = st.date_input(
                        "Return",
                        min_value=departure_date + timedelta(days=1),
                        value=departure_date + timedelta(days=7),
                        label_visibility="collapsed",
                        key="return_date_input",
                    )

            with col5:
                st.markdown("**Passengers**")
                passengers = st.selectbox(
                    "Passengers",
                    ["1 Adult", "2 Adults", "3 Adults", "4 Adults", "5+ Adults"],
                    label_visibility="collapsed",
                    key="passengers_select",
                )

            st.markdown(
                "<div class='trip-planner-submit-note'>Search flights to jump straight into the comparison screen.</div>",
                unsafe_allow_html=True,
            )
            search_submitted = st.form_submit_button("Search Flights", use_container_width=True)

            if search_submitted:
                if origin == destination:
                    st.error("⚠️ Origin and destination cannot be the same airport.")
                    st.stop()

                if trip_type == "Round-Trip" and return_date and return_date <= departure_date:
                    st.error("⚠️ Return date must be after your departure date.")
                    st.stop()

                if departure_date < date.today():
                    st.error("⚠️ Departure date cannot be in the past.")
                    st.stop()

                search_params = {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "passengers": passengers,
                    "trip_type": trip_type,
                    "preferred_airline": preferred_airline,
                    "cabin_class": cabin_class,
                }
                start_view_transition(
                    "results",
                    "Searching flights and preparing your options...",
                    action="search_flights",
                    payload={"search_params": search_params, "save_recent": True},
                )

        if st.session_state.get("search_completed"):
            reset_col, note_col = st.columns([1, 2.6])
            with reset_col:
                st.button(
                    "Reset Search",
                    on_click=reset_search,
                    key="reset_btn",
                    help="Clears all filters and search results",
                    use_container_width=True,
                )
            with note_col:
                st.caption("Need to start fresh? Reset clears the planner and your current results.")

    with st.container():
        st.markdown("<div class='planner-recent-anchor'></div>", unsafe_allow_html=True)
        render_recent_searches()
