# Equity Research Draft Generator
A lightweight Python tool that generates structured equity research drafts using publicly available financial data from Yahoo Finance.

This project focuses on automating data collection and structuring, allowing users to spend more time on higher-value analysis rather than manual data gathering.

## Demo
![App Screenshot](assets/demo.png)

## Overview
This tool takes a stock ticker (e.g. AAPL, BHP.AX) and produces a first-pass equity research report including:
- Market snapshot (price, market cap, valuation metrics)
- Business description and segmentation
- Revenue and margin data
- Structured commentary to guide further analysis
It also includes optional interactive charts via a simple Streamlit interface.

# Features
- Ticker-based report generation using yfinance
- Clean, structured Markdown output
- Interactive UI built with Streamlit
- Optional charts:
  - Price history
  - Volume history
  - Revenue trend (where available)
  - Adjustable time horizons (1 month → max history)
- Dark/light mode toggle with custom styling

# Tech Stack
- Python
- Streamlit
- yfinance
- matplotlib

# How It Works
1. User inputs a ticker symbol
2. The app fetches financial and company data from Yahoo Finance
3. Data is processed and formatted into a structured research template
4. Charts are optionally generated
5. A Markdown report is produced and can be downloaded

The system is intentionally rule-based (no LLM usage) to ensure transparency and reproducibility.

# Installation
Clone the repository:
git clone https://github.com/JakubSMaslowski/Equity-Research-Tool.git
cd equity-research-generator

Install dependencies:
pip install -r requirements.txt

# Running the App
python -m streamlit run app.py
Then open the local URL shown in your terminal.

# Example Output
The tool generates a structured equity research draft in Markdown format, including:
- Key financial metrics
- Valuation commentary
- Business overview
- Supporting charts (if selected)
See a sample generated report here:  
[Sample Report](./examples/WES_AX_sample_report.md)

# Limitations
Relies on Yahoo Finance → some tickers have incomplete data
Revenue data is not consistently available for all markets (e.g. some ASX stocks)
No forward-looking analysis or valuation modeling
Designed as a workflow tool, not a full research platform

# Purpose
This project was built to:
- Automate repetitive parts of equity research workflows
- Improve efficiency in gathering and structuring financial data
- Demonstrate practical use of Python and AI-assisted development (“vibe coding”)

# Disclaimer
This tool is for educational purposes only and does not constitute investment advice.
