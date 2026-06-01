# DCF Auto Analysis Workspace

This repository has been reduced to a DCF-only workspace.

## Structure

- scripts/dcf_dashboard/
  - dcf_dashboard.py
  - requirements.txt
  - README.md

## Run

1. Install dependencies:

   pip install -r scripts/dcf_dashboard/requirements.txt

2. Set Finnhub API key (PowerShell):

   $env:FINNHUB_API_KEY = "your_key_here"

3. Launch dashboard:

   streamlit run scripts/dcf_dashboard/dcf_dashboard.py

## Notes

- The previous web app files were removed intentionally.
- This workspace now focuses only on automatic DCF analysis.
