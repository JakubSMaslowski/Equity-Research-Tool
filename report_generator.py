# report_generator.py
# Generates a structured equity research draft from cleaned company data.
# All logic is rule-based and deterministic — no LLM or AI is used.
# Every function is named, inspectable, and easy to modify.

from datetime import date


# =============================================================================
# RULE BLOCK 1: Data Quality Assessment
# =============================================================================

# These are the fields we consider "important" for a meaningful analysis.
# If too many are missing, we flag that the report is limited.
IMPORTANT_FIELDS = [
    "description",
    "sector",
    "industry",
    "revenue",
    "operating_margin",
    "trailing_pe",
]


def assess_data_quality(data: dict) -> dict:
    """
    Checks which important fields are missing and returns a quality summary.

    Rules:
    - Count how many of the important fields are "Not available"
    - If 4 or more are missing: coverage is "poor"
    - If 2-3 are missing: coverage is "partial"
    - If 0-1 are missing: coverage is "good"
    - Missing data is NEVER treated as a negative signal about the company.
      It simply limits the depth of analysis we can produce.

    Returns a dict with:
      "missing"  -> list of field names that are missing
      "coverage" -> "good" / "partial" / "poor"
      "note"     -> plain-English sentence for the report header
    """
    missing = [field for field in IMPORTANT_FIELDS if data.get(field) == "Not available"]
    count = len(missing)

    if count >= 4:
        coverage = "poor"
        note = (
            "Data coverage for this ticker is limited. "
            f"{count} of {len(IMPORTANT_FIELDS)} key fields are unavailable from Yahoo Finance. "
            "Sections below will reflect this constraint. "
            "This should not be interpreted as a negative signal about the company — "
            "it reflects the limits of the public data source."
        )
    elif count >= 2:
        coverage = "partial"
        note = (
            f"{count} of {len(IMPORTANT_FIELDS)} key fields are unavailable ({', '.join(missing)}). "
            "Some sections of this report will be more limited than others."
        )
    else:
        coverage = "good"
        note = "Data coverage is sufficient for a first-pass analysis."

    return {"missing": missing, "coverage": coverage, "note": note}


# =============================================================================
# RULE BLOCK 2: Valuation Risk Assessment
# =============================================================================

# Simple PE thresholds. These are deliberately transparent and easy to change.
PE_HIGH_THRESHOLD = 30       # Above this: possible overvaluation / multiple compression risk
PE_MODERATE_HIGH = 20        # Above this: moderately elevated
PE_LOW_THRESHOLD = 10        # Below this: possibly cheap, but may reflect structural problems


def assess_valuation_risk(data: dict) -> str:
    """
    Produces a cautious valuation comment based on trailing P/E ratio.

    Rules:
    - PE not available: say so explicitly, do not guess
    - PE > 30:  flag elevated valuation, sensitivity to earnings misses
    - PE 20-30: moderately elevated, note dependence on growth delivery
    - PE 10-20: within a typical range, limited signal without peer context
    - PE < 10:  flag possible value opportunity OR value trap
    - All language is restrained. We are not making a buy/sell call.
    """
    pe_str = data.get("trailing_pe", "Not available")

    if pe_str == "Not available":
        return (
            "Trailing P/E is not available for this company. "
            "Valuation assessment is therefore limited. "
            "Investors would need to source earnings data from filings or a financial data provider "
            "to form a view on valuation."
        )

    # Strip the "x" suffix we added during formatting (e.g. "24.50x" -> 24.50)
    try:
        pe_val = float(pe_str.replace("x", ""))
    except ValueError:
        return "Trailing P/E could not be parsed. Valuation assessment is limited."

    if pe_val > PE_HIGH_THRESHOLD:
        return (
            f"The trailing P/E of {pe_str} is above {PE_HIGH_THRESHOLD}x, which is elevated relative to broad market averages. "
            "This implies the market is pricing in continued strong earnings growth. "
            "If growth disappoints or interest rates rise, the multiple could compress materially. "
            "This is a risk factor worth monitoring, though it does not in itself indicate overvaluation "
            "without understanding the company's growth profile and sector context."
        )
    elif pe_val > PE_MODERATE_HIGH:
        return (
            f"The trailing P/E of {pe_str} is moderately elevated (above {PE_MODERATE_HIGH}x). "
            "The current valuation implies some expectation of earnings growth. "
            "Investors should assess whether forward earnings estimates are realistic "
            "and how sensitive the valuation is to a slowdown in growth."
        )
    elif pe_val >= PE_LOW_THRESHOLD:
        return (
            f"The trailing P/E of {pe_str} sits within a broadly typical range. "
            "On its own this is a limited signal — peer comparison and forward earnings context "
            "would be needed to form a stronger view on relative valuation."
        )
    else:
        return (
            f"The trailing P/E of {pe_str} is low (below {PE_LOW_THRESHOLD}x). "
            "This could reflect genuine undervaluation, or it may indicate "
            "structural challenges, earnings risk, or sector-wide de-rating. "
            "A low P/E should be investigated further rather than assumed to be a buying opportunity."
        )


# =============================================================================
# RULE BLOCK 3: Sector / Industry Risk Mapping
# =============================================================================

# Maps sector names (as returned by Yahoo Finance) to relevant risk themes.
# Each entry is a list of (risk_label, risk_description) tuples.
# Easy to extend: add a new sector key and list.
SECTOR_RISK_MAP = {
    "Energy": [
        ("Commodity price risk",
         "Revenue and earnings are materially exposed to oil, gas, or energy price movements. "
         "These prices are cyclical and difficult to forecast with confidence."),
        ("Energy transition risk",
         "Long-term structural shift toward lower-carbon energy sources may affect demand "
         "for fossil fuel products over time."),
    ],
    "Materials": [
        ("Commodity cycle risk",
         "Materials companies are sensitive to global demand cycles and raw material price volatility. "
         "Margins can contract sharply during downturns."),
        ("Capital intensity risk",
         "Mining and materials businesses often require large ongoing capital expenditure, "
         "which can constrain free cash flow even in periods of strong earnings."),
    ],
    "Financial Services": [
        ("Credit risk",
         "Financial companies are exposed to borrower default rates, which rise during economic contractions."),
        ("Interest rate sensitivity",
         "Net interest margins and asset valuations can shift materially with interest rate changes."),
        ("Regulatory risk",
         "Banks and financial intermediaries operate under significant regulatory oversight. "
         "Capital requirements and conduct rules are subject to change."),
    ],
    "Consumer Cyclical": [
        ("Demand cyclicality",
         "Consumer discretionary spending is sensitive to economic conditions. "
         "Revenues tend to contract during recessions as consumers reduce non-essential spending."),
        ("Input cost pressure",
         "Retailers and consumer goods companies can face margin compression "
         "when input costs (labour, logistics, raw materials) rise faster than pricing power allows."),
    ],
    "Real Estate": [
        ("Interest rate sensitivity",
         "Property valuations and financing costs are closely linked to interest rates. "
         "Rising rates can compress capitalisation rates and increase debt service costs."),
        ("Liquidity risk",
         "Real estate assets are illiquid. Forced selling in a downturn can result in "
         "significant value destruction."),
    ],
    "Healthcare": [
        ("Regulatory and approval risk",
         "Drug approvals, pricing negotiations, and reimbursement decisions by regulators and payers "
         "can have an outsized impact on revenues."),
        ("Patent cliff risk",
         "Revenue streams tied to specific drug patents can decline sharply when exclusivity expires "
         "and generic competition enters."),
    ],
    "Technology": [
        ("Competitive disruption risk",
         "Technology markets evolve rapidly. Products or platforms that are dominant today "
         "may face disruption from new entrants or technological shifts."),
        ("Valuation sensitivity",
         "Technology stocks often trade on growth expectations. A moderation in growth "
         "or rise in discount rates can significantly affect the multiple."),
    ],
    "Utilities": [
        ("Regulatory risk",
         "Utility returns are typically regulated. Adverse regulatory decisions on "
         "allowed returns or capital expenditure can constrain profitability."),
        ("Capital intensity risk",
         "Infrastructure businesses require significant ongoing investment, "
         "which may limit free cash flow available for distributions."),
    ],
    "Industrials": [
        ("Economic cycle exposure",
         "Industrial demand is often tied to broader economic activity. "
         "Orders and revenues can fall materially during slowdowns."),
        ("Supply chain risk",
         "Manufacturing businesses are exposed to input cost volatility and "
         "supply chain disruptions, as seen in recent global events."),
    ],
    "Communication Services": [
        ("Subscriber churn risk",
         "Media and telecommunications companies are exposed to subscriber loss "
         "if content quality, pricing, or service quality falls behind competitors."),
        ("Platform disruption risk",
         "Shifts in how consumers consume content or communicate can erode "
         "incumbents' positions over relatively short periods."),
    ],
    "Consumer Defensive": [
        ("Thin margin risk",
         "Staples companies often operate on low margins. Input cost inflation "
         "can quickly compress profitability if pricing power is insufficient."),
        ("Private label competition",
         "Branded consumer goods face ongoing competition from lower-cost private label alternatives, "
         "particularly during periods of consumer financial stress."),
    ],
}

# More specific industry-level risk additions (on top of sector risks)
INDUSTRY_RISK_ADDITIONS = {
    "Oil & Gas Exploration & Production": (
        "Reserve replacement risk",
        "E&P companies must continually replace depleted reserves. "
        "Reserve estimates carry inherent geological uncertainty."
    ),
    "Banks—Regional": (
        "Loan book concentration risk",
        "Regional banks may have geographic or sector loan book concentrations "
        "that amplify losses in localised downturns."
    ),
    "Biotechnology": (
        "Binary clinical trial risk",
        "Biotech companies may depend heavily on a small number of pipeline assets. "
        "A failed trial can result in significant and rapid value destruction."
    ),
    "Airlines": (
        "Operating leverage risk",
        "Airlines carry high fixed costs. A modest fall in passenger volumes "
        "can result in disproportionately large earnings declines."
    ),
}


def assess_sector_risks(data: dict) -> str:
    """
    Looks up the company's sector and industry in the maps above
    and returns a formatted, numbered risk list.

    Rules:
    - If sector is in SECTOR_RISK_MAP: include those risks
    - If industry is in INDUSTRY_RISK_ADDITIONS: include that extra risk
    - Always add valuation risk using assess_valuation_risk()
    - Always add two universal risks (data limitations, concentration)
    - If sector is unknown: say so and flag that sector rules can't be applied
    """
    sector = data.get("sector", "Not available")
    industry = data.get("industry", "Not available")

    risks = []

    # Sector-level risks
    if sector in SECTOR_RISK_MAP:
        for label, description in SECTOR_RISK_MAP[sector]:
            risks.append((label, description))
    elif sector != "Not available":
        risks.append((
            "Sector risk (general)",
            f"The company operates in the '{sector}' sector. "
            "This sector is not in the current risk mapping — "
            "a manual review of sector-specific risks is recommended."
        ))
    else:
        risks.append((
            "Sector data unavailable",
            "No sector information was retrieved. Sector-specific risk assessment cannot be performed."
        ))

    # Industry-level addition (if applicable)
    if industry in INDUSTRY_RISK_ADDITIONS:
        label, description = INDUSTRY_RISK_ADDITIONS[industry]
        risks.append((label, description))

    # Valuation risk (always included, driven by rule block 2)
    risks.append(("Valuation risk", assess_valuation_risk(data)))

    # Universal risks (always appended regardless of sector)
    risks.append((
        "Data and disclosure limitations",
        "This report is based solely on publicly available summary data. "
        "Material risks disclosed in annual filings — including litigation, contingent liabilities, "
        "off-balance-sheet exposures, and related-party transactions — have not been reviewed."
    ))
    risks.append((
        "Concentration risk (unassessed)",
        "Without reviewing segment disclosures, geographic or customer concentration risk "
        "cannot be assessed. This warrants investigation in a full due diligence process."
    ))

    # Format as a numbered list
    formatted = []
    for i, (label, description) in enumerate(risks, 1):
        formatted.append(f"{i}. **{label}:** {description}")

    return "\n\n".join(formatted)


# =============================================================================
# RULE BLOCK 4: Revenue Driver Inference
# =============================================================================

# Sector-level revenue driver descriptions.
# These are intentionally general — we do not fabricate company-specific claims.
SECTOR_REVENUE_DRIVERS = {
    "Energy": (
        "Energy companies typically generate revenue through the extraction, production, "
        "refining, or distribution of oil, gas, or renewable energy. "
        "Volume and commodity price are the primary revenue levers."
    ),
    "Materials": (
        "Materials companies generate revenue through the extraction or processing of raw materials "
        "such as metals, minerals, or chemicals. "
        "Revenue is typically driven by commodity prices and production volumes."
    ),
    "Financial Services": (
        "Financial companies generate revenue through net interest income, fees, commissions, "
        "and trading. Loan growth, deposit spreads, and assets under management are common drivers."
    ),
    "Technology": (
        "Technology companies may generate revenue through software licences, subscription services, "
        "hardware sales, advertising, or platform fees. "
        "Growth is often driven by user acquisition, pricing, and expansion into new markets."
    ),
    "Healthcare": (
        "Healthcare revenue is typically driven by drug sales, medical device volumes, "
        "hospital throughput, or managed care enrolments. "
        "Pricing and reimbursement rates are critical variables."
    ),
    "Consumer Cyclical": (
        "Consumer discretionary companies generate revenue through sales of non-essential goods or services. "
        "Drivers include consumer confidence, pricing, store count or platform growth, and market share."
    ),
    "Consumer Defensive": (
        "Staples companies generate revenue through volume and pricing of everyday consumer products. "
        "Revenue tends to be relatively stable but is sensitive to input costs and pricing power."
    ),
    "Real Estate": (
        "Real estate companies generate revenue through rental income, property sales, or management fees. "
        "Occupancy rates, rental growth, and asset valuations are key drivers."
    ),
    "Utilities": (
        "Utilities generate revenue through regulated or contracted supply of electricity, gas, or water. "
        "Revenue is often relatively predictable but tied to regulatory pricing determinations."
    ),
    "Industrials": (
        "Industrial companies generate revenue through manufacturing, engineering services, logistics, "
        "or infrastructure. Revenue tends to track broader economic and capital expenditure cycles."
    ),
    "Communication Services": (
        "Communication companies generate revenue through subscriptions, advertising, or data services. "
        "Subscriber growth, average revenue per user, and content investment are important drivers."
    ),
}


def infer_revenue_drivers(data: dict) -> str:
    """
    Produces a cautious paragraph about likely revenue drivers.

    Rules:
    - Always start with business description if available (trimmed to 500 chars)
    - If sector is in our map: include the sector-level driver description
    - Show revenue and margin figures if available
    - If both description and sector are missing: explicitly flag limited analysis
    - Never fabricate company-specific claims not supported by the data
    """
    description = data.get("description", "Not available")
    sector = data.get("sector", "Not available")
    revenue = data.get("revenue", "Not available")
    margin = data.get("operating_margin", "Not available")

    lines = []

    # Business description
    if description != "Not available":
        trimmed = description if len(description) <= 500 else description[:500] + "..."
        lines.append(f"**Business description (from Yahoo Finance):**\n\n> {trimmed}")
    else:
        lines.append(
            "_No business description is available. The revenue driver analysis below "
            "relies on sector-level heuristics only._"
        )

    lines.append("")

    # Sector-level driver context
    if sector in SECTOR_REVENUE_DRIVERS:
        lines.append(
            f"**Sector-level revenue driver context ({sector}):**\n\n"
            + SECTOR_REVENUE_DRIVERS[sector]
        )
    elif sector != "Not available":
        lines.append(
            f"The company operates in the '{sector}' sector. "
            "Detailed revenue driver heuristics are not available for this sector in the current mapping. "
            "A review of the company's investor materials is recommended."
        )
    else:
        lines.append(
            "Sector data is unavailable. Revenue driver analysis cannot be supplemented "
            "with sector-level context."
        )

    lines.append("")

    # Financial metrics if available
    metrics = []
    if revenue != "Not available":
        metrics.append(f"- Reported trailing revenue: **{revenue}**")
    if margin != "Not available":
        metrics.append(f"- Reported operating margin: **{margin}**")

    if metrics:
        lines.append("**Available financial metrics:**\n" + "\n".join(metrics))
    else:
        lines.append(
            "_Revenue and margin data are not available. "
            "Financial metric analysis cannot be performed at this stage._"
        )

    lines.append(
        "\n*Note: This section is a first-pass inference based on available data. "
        "A complete analysis would require reviewing segment reporting, management guidance, "
        "and industry research.*"
    )

    return "\n".join(lines)


# =============================================================================
# RULE BLOCK 5: Competitive Positioning
# =============================================================================

def assess_competitive_positioning(data: dict) -> str:
    """
    Produces a restrained comment on competitive positioning.

    Rules:
    - We do NOT claim to know market share or moat quality
    - If operating margin is available, we note it as a partial proxy
    - Margin thresholds: >25% = relatively high, 10-25% = moderate, <10% = thin, <0% = loss-making
    - If data is limited, we say so clearly
    - We list what additional information would be needed for a stronger view
    """
    name = data.get("name", "The company")
    sector = data.get("sector", "Not available")
    industry = data.get("industry", "Not available")
    margin = data.get("operating_margin", "Not available")
    description = data.get("description", "Not available")
    quality = assess_data_quality(data)

    lines = []

    if sector != "Not available" and industry != "Not available":
        lines.append(
            f"{name} operates in the **{industry}** industry within the **{sector}** sector. "
            "Without access to market share data, peer benchmarking, or a structured competitive analysis, "
            "a definitive view on competitive positioning is not possible from this data source alone."
        )
    else:
        lines.append(
            "Sector and industry data are not available for this company. "
            "Competitive positioning cannot be assessed without this information."
        )

    # Margin as a partial proxy for competitive strength
    if margin != "Not available":
        try:
            margin_val = float(margin.replace("%", ""))
            if margin_val > 25:
                lines.append(
                    f"\nThe operating margin of **{margin}** is relatively high. "
                    "Sustained high margins can be an indicator of pricing power, cost advantages, or a degree of competitive insulation. "
                    "This would need to be tested against peer data and assessed for sustainability."
                )
            elif margin_val > 10:
                lines.append(
                    f"\nThe operating margin of **{margin}** is moderate. "
                    "This is neither a strong positive nor a negative signal in isolation — "
                    "sector norms vary significantly and peer benchmarking is needed."
                )
            elif margin_val > 0:
                lines.append(
                    f"\nThe operating margin of **{margin}** is relatively thin. "
                    "This may reflect competitive industry structure, heavy reinvestment, or pricing pressure. "
                    "Further investigation is warranted."
                )
            else:
                lines.append(
                    f"\nThe operating margin of **{margin}** is negative, suggesting the business "
                    "is currently loss-making at the operating level. "
                    "This could reflect an early-stage growth phase or structural challenges."
                )
        except ValueError:
            pass  # If parsing fails, skip this block silently

    if description != "Not available":
        lines.append(
            "\nThe available business description provides qualitative context, "
            "but is not sufficient on its own to support conclusions about market share, "
            "pricing power, or durable competitive advantage."
        )

    lines.append(
        "\n**To form a stronger competitive assessment, the following would be needed:**\n"
        "- Peer revenue and margin comparison\n"
        "- Market share data from industry sources\n"
        "- Review of barriers to entry in the specific sub-industry\n"
        "- Analysis of switching costs and customer concentration\n"
        "- Assessment of the company's own investor presentations and annual report"
    )

    if quality["coverage"] == "poor":
        lines.append(
            "\n_Data coverage for this ticker is poor, which further limits the competitive analysis._"
        )

    return "\n".join(lines)


# =============================================================================
# RULE BLOCK 6: Bull / Bear Case Generation
# =============================================================================

# Sectors where cyclical risk should be flagged in the bear case
CYCLICAL_SECTORS = {"Energy", "Materials", "Consumer Cyclical", "Industrials", "Financial Services"}


def generate_bull_bear_case(data: dict) -> str:
    """
    Generates a short bull case and bear case using rule-based logic.

    Bull case rules:
    - Large market cap (contains "T" or "B"): flag scale as a potential advantage
    - Known sector: note possible sector tailwinds
    - Operating margin > 15%: flag as a profitability positive
    - Revenue available: note established revenue base

    Bear case rules:
    - PE > 20: flag valuation risk
    - PE not available: flag inability to assess valuation
    - Sector in CYCLICAL_SECTORS: flag cyclical earnings risk
    - Operating margin < 8% or negative: flag margin concern
    - Always: flag data limitation risk and forward uncertainty

    All points are cautious and qualified. This is not a buy/sell recommendation.
    """
    name = data.get("name", "The company")
    sector = data.get("sector", "Not available")
    margin = data.get("operating_margin", "Not available")
    pe_str = data.get("trailing_pe", "Not available")
    revenue = data.get("revenue", "Not available")
    market_cap = data.get("market_cap", "Not available")

    bull = []
    bear = []

    # --- BULL CASE ---

    # Scale signal: check if the market cap string suggests a large company
    if market_cap != "Not available":
        if "T" in market_cap:
            bull.append(
                f"Scale and market position: {name} appears to be a very large company by market capitalisation "
                f"({market_cap}), which may imply scale advantages, brand recognition, and financial resilience."
            )
        elif "B" in market_cap:
            bull.append(
                f"Scale: A market capitalisation of {market_cap} suggests meaningful scale, "
                "which may support competitive positioning relative to smaller peers."
            )

    # Sector tailwind (general, non-specific)
    if sector != "Not available":
        bull.append(
            f"Sector exposure: Operating in the {sector} sector may offer structural growth drivers "
            "or defensive characteristics depending on the economic environment. "
            "Sector tailwinds, where present, could support earnings over the medium term."
        )

    # Margin strength
    if margin != "Not available":
        try:
            margin_val = float(margin.replace("%", ""))
            if margin_val > 15:
                bull.append(
                    f"Profitability: An operating margin of {margin} indicates the business generates "
                    "meaningful profit from its operations. "
                    "Sustained margins above 15% can be consistent with competitive advantages, "
                    "though peer context is needed to confirm this."
                )
            elif margin_val > 0:
                bull.append(
                    f"Operating profitability: The business is operationally profitable (margin: {margin}). "
                    "This is a basic positive signal, though the margin level should be benchmarked against sector peers."
                )
        except ValueError:
            pass

    # Established revenue base
    if revenue != "Not available":
        bull.append(
            f"Established revenue base: Reported trailing revenue of {revenue} indicates "
            "the business has meaningful commercial activity, reducing early-stage binary risk."
        )

    # Fallback if no bull points generated
    if not bull:
        bull.append(
            "Insufficient data is available to construct a specific bull case at this stage. "
            "A full analysis with access to financial filings would be required."
        )

    # --- BEAR CASE ---

    # Valuation risk
    if pe_str != "Not available":
        try:
            pe_val = float(pe_str.replace("x", ""))
            if pe_val > PE_HIGH_THRESHOLD:
                bear.append(
                    f"Valuation risk: A trailing P/E of {pe_str} is elevated. "
                    "Any earnings miss or rise in interest rates could result in meaningful multiple compression."
                )
            elif pe_val > PE_MODERATE_HIGH:
                bear.append(
                    f"Valuation sensitivity: A P/E of {pe_str} implies growth is priced in. "
                    "If growth disappoints, downside risk exists."
                )
        except ValueError:
            pass
    else:
        bear.append(
            "Valuation unassessable: Without trailing earnings data, it is not possible "
            "to evaluate whether the current price represents fair value."
        )

    # Cyclicality
    if sector in CYCLICAL_SECTORS:
        bear.append(
            f"Cyclical exposure: The {sector} sector is historically sensitive to economic cycles. "
            "Earnings and valuations can decline materially during downturns."
        )

    # Thin or negative margin
    if margin != "Not available":
        try:
            margin_val = float(margin.replace("%", ""))
            if margin_val < 0:
                bear.append(
                    f"Operating losses: The current operating margin of {margin} is negative. "
                    "If the path to profitability is uncertain or delayed, this increases financial risk."
                )
            elif margin_val < 8:
                bear.append(
                    f"Thin margins: An operating margin of {margin} leaves limited buffer "
                    "against cost increases or revenue softness."
                )
        except ValueError:
            pass

    # Data limitations (always included)
    bear.append(
        "Information risk: This analysis is based on publicly available summary data only. "
        "Material risks in filings — including debt structure, contingent liabilities, and related-party "
        "transactions — have not been reviewed and could alter the investment picture significantly."
    )

    # Forward uncertainty (always included)
    bear.append(
        "Forward uncertainty: No forward earnings estimates, management guidance, or "
        "macroeconomic forecasts have been incorporated into this analysis."
    )

    # Format output
    bull_text = "\n".join(f"- {point}" for point in bull)
    bear_text = "\n".join(f"- {point}" for point in bear)

    return (
        f"### Bull case (preliminary)\n\n{bull_text}\n\n"
        f"### Bear case (preliminary)\n\n{bear_text}\n\n"
        "### Conclusion\n\n"
        f"This is a **first-pass research draft** on {name}. "
        "It is generated from publicly available summary data using transparent, rule-based logic. "
        "It is **not investment advice** and should not be relied upon as such. "
        "The analysis does not substitute for a full due diligence process, review of financial statements, "
        "or consideration of individual investment objectives and risk tolerance."
    )


# =============================================================================
# MAIN REPORT ASSEMBLER
# =============================================================================

def generate_report(data: dict) -> str:
    """
    Assembles all sections into a complete Markdown research memo.
    Each section calls the relevant rule function above.
    The function names make it easy to see where each section comes from.
    """
    today = date.today().strftime("%d %B %Y")

    # Run data quality check once — used in the header and also inside other functions
    quality = assess_data_quality(data)

    report = f"""# Equity Research Draft — {data['name']} ({data['ticker']})

**Date:** {today}
**Exchange:** {data['exchange']}
**Currency:** {data['currency']}

---

*This document is a first-pass research draft generated from publicly available summary data
using rule-based analytical logic. It is not investment advice.*

---

## Data Coverage Note

{quality['note']}

---

## 1. Company Overview

| Field | Value |
|-------|-------|
| **Company Name** | {data['name']} |
| **Ticker** | {data['ticker']} |
| **Sector** | {data['sector']} |
| **Industry** | {data['industry']} |

### Business Description

{data['description'] if data['description'] != 'Not available' else '_No business description available from this data source._'}

---

## 2. Market Snapshot

| Metric | Value |
|--------|-------|
| **Current Price** | {data['price']} |
| **Market Capitalisation** | {data['market_cap']} |
| **52-Week Range** | {data['week_52_range']} |
| **Trailing P/E** | {data['trailing_pe']} |
| **Total Revenue (TTM)** | {data['revenue']} |
| **Operating Margin** | {data['operating_margin']} |

### Valuation Commentary

{assess_valuation_risk(data)}

---

## 3. Business Quality and Revenue Drivers

{infer_revenue_drivers(data)}

---

## 4. Key Risks

{assess_sector_risks(data)}

---

## 5. Competitive Positioning

{assess_competitive_positioning(data)}

---

## 6. Preliminary Investment View

{generate_bull_bear_case(data)}

---

*Report generated using publicly available data from Yahoo Finance via yfinance.
All analytical commentary is rule-based and deterministic. No AI or LLM was used.
All figures should be independently verified before use.*
"""

    return report
