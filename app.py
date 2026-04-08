# app.py
# The Streamlit UI for the equity research report generator.
# Run with: streamlit run app.py
#
# This file is a thin shell. It handles layout, user input, and display.
# All the real work happens in data_fetcher.py, report_generator.py, and charts.py.
# Those files are not modified at all.

import os
import streamlit as st

from data_fetcher import fetch_company_data
from report_generator import generate_report
from charts import price_history_chart, volume_history_chart, revenue_trend_chart

# =============================================================================
# PAGE CONFIG
# Must be the very first Streamlit call in the file.
# =============================================================================

st.set_page_config(
    page_title="Equity Research Draft Generator",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# DARK / LIGHT MODE STYLES
# =============================================================================

LIGHT_CSS = """
<style>
    .stApp { background-color: #F7F7F7; }
    .report-box {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 1.5rem 2rem;
        font-family: Georgia, serif;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #1A1A1A;
    }
    .section-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #888888;
        margin-bottom: 0.25rem;
    }
</style>
"""

DARK_CSS = """
<style>
    .stApp {
        background-color: #1E1E1E !important;
        color: #E0E0E0 !important;
    }

    .stApp, .stMarkdown, .stText, p, label, span, div {
        color: #E0E0E0;
    }

    div[data-baseweb="input"] {
        background-color: #2C2C2C !important;
        border: 1px solid #444444 !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="input"] input {
        background-color: #2C2C2C !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #FFFFFF !important;
    }

    div[data-baseweb="input"] input::placeholder {
        color: #A8A8A8 !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #A8A8A8 !important;
    }

    div[data-baseweb="input"]:focus-within {
        border: 1px solid #B85C3A !important;
        box-shadow: 0 0 0 1px #B85C3A !important;
    }

    .report-box {
        background-color: #2C2C2C;
        border: 1px solid #3C3C3C;
        border-radius: 8px;
        padding: 1.5rem 2rem;
        font-family: Georgia, serif;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #DCDCDC;
    }

    .section-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #9A9A9A !important;
        margin-bottom: 0.25rem;
    }

    .stDataFrame, table {
        background-color: #2C2C2C !important;
        color: #E0E0E0 !important;
    }

    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] span {
        color: #E0E0E0 !important;
    }

    div[data-testid="stSelectSlider"] label,
    div[data-testid="stSelectSlider"] span {
        color: #E0E0E0 !important;
    }

    div[data-testid="stSelectSlider"] div[data-baseweb="slider"] > div > div {
        background: #5B3428 !important;
    }

    div[data-testid="stSelectSlider"] div[data-baseweb="slider"] [role="slider"] ~ div {
        background: #B85C3A !important;
    }

    div[data-testid="stSelectSlider"] div[data-baseweb="slider"] [role="slider"] {
        background-color: #D06A45 !important;
        border: 2px solid #D06A45 !important;
        box-shadow: none !important;
    }

    div[data-testid="stSelectSlider"] div[data-baseweb="slider"] span {
        color: #CFCFCF !important;
    }
</style>
"""

# =============================================================================
# SESSION STATE
# =============================================================================

if "report_text" not in st.session_state:
    st.session_state.report_text = None
if "company_data" not in st.session_state:
    st.session_state.company_data = None
if "last_ticker" not in st.session_state:
    st.session_state.last_ticker = ""

# =============================================================================
# HEADER
# =============================================================================

header_col1, header_col2 = st.columns([6, 1])
with header_col1:
    st.title("📋 Equity Research Draft Generator")
    st.caption(
        "Enter a stock ticker to generate a structured first-pass equity research memo. "
        "This tool uses publicly available data and rule-based logic only — no AI or LLM."
    )
with header_col2:
    dark_mode = st.toggle("🌙", value=False, help="Toggle dark mode")

st.markdown(DARK_CSS if dark_mode else LIGHT_CSS, unsafe_allow_html=True)

# =============================================================================
# INPUT AREA
# =============================================================================

st.markdown("---")

input_col, button_col = st.columns([3, 1])

with input_col:
    ticker_input = st.text_input(
        label="Ticker symbol",
        placeholder="e.g. AAPL, MSFT, BHP.AX, CBA.AX",
        label_visibility="collapsed",
    )

with button_col:
    generate_btn = st.button("Generate report", use_container_width=True, type="primary")

# =============================================================================
# CHART SELECTION
# =============================================================================

st.markdown('<p class="section-label">Optional charts</p>', unsafe_allow_html=True)

chart_col1, chart_col2, chart_col3 = st.columns(3)
with chart_col1:
    show_price = st.checkbox("Price history", value=True)
with chart_col2:
    show_volume = st.checkbox("Volume history", value=False)
with chart_col3:
    show_revenue = st.checkbox("Revenue trend", value=False)

if show_price or show_volume:
    period_options = {
        "1 month": "1mo",
        "3 months": "3mo",
        "6 months": "6mo",
        "1 year": "1y",
        "2 years": "2y",
        "5 years": "5y",
        "10 years": "10y",
        "Max": "max",
    }
    selected_period_label = st.select_slider(
        "Chart time period",
        options=list(period_options.keys()),
        value="1 year",
        label_visibility="visible",
    )
    selected_period = period_options[selected_period_label]
else:
    selected_period = "1y"

st.markdown("---")

# =============================================================================
# REPORT GENERATION LOGIC
# =============================================================================

if generate_btn:
    ticker = ticker_input.strip().upper()

    if not ticker:
        st.warning("Please enter a ticker symbol before generating a report.")
    else:
        with st.spinner(f"Fetching data for {ticker}..."):
            data = fetch_company_data(ticker)

        if not data:
            st.error(
                f"Could not retrieve data for **{ticker}**. "
                "Please check the ticker symbol and your internet connection. "
                "Australian stocks need the `.AX` suffix (e.g. `BHP.AX`)."
            )
            st.session_state.report_text = None
            st.session_state.company_data = None
            st.session_state.last_ticker = ""
        else:
            report = generate_report(data)

            st.session_state.report_text = report
            st.session_state.company_data = data
            st.session_state.last_ticker = ticker

            os.makedirs("outputs", exist_ok=True)
            filename = f"outputs/{ticker}_research_draft.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)

            st.success(f"Report generated and saved to `{filename}`")

# =============================================================================
# CHART DISPLAY
# =============================================================================

if st.session_state.last_ticker and (show_price or show_volume or show_revenue):
    ticker = st.session_state.last_ticker

    if show_price:
        st.markdown('<p class="section-label">Price history</p>', unsafe_allow_html=True)
        try:
            fig = price_history_chart(ticker, period=selected_period, dark_mode=dark_mode)
            if fig:
                st.pyplot(fig, use_container_width=True)
            else:
                st.info("Price history data is not available for this ticker.")
        except Exception as e:
            st.warning(f"Could not render price chart: {e}")

    if show_volume:
        st.markdown('<p class="section-label">Volume history</p>', unsafe_allow_html=True)
        try:
            fig = volume_history_chart(ticker, period=selected_period, dark_mode=dark_mode)
            if fig:
                st.pyplot(fig, use_container_width=True)
            else:
                st.info("Volume history data is not available for this ticker.")
        except Exception as e:
            st.warning(f"Could not render volume chart: {e}")

    if show_revenue:
        st.markdown('<p class="section-label">Revenue trend</p>', unsafe_allow_html=True)
        try:
            fig = revenue_trend_chart(ticker, dark_mode=dark_mode)
            if fig:
                st.pyplot(fig, use_container_width=True)
            else:
                st.info(
                    "Annual revenue data is not available for this ticker from Yahoo Finance. "
                    "This is common for non-US stocks, ETFs, and smaller companies."
                )
        except Exception as e:
            st.warning(f"Could not render revenue chart: {e}")

# =============================================================================
# REPORT DISPLAY
# =============================================================================

if st.session_state.report_text:
    st.markdown("## Research report")

    with st.container():
        st.markdown(
            f'<div class="report-box">{st.session_state.report_text}</div>',
            unsafe_allow_html=True,
        )

    st.download_button(
        label="⬇ Download report as Markdown",
        data=st.session_state.report_text,
        file_name=f"{st.session_state.last_ticker}_research_draft.md",
        mime="text/markdown",
    )

else:
    st.markdown(
        """
        <div style="text-align: center; padding: 3rem 1rem; color: #999999;">
            <p style="font-size: 1.1rem;">Enter a ticker and click <strong>Generate report</strong> to begin.</p>
            <p style="font-size: 0.85rem;">
                Examples: <code>AAPL</code> &nbsp;|&nbsp; <code>MSFT</code> &nbsp;|&nbsp;
                <code>BHP.AX</code> &nbsp;|&nbsp; <code>CBA.AX</code>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption(
    "Data sourced from Yahoo Finance via yfinance. "
    "All analysis is rule-based and deterministic. Not investment advice."
)