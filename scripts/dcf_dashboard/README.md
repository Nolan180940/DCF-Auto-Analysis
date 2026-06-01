# DCF Auto Analysis Workbench (Python)

This dashboard builds a three-scenario DCF model (Bull / Base / Bear) using Finnhub market and fundamental data, with interactive assumption sliders.

## Features

- Pulls fundamentals and quote data from Finnhub
- Shows historical revenue, EBIT, CFO, CapEx, and inferred FCF
- Three scenario controls:
  - FCF growth start/end
  - WACC
  - Terminal growth
  - Probability
- Projection horizon sensitivity
- WACC vs terminal growth sensitivity heatmap
- Transparent step-by-step valuation tables

## Data Source

This script uses Finnhub for quote and fundamentals.

Required API key env var:

- `FINNHUB_API_KEY`

## Quick Start

1. Install dependencies:

   pip install -r scripts/dcf_dashboard/requirements.txt

2. Export your API key in shell (PowerShell):

   $env:FINNHUB_API_KEY = "your_key_here"

3. Run Streamlit:

   streamlit run scripts/dcf_dashboard/dcf_dashboard.py

## Notes

- DCF output is highly assumption-sensitive.
- If a ticker has incomplete financial statements, you can still run the model by overriding base FCF, shares outstanding, and net debt manually.
- This tool is for research and educational use, not financial advice.
