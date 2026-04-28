"""
Flight Results Tab — dark theme edition
"""

import streamlit as st
import plotly.graph_objects as go
from data import flights_data, get_probability_color
from navigation import start_view_transition
from ui_shell import inject_page_shell_styles, render_page_intro, render_section_intro, render_inline_summary

LOW_RISK_THRESHOLD  = 67
MEDIUM_RISK_THRESHOLD = 33
GREEN  = '#3fb950'
YELLOW = '#d29922'
RED    = '#f85149'
CARD_BG      = '#0d1117'
BORDER_COLOR = '#30363d'
FILTER_DEFAULTS = {
    "risk_filter_select": "All",
    "time_filter_select": "All",
    "price_filter_select": "All",
    "sort_by_select": "On-Time Probability",
    "results_airline_filter": "All Airlines",
}


def get_time_period(departure_time):
    try:
        hour = int(departure_time.split(":")[0])
        am_pm = departure_time.split(" ")[1].upper()
        if am_pm == "PM" and hour != 12: hour += 12
        elif am_pm == "AM" and hour == 12: hour = 0
        if 5 <= hour < 12:   return "Morning (5AM-12PM)"
        elif 12 <= hour < 17: return "Afternoon (12PM-5PM)"
        else:                 return "Evening (5PM-12AM)"
    except (IndexError, ValueError):
        return "Unknown"


def parse_time_for_sort(time_str):
    try:
        hour   = int(time_str.split(":")[0])
        minute = int(time_str.split(":")[1].split(" ")[0])
        am_pm  = time_str.split(" ")[1].upper()
        if am_pm == "PM" and hour != 12: hour += 12
        elif am_pm == "AM" and hour == 12: hour = 0
        return hour * 60 + minute
    except (IndexError, ValueError):
        return 0


def get_risk_color(prob):
    if prob >= LOW_RISK_THRESHOLD:   return GREEN
    elif prob >= MEDIUM_RISK_THRESHOLD: return YELLOW
    return RED


def parse_duration_minutes(duration_str):
    try:
        parts = duration_str.lower().replace("m", "").split("h")
        hours = int(parts[0].strip()) if parts[0].strip() else 0
        minutes = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
        return (hours * 60) + minutes
    except (IndexError, ValueError, AttributeError):
        return 9999


def trigger_reset_results_filters():
    st.session_state.reset_results_filters = True


def build_flight_labels(flights):
    if not flights:
        return {}

    labels = {}

    def add_label(flight_id, label, bg_color, text_color):
        labels.setdefault(flight_id, []).append(
            {"label": label, "bg": bg_color, "text": text_color}
        )

    safest = max(flights, key=lambda x: x["on_time_prob"])
    fastest = min(flights, key=lambda x: parse_duration_minutes(x.get("duration", "")))
    add_label(safest["id"], "Lowest Risk", f"{GREEN}22", GREEN)
    add_label(fastest["id"], "Fastest", "#0c2d4e", "#79c0ff")

    priced_flights = [flight for flight in flights if flight.get("price") and flight["price"] > 0]
    if priced_flights:
        min_price = min(flight["price"] for flight in priced_flights)
        max_price = max(flight["price"] for flight in priced_flights)
        min_prob = min(flight["on_time_prob"] for flight in priced_flights)
        max_prob = max(flight["on_time_prob"] for flight in priced_flights)

        def value_score(flight):
            if max_price == min_price:
                price_score = 1
            else:
                price_score = 1 - ((flight["price"] - min_price) / (max_price - min_price))

            if max_prob == min_prob:
                reliability_score = 1
            else:
                reliability_score = (
                    (flight["on_time_prob"] - min_prob) / (max_prob - min_prob)
                )
            return (0.65 * reliability_score) + (0.35 * price_score)

        best_value = max(priced_flights, key=value_score)
        add_label(best_value["id"], "Best Value", "#2d1f00", YELLOW)

    return labels


def apply_filters(flights, risk_filter, time_filter, price_filter, airline_filter):
    f = flights.copy()
    if risk_filter == "Low Risk (67-100%)":    f = [x for x in f if x["on_time_prob"] >= 67]
    elif risk_filter == "Medium Risk (33-66%)": f = [x for x in f if 33 <= x["on_time_prob"] < 67]
    elif risk_filter == "High Risk (0-32%)":    f = [x for x in f if x["on_time_prob"] < 33]
    if time_filter != "All":
        f = [x for x in f if get_time_period(x["departure"]) == time_filter]
    if price_filter == "Under $300":   f = [x for x in f if x["price"] < 300]
    elif price_filter == "$300-$400":  f = [x for x in f if 300 <= x["price"] <= 400]
    elif price_filter == "Over $400":  f = [x for x in f if x["price"] > 400]
    if airline_filter != "All Airlines": f = [x for x in f if x["airline"] == airline_filter]
    return f


def sort_flights(flights, sort_by):
    if sort_by == "On-Time Probability": return sorted(flights, key=lambda x: x["on_time_prob"], reverse=True)
    elif sort_by == "Price":             return sorted(flights, key=lambda x: x["price"])
    return sorted(flights, key=lambda x: parse_time_for_sort(x["departure"]))


def render_horizontal_bar_chart(flights):
    st.markdown("<p style='font-size:16px;font-weight:600;margin-bottom:5px;color:#e6edf3;'>On-Time Probability by Flight</p>", unsafe_allow_html=True)
    sf = sorted(flights, key=lambda x: x["on_time_prob"], reverse=True)
    fig = go.Figure(data=[go.Bar(
        y=[f"{f['airline']} {f['flight_num']}" for f in sf],
        x=[f["on_time_prob"] for f in sf],
        orientation="h",
        marker_color=[get_risk_color(f["on_time_prob"]) for f in sf],
        text=[f"{f['on_time_prob']}%" for f in sf],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=13, color="white", weight="bold"),
        hovertemplate="<b>%{y}</b><br>On-Time: %{x}%<extra></extra>",
    )])
    fig.update_layout(
        plot_bgcolor='#0d1117', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title="On-Time Probability (%)", range=[0, 100], dtick=20,
                   color="#8b949e", gridcolor="#21262d", linecolor="#30363d"),
        yaxis=dict(color="#8b949e", linecolor="#30363d"),
        margin=dict(l=10, r=20, t=5, b=40),
        height=max(200, len(flights) * 44), bargap=0.3,
        font=dict(color="#8b949e"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="bar_chart")


def render_pie_chart(flights):
    st.markdown("<p style='font-size:16px;font-weight:600;margin-bottom:5px;color:#e6edf3;'>Risk Distribution</p>", unsafe_allow_html=True)
    low    = len([f for f in flights if f["on_time_prob"] >= 67])
    medium = len([f for f in flights if 33 <= f["on_time_prob"] < 67])
    high   = len([f for f in flights if f["on_time_prob"] < 33])
    labels, values, colors = [], [], []
    if low:    labels.append("Low (67-100%)");    values.append(low);    colors.append(GREEN)
    if medium: labels.append("Medium (33-66%)");  values.append(medium); colors.append(YELLOW)
    if high:   labels.append("High (0-32%)");     values.append(high);   colors.append(RED)
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors, line=dict(color="#161b22", width=3)),
        hole=0.4, textinfo="none",
        hovertemplate="<b>%{label}</b><br>Flights: %{value}<br>%{percent}<extra></extra>",
    )])
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=5, b=5), height=220,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5,
                    font=dict(color="#8b949e")),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="pie_chart")


def render_flight_card(flight, labels=None):
    prob_color, _ = get_probability_color(flight["on_time_prob"])
    col1, col2, col3, col4 = st.columns([1.5, 2.5, 1.5, 1.5])

    with col1:
        st.markdown(f"""
            <div style="background:{prob_color}22;border:1px solid {prob_color}66;
                        color:{prob_color};padding:12px;border-radius:10px;text-align:center;">
                <div style="font-size:26px;font-weight:700;font-family:'Space Mono',monospace;">{flight['on_time_prob']}%</div>
                <div style="font-size:10px;letter-spacing:0.5px;opacity:0.85;">ON-TIME</div>
            </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"**{flight['airline']} {flight['flight_num']}**")
        if labels:
            pills = "".join(
                [
                    (
                        f"<span style='display:inline-block;margin:0 8px 8px 0;padding:4px 10px;"
                        f"border-radius:999px;background:{label['bg']};color:{label['text']};"
                        f"font-size:0.78rem;font-weight:700;border:1px solid {label['text']}44;'>"
                        f"{label['label']}</span>"
                    )
                    for label in labels
                ]
            )
            st.markdown(pills, unsafe_allow_html=True)
        st.markdown(f"**{flight['origin']}** → **{flight['destination']}**")
        st.markdown(f"{flight['departure']} – {flight['arrival']} · {flight['duration']}")
        st.caption(f"{flight['stops']}  ·  Status: {flight.get('status','—')}")

    with col3:
        price = flight["price"]

        price_text = f"${price}" if price else "Price N/A"

        st.markdown(
            f"""
            <div style="
                font-size:1.5rem;
                font-weight:600;
                color:#8b949e;
                font-family:'Space Mono',monospace;
                text-align:left;
            ">
                {price_text}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        if st.button(
            "Review Flight",
            key=f"select_{flight['id']}",
            use_container_width=True,
            help="Open Risk Analysis for this flight and review weather-adjusted delay risk.",
        ):
            st.session_state.selected_flight = flight
            st.session_state.flight_selected = True
            st.toast(f"✅ Selected {flight['airline']} {flight['flight_num']}!", icon="✈️")
            start_view_transition("risk", "Building your flight risk analysis...")

    st.markdown(f"<hr style='border:none;height:1px;background:{BORDER_COLOR};margin:12px 0;'/>", unsafe_allow_html=True)


def render_weather_alerts(filtered_flights, all_flights):
    render_section_intro("Decision support")
    risky = [f for f in filtered_flights if f["on_time_prob"] < 50]
    if risky:
        st.markdown(f"""
            <div style="background:#2d1f00;border:1px solid #d2992244;border-left:4px solid #d29922;
                        padding:15px;border-radius:10px;margin-bottom:12px;">
                <h4 style="color:#d29922;margin:0 0 6px;">⚠️ Weather Alert</h4>
                <p style="margin:0;color:#8b949e;">Several flights may be affected. Consider higher on-time probability options.</p>
            </div>""", unsafe_allow_html=True)
        best = max(all_flights, key=lambda x: x["on_time_prob"])
        st.markdown(f"""
            <div style="background:#0d2818;border:1px solid #3fb95044;border-left:4px solid #3fb950;
                        padding:15px;border-radius:10px;">
                <h4 style="color:#3fb950;margin:0 0 6px;">✅ Better Option Found</h4>
                <p style="margin:0;color:#8b949e;">
                    <strong style="color:#e6edf3;">{best['airline']} {best['flight_num']} — {best['on_time_prob']}% On-Time</strong>
                    · {'$'+str(best['price']) if best['price'] else 'N/A'}
                </p>
            </div>""", unsafe_allow_html=True)
    elif filtered_flights:
        st.success("All displayed flights are currently in a healthy reliability range.")

def render_analytics_summary(flights):
    prices = [flight["price"] for flight in flights if flight.get("price")]
    avg_price = f"${round(sum(prices) / len(prices))}" if prices else "N/A"
    avg_prob = round(sum(flight["on_time_prob"] for flight in flights) / len(flights))
    low_risk_count = len([flight for flight in flights if flight["on_time_prob"] >= LOW_RISK_THRESHOLD])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Flights Compared", len(flights))
    with col2:
        st.metric("Average On-Time", f"{avg_prob}%")
    with col3:
        st.metric("Average Price", avg_price)

    st.caption(f"{low_risk_count} flight(s) are currently in the low-risk range.")


def render_selected_flight_banner(selected_flight):
    render_inline_summary(
        f"Selected flight: {selected_flight['airline']} {selected_flight['flight_num']}",
        (
            f"{selected_flight['origin']} → {selected_flight['destination']} · "
            f"{selected_flight['departure']} – {selected_flight['arrival']} · "
            f"{selected_flight['on_time_prob']}% on-time"
        ),
    )
    col1, col2 = st.columns([1.3, 1.1])
    with col1:
        if st.button(
            "Review Risk Analysis",
            key="goto_risk_banner",
            use_container_width=True,
            help="Go to the selected flight's full risk breakdown with weather effects and alternatives.",
        ):
            start_view_transition("risk", "Opening the risk breakdown...")
    with col2:
        if st.button(
            "Start New Search",
            key="new_search_banner",
            use_container_width=True,
            help="Clear the current trip and return to Home to search a different route.",
        ):
            start_view_transition(
                "home",
                "Returning you to the search page...",
                action="reset_search_state",
            )


def render():
    if not st.session_state.get("search_completed"):
        st.warning("⚠️ Please search for a flight on the Home page first.")
        return

    inject_page_shell_styles()
    params = st.session_state.get("search_params", {})
    source_flights = st.session_state.get("live_flights", flights_data)
    selected_flight = st.session_state.get("selected_flight")
    route_title = "Flight Results"
    route_subtitle = "Pick a flight to review next."
    header_chips = [f"{len(source_flights)} option{'s' if len(source_flights) != 1 else ''}"]
    if params:
        dep = params.get("departure_date")
        dep_str = dep.strftime("%b %d") if hasattr(dep, "strftime") else str(dep)
        route_title = f"{params.get('origin','?')} → {params.get('destination','?')}"
        route_subtitle = f"{dep_str} · Pick a flight to review next."
        header_chips.append(dep_str)
    if selected_flight:
        header_chips.append("1 flight selected")
    render_page_intro("Flight Results", route_title, route_subtitle, header_chips)

    nav_col1, _ = st.columns([1.15, 3.85])
    with nav_col1:
        if st.button(
            "Back to Home",
            key="results_back_home",
            use_container_width=True,
            help="Start over with a different route or travel date.",
        ):
            start_view_transition(
                "home",
                "Returning you to the search page...",
                action="reset_search_state",
            )
    if selected_flight:
        render_selected_flight_banner(selected_flight)

    render_section_intro("Refine results")
    airline_names = ["All Airlines"] + sorted({flight["airline"] for flight in source_flights})
    if st.session_state.get("results_airline_filter") not in airline_names:
        st.session_state.results_airline_filter = "All Airlines"

    # Apply filter reset BEFORE widgets exist
    if st.session_state.get("reset_results_filters"):
        for key, value in FILTER_DEFAULTS.items():
            st.session_state[key] = value

        st.session_state.reset_results_filters = False

    if st.session_state.get("apply_safest_filters"):
        st.session_state.risk_filter_select = "Low Risk (67-100%)"
        st.session_state.sort_by_select = "On-Time Probability"
        st.session_state.time_filter_select = "All"
        st.session_state.price_filter_select = "All"
        st.session_state.results_airline_filter = "All Airlines"

        st.session_state.apply_safest_filters = False

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        risk_filter = st.selectbox("Risk", ["All","Low Risk (67-100%)","Medium Risk (33-66%)","High Risk (0-32%)"], key="risk_filter_select")
    with col2:
        time_filter = st.selectbox("Time", ["All","Morning (5AM-12PM)","Afternoon (12PM-5PM)","Evening (5PM-12AM)"], key="time_filter_select")
    with col3:
        price_filter = st.selectbox("Price", ["All","Under $300","$300-$400","Over $400"], key="price_filter_select")
    with col4:
        sort_by = st.selectbox("Sort By", ["On-Time Probability","Price","Departure Time"], key="sort_by_select")
    with col5:
        all_flights_data = st.session_state.get("live_flights", flights_data)
        airline_names = ["All Airlines"] + sorted({f["airline"] for f in all_flights_data})
        airline_filter = st.selectbox("Airline", airline_names, key="results_airline_filter")

    action_col1, action_col2, _ = st.columns([1, 1, 3])

    with action_col1:
        if st.button(
            "Clear Filters",
            key="clear_results_filters",
            use_container_width=True,
            help="Reset all filters and show the full set of flight options again.",
        ):
            trigger_reset_results_filters()
            st.rerun()

    with action_col2:
        if st.button(
            "Show Safest Flights",
            key="show_safest_flights",
            use_container_width=True,
            help="Keep only low-risk flights and sort them by reliability.",
        ):
            st.session_state.apply_safest_filters = True
            st.rerun()
    if risk_filter == "High Risk (0-32%)" and price_filter == "Over $400":
        st.warning("⚠️ High-risk flights rarely exceed $400 — you may get no results with this combination.")

    with st.spinner("🔍 Filtering flights..."):
        source_flights = st.session_state.get("live_flights", flights_data)
        filtered = apply_filters(source_flights, risk_filter, time_filter, price_filter, airline_filter)
        filtered = sort_flights(filtered, sort_by)

    if not filtered:
        st.warning("No flights match your current filters.")
        recovery_col1, recovery_col2 = st.columns(2)
        with recovery_col1:
            if st.button(
                "Reset All Result Filters",
                key="reset_filters_empty",
                use_container_width=True,
                help="Clear the filters that are hiding all of the available flights.",
            ):
                reset_results_filters()
                st.rerun()
        with recovery_col2:
            if st.button(
                "Show Only Safest Options",
                key="show_safest_empty",
                use_container_width=True,
                help="Jump straight to low-risk flights instead of broadening everything.",
            ):
                reset_results_filters()
                st.session_state.risk_filter_select = "Low Risk (67-100%)"
                st.session_state.sort_by_select = "On-Time Probability"
                st.rerun()
        return

    labels_by_id = build_flight_labels(filtered)
    st.caption(f"{len(filtered)} flight{'s' if len(filtered) != 1 else ''}")

    tab_flights, tab_analytics = st.tabs(["Flights", "Analytics"])
    with tab_flights:
        render_section_intro("Flight options")
        for flight in filtered:
            render_flight_card(flight, labels_by_id.get(flight["id"], []))

        render_weather_alerts(filtered, source_flights)

    with tab_analytics:
        render_section_intro("Analytics")
        render_analytics_summary(filtered)
        col_bar, col_pie = st.columns([1.5, 1])
        with col_bar:
            render_horizontal_bar_chart(filtered)
        with col_pie:
            render_pie_chart(filtered)

    return
