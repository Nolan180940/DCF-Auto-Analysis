# OpenStock — DCF Valuation Dashboard

An automated Discounted Cash Flow (DCF) valuation analysis tool built with Streamlit. It enables rapid assessment of a company's intrinsic value through interactive visualizations and financial data retrieval.

## Features

- **Automated Financial Data Retrieval**: Fetches company financial statements via the Finnhub API
- **Free Cash Flow Calculation**: Computes free cash flow and performs discounted cash flow valuation
- **Interactive Dashboard**: Visualizes valuation results and key assumptions through Streamlit
- **Customizable Parameters**: Adjustable WACC, projection range, and other key assumptions

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/OpenStock.git
   cd OpenStock
   ```

2. Install dependencies:
   ```bash
   pip install -r scripts/dcf_dashboard/requirements.txt
   ```

## Configuration

Set your Finnhub API key as an environment variable:

**PowerShell:**
```powershell
$env:FINNHUB_API_KEY = "your_finnhub_api_key"
```

**Bash:**
```bash
export FINNHUB_API_KEY="your_finnhub_api_key"
```

You can obtain a free API key from the [Finnhub official website](https://finnhub.io/).

## Usage

Run the DCF dashboard:

```bash
streamlit run scripts/dcf_dashboard/dcf_dashboard.py
```

In the dashboard, you can:
- Enter a stock ticker symbol to retrieve financial data
- Adjust WACC assumptions using the sliders
- Set projection range for future cash flows
- View intrinsic value calculations and visualizations

## Requirements

- Python 3.8+
- Streamlit
- pandas, numpy, plotly, requests

See `scripts/dcf_dashboard/requirements.txt` for the complete list of dependencies.

## Demo

A live demo is available at [Auto DCF Analysis](https://auto-dcf.streamlit.app/).

## Disclaimer

This tool provides fundamental financial information and valuation process visualization for educational and informational purposes only. It should not be considered as investment advice or a basis for actual investment decisions. Users are responsible for their own investment choices and should possess appropriate knowledge in accounting and DCF valuation.

## Contributing

Contributions are welcome. This project is in early development and may contain bugs or incomplete features. Please feel free to:

- Open issues for bugs or feature requests
- Submit pull requests with improvements
- Add test cases or documentation

When contributing, please ensure your changes follow the existing code style and include appropriate documentation.

## License

This project is provided for educational purposes. Please verify API usage terms with Finnhub before use.