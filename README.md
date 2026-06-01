# DCF Auto Analysis Workspace

This repository has been reduced to a DCF-only workspace.

## Welcome for contributions cuz it's an early stage of the repo with definitely potential failures and errors. Please propose issues or PRs if possible. Thank you for your visiting and if helpful, click a STAR to support author:)

## Structure

- scripts/dcf_dashboard/
  - dcf_dashboard.py
  - requirements.txt
  - README.md

## Run

1. Install dependencies:

  ```powershell
   pip install -r scripts/dcf_dashboard/requirements.txt
  ```

2. Set Finnhub API key (PowerShell): YOU NEED TO USE YOUR OWN FINNHUB API KEY (FREE TO SIGH UP AND FREE TO RETRIEVE)

  ```powershell
   $env:FINNHUB_API_KEY = "your_key_here"
  ```

3. Launch dashboard:

  ```powershell
   streamlit run scripts/dcf_dashboard/dcf_dashboard.py
  ```

## Notes

- This workspace now focuses only on automatic DCF analysis.
- You are supposed to be equipped with expertise in accounting, and basic DCF Valuation skills. The repo and relative python scripts are simply providing fundamental information and valution process visualization for investment suggestion purpose only, which indicates inrresponsibility for your actual investment behaviors and decisions.
- You need to swipe the bar for WACC assumptions and decide your own projection range and key parameters assumptions.
- Get your API Keys dierctly from finnhub official website.

## DEMO WEBSITE:

[Auto DCF Analysis](https://auto-dcf.streamlit.app/)
