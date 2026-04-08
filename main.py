# main.py
# This is the entry point of the program — the file you run.
# It asks the user for a ticker, fetches data, generates a report,
# saves it to a file, and prints it to the terminal.

import os
import sys
from data_fetcher import fetch_company_data
from report_generator import generate_report


def main():
    print("=" * 60)
    print("  Equity Research Draft Generator")
    print("=" * 60)
    print()
    print("Enter a stock ticker symbol to generate a research draft.")
    print("Examples: AAPL, MSFT, GOOGL, BHP.AX, CBA.AX, RIO.AX")
    print()

    # Ask the user for a ticker
    ticker = input("Ticker symbol: ").strip().upper()

    if not ticker:
        print("[ERROR] No ticker entered. Exiting.")
        sys.exit(1)

    print(f"\nFetching data for '{ticker}' from Yahoo Finance...")
    print("(This may take a few seconds.)\n")

    # Step 1: Fetch data
    data = fetch_company_data(ticker)

    # If data_fetcher returned an empty dict, something went wrong
    if not data:
        print("[ERROR] No data was returned. Check the ticker and try again.")
        sys.exit(1)

    print(f"Data fetched successfully for: {data.get('name', ticker)}\n")

    # Step 2: Generate the report
    report = generate_report(data)

    # Step 3: Save to file
    # Create the outputs/ folder if it doesn't exist
    os.makedirs("outputs", exist_ok=True)

    # Build a clean filename from the ticker
    filename = f"outputs/{ticker}_research_draft.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)

    # Step 4: Print the report to the terminal
    print("=" * 60)
    print(report)
    print("=" * 60)
    print(f"\n Report saved to: {filename}")
    print("Done.\n")


# This ensures main() only runs when you execute this file directly,
# not if another file imports it.
if __name__ == "__main__":
    main()
