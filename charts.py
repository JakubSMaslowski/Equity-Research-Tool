# charts.py
# Contains the three optional chart functions for the Streamlit UI.
# Each function is self-contained: it fetches its own data and returns
# a matplotlib Figure object, which Streamlit can display with st.pyplot().
#
# Design principle: if a chart can't be built (missing data, bad ticker),
# it returns None and the caller shows a message instead of crashing.

import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def _apply_style(dark_mode: bool = False):
    """Apply shared chart styling, with dark/light mode support."""
    if dark_mode:
        plt.rcParams.update({
            "figure.facecolor": "none",
            "axes.facecolor": "none",
            "axes.grid": True,
            "grid.alpha": 0.22,
            "grid.color": "#666666",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#8A8A8A",
            "xtick.color": "#D8D8D8",
            "ytick.color": "#D8D8D8",
            "axes.labelcolor": "#E0E0E0",
            "text.color": "#E0E0E0",
        })
    else:
        plt.rcParams.update({
            "figure.facecolor": "none",
            "axes.facecolor": "none",
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.color": "#BBBBBB",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#666666",
            "xtick.color": "#333333",
            "ytick.color": "#333333",
            "axes.labelcolor": "#222222",
            "text.color": "#222222",
        })


def _style_axes(ax, dark_mode: bool = False):
    """Apply axis-level styling after plot creation."""
    if dark_mode:
        ax.tick_params(colors="#D8D8D8")
        ax.xaxis.label.set_color("#E0E0E0")
        ax.yaxis.label.set_color("#E0E0E0")
        ax.title.set_color("#EAEAEA")
        ax.spines["bottom"].set_color("#8A8A8A")
        ax.spines["left"].set_color("#8A8A8A")
    else:
        ax.tick_params(colors="#333333")
        ax.xaxis.label.set_color("#222222")
        ax.yaxis.label.set_color("#222222")
        ax.title.set_color("#222222")
        ax.spines["bottom"].set_color("#666666")
        ax.spines["left"].set_color("#666666")


def price_history_chart(ticker: str, period: str = "1y", dark_mode: bool = False) -> plt.Figure | None:
    """
    Downloads daily closing prices for the given ticker and period,
    then returns a line chart as a matplotlib Figure.

    Parameters:
      ticker: stock ticker symbol (e.g. "AAPL")
      period: yfinance period string — "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"

    Returns a Figure, or None if data is unavailable.
    """
    _apply_style(dark_mode)

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
    except Exception:
        return None

    if hist is None or hist.empty or "Close" not in hist.columns:
        return None

    fig, ax = plt.subplots(figsize=(9, 3.5))

    ax.plot(hist.index, hist["Close"], linewidth=1.5, color="#4A90D9")
    ax.fill_between(hist.index, hist["Close"], alpha=0.08, color="#4A90D9")

    ax.set_title(f"{ticker.upper()} — Closing Price ({period})", fontsize=13, pad=10)
    ax.set_ylabel("Price", fontsize=11)
    ax.set_xlabel("")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.2f}"))

    _style_axes(ax, dark_mode)
    fig.tight_layout()
    return fig


def volume_history_chart(ticker: str, period: str = "1y", dark_mode: bool = False) -> plt.Figure | None:
    """
    Downloads daily trading volume for the given ticker and period,
    then returns a bar chart as a matplotlib Figure.

    Returns a Figure, or None if data is unavailable.
    """
    _apply_style(dark_mode)

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
    except Exception:
        return None

    if hist is None or hist.empty or "Volume" not in hist.columns:
        return None

    fig, ax = plt.subplots(figsize=(9, 3))

    ax.bar(hist.index, hist["Volume"], color="#7EC8A0", alpha=0.75, width=1.5)

    ax.set_title(f"{ticker.upper()} — Daily Volume ({period})", fontsize=13, pad=10)
    ax.set_ylabel("Volume", fontsize=11)
    ax.set_xlabel("")

    def volume_formatter(x, _):
        if x >= 1_000_000_000:
            return f"{x / 1_000_000_000:.1f}B"
        elif x >= 1_000_000:
            return f"{x / 1_000_000:.1f}M"
        return f"{x:,.0f}"

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(volume_formatter))

    _style_axes(ax, dark_mode)
    fig.tight_layout()
    return fig


def revenue_trend_chart(ticker: str, dark_mode: bool = False) -> plt.Figure | None:
    """
    Fetches annual revenue (total revenue) from yfinance's financials table
    and returns a bar chart showing the trend over available years.

    Returns a Figure, or None if revenue data is unavailable.
    """
    _apply_style(dark_mode)

    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
    except Exception:
        return None

    if financials is None or financials.empty:
        return None

    if "Total Revenue" not in financials.index:
        return None

    revenue_row = financials.loc["Total Revenue"].dropna()

    if len(revenue_row) < 1:
        return None

    revenue_row = revenue_row.sort_index()

    labels = [str(d.year) for d in revenue_row.index]
    values_bn = revenue_row.values / 1_000_000_000

    fig, ax = plt.subplots(figsize=(9, 3.5))

    bars = ax.bar(labels, values_bn, color="#C07AB8", alpha=0.8, width=0.55)

    for bar, val in zip(bars, values_bn):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values_bn) * 0.015,
            f"${val:.1f}B",
            ha="center",
            va="bottom",
            fontsize=10,
            color="#E0E0E0" if dark_mode else "#222222",
        )

    ax.set_title(f"{ticker.upper()} — Annual Revenue Trend", fontsize=13, pad=10)
    ax.set_ylabel("Revenue (USD Billions)", fontsize=11)
    ax.set_ylim(0, max(values_bn) * 1.2)

    _style_axes(ax, dark_mode)
    fig.tight_layout()
    return fig