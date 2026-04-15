"""
Flight Risk Analysis Tab
========================
Shows detailed risk breakdown for selected flight.
Milestone 3: uses real OpenWeatherMap data for weather cards and
dynamically adjusts the on-time probability based on live conditions.
"""

import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
from data import get_probability_color, flights_data, fetch_airport_weather, compute_weather_adjusted_prob
from navigation import start_view_transition
from booking import render_continue_to_airline
from ui_shell import inject_page_shell_styles, render_page_intro, render_section_intro

GREEN  = '#3fb950'
YELLOW = '#d29922'
RED    = '#f85149'
BG_GREEN  = '#0d2818'
BG_YELLOW = '#2d1f00'
BG_RED    = '#2d0f0f'
TEXT_GREEN  = '#3fb950'
TEXT_YELLOW = '#d29922'
TEXT_RED    = '#f85149'
BORDER_COLOR = '#30363d'
CARD_BG      = '#0d1117'


def get_risk_level(prob):
    if prob >= 67: return "LOW RISK"
    elif prob >= 33: return "MEDIUM RISK"
    return "HIGH RISK"


def get_bar_color(prob):
    if prob >= 67: return GREEN
    elif prob >= 33: return YELLOW
    return RED


def render_flight_header(flight):
    col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
    with col1:
        dep = st.session_state.search_params.get("departure_date", datetime.today()) if st.session_state.get("search_params") else datetime.today()
        st.markdown(f"**{dep.strftime('%b %d') if hasattr(dep,'strftime') else dep}**")
    with col2:
        st.markdown(f"**{flight['airline']} {flight['flight_num']}**")
    with col3:
        st.markdown(f"**{flight['origin']}** → **{flight['destination']}**")
    with col4:
        st.markdown(f"**{flight['departure']} – {flight['arrival']}** · {flight['duration']}")


def render_probability_badge(prob, color, risk_level, is_adjusted=False):
    label = "WEATHER-ADJUSTED PROBABILITY" if is_adjusted else "ON-TIME PROBABILITY"
    note  = "<div style='font-size:11px;opacity:0.7;margin-top:4px;'>adjusted for live weather</div>" if is_adjusted else ""
    st.markdown(f"""
        <div style="background:{color}22;border:2px solid {color};color:{color};
                    padding:15px 25px;border-radius:12px;text-align:center;
                    display:inline-block;margin:15px 0;">
            <div style="font-size:36px;font-weight:700;font-family:'Space Mono',monospace;">{prob}%</div>
            <div style="font-size:12px;opacity:0.9;letter-spacing:1px;">{label} · {risk_level}</div>
            {note}
        </div>""", unsafe_allow_html=True)

def render_recommendation_summary(flight, adjusted_prob):
    source = st.session_state.get("live_flights", flights_data)
    alternatives = sorted(
        [candidate for candidate in source if candidate["id"] != flight["id"]],
        key=lambda x: x["on_time_prob"],
        reverse=True,
    )
    better_option = alternatives[0] if alternatives and alternatives[0]["on_time_prob"] > flight["on_time_prob"] else None

    if adjusted_prob >= 75:
        title = "Good choice"
        bg, border, text = BG_GREEN, TEXT_GREEN, TEXT_GREEN
        message = "This flight currently looks reliable and is a strong option to keep."
    elif adjusted_prob >= 50:
        title = "Proceed with caution"
        bg, border, text = BG_YELLOW, TEXT_YELLOW, TEXT_YELLOW
        message = "This option is workable, but the risk is noticeable enough that a safer alternative may be worth a look."
    else:
        title = "Pick an alternative"
        bg, border, text = BG_RED, TEXT_RED, TEXT_RED
        message = "Current conditions make this a riskier choice than usual."

    if better_option:
        message += (
            f" Better option: {better_option['airline']} {better_option['flight_num']} "
            f"at {better_option['on_time_prob']}% on-time."
        )

    st.markdown(f"""
        <div style="background:{bg};border:1px solid {border}44;border-left:4px solid {border};
                    padding:16px;border-radius:10px;margin:4px 0 16px;">
            <div style="color:{text};font-size:1rem;font-weight:700;margin-bottom:6px;">{title}</div>
            <div style="color:#8b949e;font-size:0.92rem;">{message}</div>
        </div>""", unsafe_allow_html=True)


def render_weather_radar_callout(flight, origin_weather, dest_weather, adjusted_prob):
    base_prob = flight["on_time_prob"]
    weather_impact = max(0, base_prob - adjusted_prob)

    origin_penalty = (
        origin_weather.get("weather_risk_penalty", 0)
        if origin_weather and origin_weather.get("source") not in (None, "unavailable")
        else 0
    )
    dest_penalty = (
        dest_weather.get("weather_risk_penalty", 0)
        if dest_weather and dest_weather.get("source") not in (None, "unavailable")
        else 0
    )

    severe_weather = max(origin_penalty, dest_penalty) >= 20
    emphasize = weather_impact >= 10 or severe_weather

    if emphasize:
        bg = BG_YELLOW
        border = TEXT_YELLOW
        title = "Weather is materially affecting this flight"
        copy = (
            f"Live weather is pulling this flight down by about {weather_impact} points. "
            "Want to inspect live weather conditions around this route? Open Weather Radar."
        )
    else:
        bg = CARD_BG
        border = "#58a6ff"
        title = "Want a closer look at the weather?"
        copy = "Want to inspect live weather conditions around this route? Open Weather Radar."

    card_col, button_col = st.columns([3.2, 1.2])
    with card_col:
        st.markdown(
            f"""
            <div style="background:{bg};border:1px solid {border}44;border-left:4px solid {border};
                        padding:16px;border-radius:10px;margin:0 0 16px;">
                <div style="color:{border};font-size:0.98rem;font-weight:700;margin-bottom:6px;">{title}</div>
                <div style="color:#8b949e;font-size:0.92rem;line-height:1.45;">{copy}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with button_col:
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        if st.button("View Weather Radar", key="view_weather_radar_cta", use_container_width=True):
            start_view_transition("weather", "Opening live weather radar...")


def weather_card(iata, weather, side="origin"):
    """
    Render a weather card. Handles 3 states:
      1. Real data (source = "current" or "forecast") — shows live conditions
      2. Beyond forecast window (source = "unavailable") — explains 5-day limit
      3. None — no API key or unknown airport, shows estimated fallback
    """
    # ── State 2: beyond 5-day forecast window ────────────────────────────────
    if weather and weather.get("source") == "unavailable":
        days_out = weather.get("days_out", "?")
        st.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid {BORDER_COLOR};border-left:4px solid #58a6ff;
                        padding:15px;border-radius:10px;margin-bottom:15px;">
                <h4 style="color:#58a6ff;margin:0 0 8px;">📅 Weather at {iata}</h4>
                <p style="margin:0;color:#8b949e;font-size:13px;">
                    Your flight is <strong style="color:#e6edf3;">{days_out} days away</strong> —
                    forecasts are only available up to 5 days in advance.<br>
                    <em style="font-size:11px;">Check back closer to your departure for live conditions.</em>
                </p>
            </div>""", unsafe_allow_html=True)
        return

    # ── State 1: real weather data ────────────────────────────────────────────
    if weather and weather.get("source") in ("current", "forecast"):
        penalty = weather["weather_risk_penalty"]
        if penalty >= 20:
            bg, border, text = BG_RED,    TEXT_RED,    TEXT_RED
            risk_label = "⚠️ High delay risk"
        elif penalty >= 10:
            bg, border, text = BG_YELLOW, TEXT_YELLOW, TEXT_YELLOW
            risk_label = "⚠️ Moderate delay risk"
        else:
            bg, border, text = BG_GREEN,  TEXT_GREEN,  TEXT_GREEN
            risk_label = "✅ Low delay risk"

        source_label = (
            f"Forecast for {weather.get('forecast_dt', 'departure time')} · OpenWeatherMap"
            if weather["source"] == "forecast"
            else "Current conditions · OpenWeatherMap"
        )

        st.markdown(f"""
            <div style="background:{bg};border:1px solid {border}44;border-left:4px solid {border};
                        padding:15px;border-radius:10px;margin-bottom:15px;">
                <h4 style="color:{text};margin:0 0 10px;">
                    {weather['icon']} {iata} — {weather['description']}
                </h4>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;color:#8b949e;font-size:13px;">
                    <div>🌡️ <strong style="color:#e6edf3;">{weather['temp_f']}°F</strong> (feels {weather['feels_like']}°F)</div>
                    <div>💨 Wind: <strong style="color:#e6edf3;">{weather['wind_mph']} mph</strong></div>
                    <div>👁️ Visibility: <strong style="color:#e6edf3;">{weather['visibility_mi']} mi</strong></div>
                    <div>💧 Humidity: <strong style="color:#e6edf3;">{weather['humidity']}%</strong></div>
                </div>
                <div style="margin-top:10px;font-size:12px;color:{text};font-weight:600;">{risk_label}</div>
                <div style="font-size:11px;color:#8b949e;margin-top:2px;">{source_label}</div>
            </div>""", unsafe_allow_html=True)
        return

    # ── State 3: no API key or unknown airport — estimated fallback ───────────
    st.markdown(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER_COLOR};border-left:4px solid #30363d;
                    padding:15px;border-radius:10px;margin-bottom:15px;">
            <h4 style="color:#8b949e;margin:0 0 8px;">🌤️ Weather at {iata}</h4>
            <p style="margin:0;color:#8b949e;font-size:13px;">Estimated conditions<br>
            <em style="font-size:11px;">Add OPENWEATHER_KEY to secrets.toml for live forecasts</em></p>
        </div>""", unsafe_allow_html=True)


def render_performance_cards(flight, adjusted_prob):
    col1, col2 = st.columns(2)
    delay_pct = 100 - adjusted_prob

    with col1:
        if delay_pct > 50:   bg, border, text = BG_RED,    TEXT_RED,    TEXT_RED
        elif delay_pct > 25: bg, border, text = BG_YELLOW, TEXT_YELLOW, TEXT_YELLOW
        else:                bg, border, text = BG_GREEN,  TEXT_GREEN,  TEXT_GREEN
        st.markdown(f"""
            <div style="background:{bg};border:1px solid {border}44;border-left:4px solid {border};
                        padding:15px;border-radius:10px;margin-bottom:15px;">
                <h4 style="color:{text};margin:0 0 8px;">📊 Historic Route Performance</h4>
                <p style="margin:0;color:#8b949e;font-size:14px;">
                    {flight['origin']} → {flight['destination']} has<br>
                    <strong style="color:{text};">{delay_pct}% estimated delay rate</strong> given current conditions.
                </p>
            </div>""", unsafe_allow_html=True)

    with col2:
        if adjusted_prob < 50:   level, ind, bg, border, text = "High",     "🔴", BG_RED,    TEXT_RED,    TEXT_RED
        elif adjusted_prob < 75: level, ind, bg, border, text = "Moderate", "🟡", BG_YELLOW, TEXT_YELLOW, TEXT_YELLOW
        else:                    level, ind, bg, border, text = "Low",       "🟢", BG_GREEN,  TEXT_GREEN,  TEXT_GREEN
        st.markdown(f"""
            <div style="background:{bg};border:1px solid {border}44;border-left:4px solid {border};
                        padding:15px;border-radius:10px;margin-bottom:15px;">
                <h4 style="color:{text};margin:0 0 8px;">🛫 Airport Congestion</h4>
                <p style="margin:0;color:#8b949e;font-size:14px;">
                    {ind} <strong style="color:{text};">{level} congestion</strong> at {flight['destination']}<br>
                    during your arrival window.
                </p>
            </div>""", unsafe_allow_html=True)


def render_historical_chart(flight, adjusted_prob):
    dates = ["12-09","12-10","12-11","12-12","12-13","12-14","12-15","12-16","12-17","12-18","12-19"]
    probs = [78, 82, 75, 80, 85, 72, 88, adjusted_prob, 94, 91, 89]
    colors = [get_bar_color(p) for p in probs]
    borders = ['rgba(0,0,0,0)'] * len(dates)
    widths  = [0] * len(dates)
    borders[7] = '#58a6ff'
    widths[7]  = 2

    fig = go.Figure(data=[go.Bar(
        x=dates, y=probs,
        marker_color=colors, marker_line_color=borders, marker_line_width=widths,
        text=[f"{p}%" for p in probs], textposition="outside",
        textfont=dict(color="#8b949e", size=11),
    )])
    fig.update_layout(
        plot_bgcolor='#0d1117', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title="Date", color="#8b949e", gridcolor="#21262d", linecolor="#30363d"),
        yaxis=dict(title="On-Time Probability (%)", range=[0, 115], color="#8b949e", gridcolor="#21262d"),
        margin=dict(l=60, r=40, t=30, b=60), height=350,
        font=dict(color="#8b949e"),
    )
    fig.add_annotation(x="12-16", y=adjusted_prob + 10,
                       text="Your Flight", showarrow=True, arrowhead=2,
                       font=dict(color="#58a6ff"), arrowcolor="#58a6ff")

    col1, col2 = st.columns([4, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="risk_history_chart")
    with col2:
        st.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid {BORDER_COLOR};
                        padding:15px;border-radius:10px;margin-top:20px;">
                <p style="font-weight:600;margin-bottom:12px;color:#e6edf3;">Risk Key</p>
                <div style="margin-bottom:8px;color:#8b949e;"><span style="display:inline-block;width:12px;height:12px;background:{GREEN};border-radius:3px;margin-right:6px;"></span><strong style="color:{GREEN};">Low</strong> 68%+</div>
                <div style="margin-bottom:8px;color:#8b949e;"><span style="display:inline-block;width:12px;height:12px;background:{YELLOW};border-radius:3px;margin-right:6px;"></span><strong style="color:{YELLOW};">Med</strong> 33-67%</div>
                <div style="color:#8b949e;"><span style="display:inline-block;width:12px;height:12px;background:{RED};border-radius:3px;margin-right:6px;"></span><strong style="color:{RED};">High</strong> 0-32%</div>
            </div>""", unsafe_allow_html=True)


def render_alternatives(flight, adjusted_prob):
    source = st.session_state.get("live_flights", flights_data)
    better = sorted(
        [f for f in source if f["on_time_prob"] > flight["on_time_prob"] and f["id"] != flight["id"]],
        key=lambda x: x["on_time_prob"], reverse=True
    )[:3]

    if better:
        for alt in better:
            color, _ = get_probability_color(alt["on_time_prob"])
            st.markdown(f"""
                <div style="background:{CARD_BG};border:1px solid {BORDER_COLOR};border-left:4px solid {color};
                            padding:12px 15px;border-radius:10px;margin-bottom:10px;
                            display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <strong style="color:#e6edf3;">{alt['airline']} {alt['flight_num']}</strong>
                        <span style="color:#8b949e;margin-left:8px;">{alt['departure']} – {alt['arrival']}</span>
                    </div>
                    <span style="background:{color}22;color:{color};border:1px solid {color}66;
                                 padding:4px 12px;border-radius:20px;font-weight:700;font-size:0.9rem;">
                        {alt['on_time_prob']}%
                    </span>
                </div>""", unsafe_allow_html=True)
    else:
        st.success("✅ You've selected one of the best options available!")


def render_risk_navigation():
    can_view_results = st.session_state.get("search_completed", False)
    can_view_weather = st.session_state.get("selected_flight") is not None

    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1.15, 1.15, 1.15, 3.55])
    with nav_col1:
        if st.button("Back to Home", key="risk_back_home", use_container_width=True):
            start_view_transition(
                "home",
                "Returning you to the search page...",
                action="reset_search_state",
            )
    with nav_col2:
        if st.button(
            "Back to Results",
            key="risk_back_results",
            use_container_width=True,
            disabled=not can_view_results,
        ):
            start_view_transition("results", "Returning to your flight options...")
    with nav_col3:
        if st.button(
            "Weather Radar",
            key="risk_to_weather_top",
            use_container_width=True,
            disabled=not can_view_weather,
        ):
            start_view_transition("weather", "Opening live weather radar...")
    with nav_col4:
        if can_view_results:
            st.caption("Use Home for a new route, Results to compare alternatives, and Weather Radar for live conditions.")
        else:
            st.caption("Use Home for a new route. Results and Weather Radar unlock as you move through the trip flow.")


def render():
    inject_page_shell_styles()
    render_risk_navigation()

    if not st.session_state.get("selected_flight"):
        st.warning("⚠️ Please select a flight on the Flight Results page first.")
        return

    flight = st.session_state.selected_flight

    # Pull departure date and time from search params for forecast matching
    params      = st.session_state.get("search_params", {})
    dep_date    = params.get("departure_date", None)
    dep_time    = flight.get("departure", None)  # e.g. "9:15 AM"

    # Fetch weather — uses forecast endpoint for trips within 5 days,
    # current weather for today, "unavailable" sentinel beyond 5 days
    with st.status("🔍 Building risk analysis...", expanded=False) as status:
        st.write("Fetching weather forecast at origin...")
        origin_weather = fetch_airport_weather(flight["origin"], dep_date, dep_time)
        st.write("Fetching weather forecast at destination...")
        dest_weather   = fetch_airport_weather(flight["destination"], dep_date, dep_time)
        st.write("Computing weather-adjusted risk score...")
        adjusted_prob  = compute_weather_adjusted_prob(
            flight["on_time_prob"], origin_weather, dest_weather
        )
        status.update(label="✅ Analysis ready!", state="complete", expanded=False)

    prob_color, _ = get_probability_color(adjusted_prob)
    risk_level = get_risk_level(adjusted_prob)
    is_adjusted = (origin_weather is not None or dest_weather is not None)
    dep_label = dep_date.strftime("%b %d") if hasattr(dep_date, "strftime") else "Upcoming trip"
    render_page_intro(
        "Risk Analysis",
        f"{flight['airline']} {flight['flight_num']}",
        f"{flight['origin']} → {flight['destination']} · {flight['departure']} – {flight['arrival']} · {flight['duration']}",
        [dep_label, f"{adjusted_prob}% adjusted", risk_level.title()],
    )
    render_probability_badge(adjusted_prob, prob_color, risk_level, is_adjusted)
    render_recommendation_summary(flight, adjusted_prob)
    render_continue_to_airline(flight)
    render_weather_radar_callout(flight, origin_weather, dest_weather, adjusted_prob)

    # Show what changed if weather affected the score
    if is_adjusted and adjusted_prob != flight["on_time_prob"]:
        delta = adjusted_prob - flight["on_time_prob"]
        sign  = "+" if delta > 0 else ""
        color = TEXT_GREEN if delta > 0 else TEXT_RED
        st.markdown(f"""
            <div style="display:inline-block;background:{CARD_BG};border:1px solid {BORDER_COLOR};
                        padding:6px 14px;border-radius:20px;font-size:13px;margin-bottom:12px;">
                Base estimate: <strong style="color:#e6edf3;">{flight['on_time_prob']}%</strong>
                &nbsp;→&nbsp;
                Weather adjustment: <strong style="color:{color};">{sign}{delta} pts</strong>
            </div>""", unsafe_allow_html=True)

    render_section_intro("Why this score moved", "Weather and route conditions that are shaping this flight right now.")
    col1, col2 = st.columns(2)
    with col1:
        weather_card(flight["origin"], origin_weather, side="origin")
    with col2:
        weather_card(flight["destination"], dest_weather, side="dest")

    render_performance_cards(flight, adjusted_prob)
    render_section_intro("Historical context", "See how this flight compares with the recent reliability window.")
    render_historical_chart(flight, adjusted_prob)
    render_section_intro("Lower-risk alternatives", "If you want a safer option, these are the first flights to check.")
    render_alternatives(flight, adjusted_prob)
