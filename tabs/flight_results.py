"""
Flight Results Tab — dark theme edition
"""

import streamlit as st
from datetime import date
import time
import plotly.graph_objects as go
from data import flights_data, get_probability_color

LOW_RISK_THRESHOLD  = 67
MEDIUM_RISK_THRESHOLD = 33
GREEN  = '#3fb950'
YELLOW = '#d29922'
RED    = '#f85149'
CARD_BG      = '#0d1117'
BORDER_COLOR = '#30363d'


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


def render_flight_card(flight):
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
        st.markdown(f"**{flight['origin']}** → **{flight['destination']}**")
        st.markdown(f"{flight['departure']} – {flight['arrival']} · {flight['duration']}")
        st.caption(f"{flight['stops']}  ·  Status: {flight.get('status','—')}")

    with col3:
        price = flight["price"]
        if price:
            st.markdown(f"<div style='font-size:1.6rem;font-weight:700;color:#58a6ff;font-family:Space Mono,monospace;'>${price}</div>", unsafe_allow_html=True)
        else:
            st.caption("Price N/A")

    with col4:
        if st.button("Select ✈️", key=f"select_{flight['id']}", use_container_width=True):
            st.session_state.selected_flight = flight
            st.session_state.flight_selected = True
            st.toast(f"✅ Selected {flight['airline']} {flight['flight_num']}!", icon="✈️")

    st.markdown(f"<hr style='border:none;height:1px;background:{BORDER_COLOR};margin:12px 0;'/>", unsafe_allow_html=True)


def render_weather_alerts(filtered_flights, all_flights):
    st.markdown("### ⚠️ Weather & Risk Alerts")
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
        st.success("✅ All displayed flights have good on-time probability!")
    st.info("💡 Select a flight and click the **⚠️ Risk Analysis** tab for details.")


def render():
    if not st.session_state.get("search_completed"):
        st.warning("⚠️ Please search for a flight on the Home tab first.")
        return

    st.subheader("Flight Results")
    params = st.session_state.get("search_params", {})
    if params:
        dep = params.get("departure_date")
        dep_str = dep.strftime("%b %d") if hasattr(dep, "strftime") else str(dep)
        st.markdown(f"### {params.get('origin','?')} → {params.get('destination','?')} · {dep_str}")

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

    if risk_filter == "High Risk (0-32%)" and price_filter == "Over $400":
        st.warning("⚠️ High-risk flights rarely exceed $400 — you may get no results with this combination.")

    with st.spinner("🔍 Filtering flights..."):
        source_flights = st.session_state.get("live_flights", flights_data)
        filtered = apply_filters(source_flights, risk_filter, time_filter, price_filter, airline_filter)
        filtered = sort_flights(filtered, sort_by)

    if not filtered:
        st.warning("📭 No flights match your current filters. Try broadening your selections.")
        st.stop()

    st.success(f"✅ Showing {len(filtered)} flight{'s' if len(filtered) != 1 else ''}")

    col_bar, col_pie = st.columns([1.5, 1])
    with col_bar:
        render_horizontal_bar_chart(filtered)
    with col_pie:
        render_pie_chart(filtered)

    st.markdown(f"<hr style='border:none;height:1px;background:{BORDER_COLOR};margin:16px 0;'/>", unsafe_allow_html=True)
    st.markdown("#### Available Flights")
    for flight in filtered:
        render_flight_card(flight)

    render_weather_alerts(filtered, source_flights)

    if st.session_state.get("flight_selected") and st.session_state.get("selected_flight"):
        sel = st.session_state.selected_flight
        st.markdown(f"<hr style='border:none;height:1px;background:{BORDER_COLOR};margin:16px 0;'/>", unsafe_allow_html=True)
        st.success(f"✈️ **{sel['airline']} {sel['flight_num']}** selected! Head to **⚠️ Risk Analysis** for the full breakdown.")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📊 View Risk Analysis →", key="goto_risk", use_container_width=True):
                st.info("Click the **⚠️ Risk Analysis** tab above.")
        with col_b:
            if st.button("🔍 New Search", key="new_search_btn", use_container_width=True):
                st.session_state.search_completed = False
                st.session_state.flight_selected = False
                st.rerun()
