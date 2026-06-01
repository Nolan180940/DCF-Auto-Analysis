# OpenStock — DCF 估值分析仪表板

基于 **Streamlit** 构建的自动化 DCF（Discounted Cash Flow，现金流折现）估值分析工具，用于快速评估公司内在价值。

## Welcome for contributions cuz it's an early stage of the repo with definitely potential failures and errors. Please propose issues or PRs if possible. Thank you for your visiting and if helpful, click a STAR to support author:)

## Structure

## 功能概述

- 自动获取公司财务数据（通过 Finnhub API）
- 计算自由现金流并进行折现估值
- 交互式 Streamlit 仪表板，可视化展示估值结果

---

  ```powershell
   pip install -r scripts/dcf_dashboard/requirements.txt
  ```

2. Set Finnhub API key (PowerShell): YOU NEED TO USE YOUR OWN FINNHUB API KEY (FREE TO SIGH UP AND FREE TO RETRIEVE)

  ```powershell
   $env:FINNHUB_API_KEY = "your_key_here"
  ```

### 2. 配置 API 密钥

  ```powershell
   streamlit run scripts/dcf_dashboard/dcf_dashboard.py
  ```

**PowerShell：**
```powershell
$env:FINNHUB_API_KEY = "your_finnhub_api_key"
```

- This workspace now focuses only on automatic DCF analysis.
- You are supposed to be equipped with expertise in accounting, and basic DCF Valuation skills. The repo and relative python scripts are simply providing fundamental information and valution process visualization for investment suggestion purpose only, which indicates inrresponsibility for your actual investment behaviors and decisions.
- You need to swipe the bar for WACC assumptions and decide your own projection range and key parameters assumptions.
- Get your API Keys dierctly from finnhub official website.

## DEMO WEBSITE:

[Auto DCF Analysis](https://auto-dcf.streamlit.app/)
