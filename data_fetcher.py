# data_fetcher.py
# This file is responsible for connecting to Yahoo Finance and pulling company data.
# It uses the yfinance library, which wraps Yahoo Finance's public data.

import yfinance as yf


def fetch_company_data(ticker: str) -> dict:
    """
    Given a ticker symbol (e.g. "AAPL" or "BHP.AX"), fetch a small set of
    company fundamentals and return them as a plain Python dictionary.

    If a field is missing from Yahoo Finance, we store "Not available" instead
    of crashing the program.
    """

    # Create a Ticker object — this doesn't make a network call yet
    stock = yf.Ticker(ticker)

    # .info is a dictionary with hundreds of possible fields.
    # The call happens here. It can fail if Yahoo Finance is down or the ticker is wrong.
    try:
        info = stock.info
    except Exception as e:
        print(f"\n[ERROR] Could not fetch data for '{ticker}'. "
              f"Check the ticker symbol and your internet connection.\nDetails: {e}")
        return {}

    # A small helper so we never crash on a missing key
    def get(key):
        value = info.get(key)
        if value is None or value == "" or value == "None":
            return "Not available"
        return value

    # Format market cap as a readable string (e.g. "$2.5T" or "$340B")
    raw_market_cap = info.get("marketCap")
    if raw_market_cap is None:
        market_cap_str = "Not available"
    elif raw_market_cap >= 1_000_000_000_000:
        market_cap_str = f"${raw_market_cap / 1_000_000_000_000:.2f}T"
    elif raw_market_cap >= 1_000_000_000:
        market_cap_str = f"${raw_market_cap / 1_000_000_000:.2f}B"
    elif raw_market_cap >= 1_000_000:
        market_cap_str = f"${raw_market_cap / 1_000_000:.2f}M"
    else:
        market_cap_str = f"${raw_market_cap:,}"

    # Format revenue similarly
    raw_revenue = info.get("totalRevenue")
    if raw_revenue is None:
        revenue_str = "Not available"
    elif raw_revenue >= 1_000_000_000_000:
        revenue_str = f"${raw_revenue / 1_000_000_000_000:.2f}T"
    elif raw_revenue >= 1_000_000_000:
        revenue_str = f"${raw_revenue / 1_000_000_000:.2f}B"
    elif raw_revenue >= 1_000_000:
        revenue_str = f"${raw_revenue / 1_000_000:.2f}M"
    else:
        revenue_str = f"${raw_revenue:,}" if raw_revenue else "Not available"

    # Format trailing PE to 2 decimal places if available
    raw_pe = info.get("trailingPE")
    pe_str = f"{raw_pe:.2f}x" if raw_pe else "Not available"

    # Format operating margin as a percentage
    raw_margin = info.get("operatingMargins")
    margin_str = f"{raw_margin * 100:.1f}%" if raw_margin else "Not available"

    # Format 52-week range
    low_52 = info.get("fiftyTwoWeekLow")
    high_52 = info.get("fiftyTwoWeekHigh")
    if low_52 and high_52:
        week_range = f"${low_52:.2f} – ${high_52:.2f}"
    else:
        week_range = "Not available"

    # Format current price
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    price_str = f"${price:.2f}" if price else "Not available"

    # Build the final clean data dictionary
    data = {
        "ticker": ticker.upper(),
        "name": get("longName"),
        "sector": get("sector"),
        "industry": get("industry"),
        "description": get("longBusinessSummary"),
        "price": price_str,
        "market_cap": market_cap_str,
        "week_52_range": week_range,
        "trailing_pe": pe_str,
        "revenue": revenue_str,
        "operating_margin": margin_str,
        "currency": get("currency"),
        "exchange": get("exchange"),
    }

    return data
