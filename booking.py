import html
from urllib.parse import quote_plus

import streamlit as st


AIRLINE_BOOKING_URLS = {
    "united": "https://www.united.com/",
    "american": "https://www.aa.com/",
    "delta": "https://www.delta.com/",
    "southwest": "https://www.southwest.com/",
    "spirit": "https://www.spirit.com/",
    "jetblue": "https://www.jetblue.com/",
    "frontier": "https://www.flyfrontier.com/",
    "alaska": "https://www.alaskaair.com/",
    "sun country": "https://www.suncountry.com/",
}


def get_airline_booking_url(flight):
    if not flight:
        return None

    airline_name = str(flight.get("airline", "")).strip()
    if not airline_name:
        return None

    normalized = airline_name.lower()
    for alias, url in AIRLINE_BOOKING_URLS.items():
        if alias in normalized:
            return url

    query = quote_plus(f"{airline_name} official booking")
    return f"https://www.google.com/search?q={query}"


def render_continue_to_airline(flight, label="Continue to Airline", compact=False):
    if not flight:
        st.caption("Select a flight to unlock the airline booking handoff.")
        return

    airline_name = flight.get("airline", "the airline")
    url = get_airline_booking_url(flight)
    if not url:
        st.caption("Airline booking link unavailable for this flight.")
        return

    button_html = f"""
        <a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer"
           style="text-decoration:none;display:block;width:100%;margin:0 0 0.45rem;color:#ffffff !important;">
            <div style="
                width:100%;
                box-sizing:border-box;
                background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
                color:#ffffff !important;
                border:1px solid rgba(63, 185, 80, 0.38);
                border-radius:12px;
                padding:{'0.7rem 0.9rem' if compact else '0.9rem 1rem'};
                text-align:center;
                font-weight:700;
                font-size:{'0.92rem' if compact else '1rem'};
                box-shadow:0 10px 22px rgba(35, 134, 54, 0.22);
            ">
                {html.escape(label)} ↗
            </div>
        </a>
    """
    st.markdown(button_html, unsafe_allow_html=True)
    st.caption(f"Opens {airline_name}'s site in a new tab so you can complete booking there.")
