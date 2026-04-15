import html

import streamlit as st


PAGE_SHELL_CSS = """
<style>
.page-shell-card {
    background: linear-gradient(180deg, rgba(18, 26, 38, 0.96) 0%, rgba(13, 17, 23, 0.98) 100%);
    border: 1px solid rgba(121, 192, 255, 0.16);
    border-radius: 20px;
    padding: 1.2rem 1.35rem;
    box-shadow: 0 18px 36px rgba(0, 0, 0, 0.22);
    margin-bottom: 1rem;
}

.page-shell-eyebrow {
    color: #79c0ff;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 0.45rem;
}

.page-shell-title {
    color: #f0f6fc;
    font-size: 1.55rem;
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 0.35rem;
}

.page-shell-subtitle {
    color: #8b949e;
    font-size: 0.94rem;
    line-height: 1.5;
    max-width: 760px;
}

.page-shell-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 0.95rem;
}

.page-shell-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.42rem 0.72rem;
    border-radius: 999px;
    background: rgba(13, 17, 23, 0.72);
    border: 1px solid #30363d;
    color: #c9d1d9;
    font-size: 0.82rem;
    font-weight: 600;
}

.page-shell-section-title {
    color: #f0f6fc;
    font-size: 1.05rem;
    font-weight: 700;
    margin: 0.1rem 0 0.2rem;
}

.page-shell-section-copy {
    color: #8b949e;
    font-size: 0.9rem;
    margin-bottom: 0.75rem;
}

.page-shell-inline-card {
    background: rgba(13, 17, 23, 0.62);
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 0.95rem 1rem;
    margin-bottom: 1rem;
}

.page-shell-inline-title {
    color: #f0f6fc;
    font-size: 0.98rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.page-shell-inline-copy {
    color: #8b949e;
    font-size: 0.89rem;
    line-height: 1.45;
}
</style>
"""


def inject_page_shell_styles():
    st.markdown(PAGE_SHELL_CSS, unsafe_allow_html=True)


def render_page_intro(eyebrow, title, subtitle="", chips=None):
    chips = chips or []
    chips_html = "".join(
        f"<span class='page-shell-chip'>{html.escape(str(chip))}</span>"
        for chip in chips
        if chip
    )
    st.markdown(
        f"""
        <div class="page-shell-card">
            <div class="page-shell-eyebrow">{html.escape(str(eyebrow))}</div>
            <div class="page-shell-title">{html.escape(str(title))}</div>
            <div class="page-shell-subtitle">{html.escape(str(subtitle))}</div>
            {"<div class='page-shell-chip-row'>" + chips_html + "</div>" if chips_html else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_intro(title, subtitle=""):
    st.markdown(
        f"""
        <div class="page-shell-section-title">{html.escape(str(title))}</div>
        {"<div class='page-shell-section-copy'>" + html.escape(str(subtitle)) + "</div>" if subtitle else ""}
        """,
        unsafe_allow_html=True,
    )


def render_inline_summary(title, copy):
    st.markdown(
        f"""
        <div class="page-shell-inline-card">
            <div class="page-shell-inline-title">{html.escape(str(title))}</div>
            <div class="page-shell-inline-copy">{html.escape(str(copy))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
