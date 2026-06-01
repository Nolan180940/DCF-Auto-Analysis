from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

FINNHUB_BASE_URL = os.getenv("FINNHUB_BASE_URL", "https://finnhub.io/api/v1")
DEFAULT_TICKER = "DT"
DEFAULT_TIMEOUT = 20


class FinnhubClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key.strip()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.api_key:
            raise ValueError("Finnhub API key is missing")

        merged = dict(params or {})
        merged["token"] = self.api_key
        url = f"{FINNHUB_BASE_URL}{path}"

        response = requests.get(url, params=merged, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = response.json()

        if isinstance(payload, dict) and payload.get("error"):
            raise RuntimeError(f"Finnhub error: {payload['error']}")

        if isinstance(payload, list):
            return {"data": payload}

        return payload

    def get_quote(self, symbol: str) -> dict[str, Any]:
        return self._get("/quote", {"symbol": symbol})

    def get_profile(self, symbol: str) -> dict[str, Any]:
        return self._get("/stock/profile2", {"symbol": symbol})

    def get_basic_financials(self, symbol: str) -> dict[str, Any]:
        return self._get("/stock/metric", {"symbol": symbol, "metric": "all"})

    def get_financials_reported(self, symbol: str) -> dict[str, Any]:
        return self._get("/stock/financials-reported", {"symbol": symbol, "freq": "annual"})


@dataclass
class ScenarioAssumptions:
    name: str
    growth_start_pct: float
    growth_end_pct: float
    wacc_pct: float
    terminal_growth_pct: float
    probability_pct: float


def to_float(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        if math.isfinite(float(value)):
            return float(value)
        return None

    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if not cleaned:
            return None
        try:
            numeric = float(cleaned)
            if math.isfinite(numeric):
                return numeric
        except ValueError:
            return None

    return None


def normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def concept_map_from_object(payload: Any) -> dict[str, float]:
    concepts: dict[str, float] = {}

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            concept = node.get("concept")
            value = to_float(node.get("value"))
            if isinstance(concept, str) and value is not None:
                concepts[normalize_key(concept)] = value

            for child in node.values():
                walk(child)

        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(payload)
    return concepts


def pick_value(concepts: dict[str, float], fragments: list[str]) -> float | None:
    for fragment in fragments:
        nf = normalize_key(fragment)
        for concept, value in concepts.items():
            if nf in concept:
                return value
    return None


def pick_debt(concepts: dict[str, float]) -> float | None:
    total_debt = pick_value(
        concepts,
        [
            "debtandfinanceleasecurrentandnoncurrent",
            "longtermdebtandshorttermborrowings",
            "totalliabilitiesdebt",
            "debt",
        ],
    )
    if total_debt is not None:
        return total_debt

    short_debt = pick_value(concepts, ["shorttermdebt", "debtcurrent", "borrowingscurrent"])
    long_debt = pick_value(concepts, ["longtermdebt", "noncurrentdebt", "borrowingsnoncurrent"])

    if short_debt is None and long_debt is None:
        return None

    return (short_debt or 0.0) + (long_debt or 0.0)


def parse_reported_financials(payload: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in payload.get("data", []):
        report = item.get("report", {})
        concepts = concept_map_from_object(report)

        revenue = pick_value(
            concepts,
            [
                "revenues",
                "salesrevenue",
                "revenuefromcontractwithcustomer",
                "totalrevenue",
            ],
        )
        ebit = pick_value(concepts, ["operatingincome", "incomefromoperations", "ebit"])
        cfo = pick_value(
            concepts,
            [
                "netcashprovidedbyusedinoperatingactivities",
                "netcashprovidedbyoperatingactivities",
                "operatingcashflow",
                "cashfromoperatingactivities",
            ],
        )
        capex_raw = pick_value(
            concepts,
            [
                "paymentstoacquirepropertyplantandequipment",
                "capitalexpenditures",
                "purchaseofpropertyplantandequipment",
                "capitalexpenditure",
            ],
        )
        capex = abs(capex_raw) if capex_raw is not None else None
        fcf = (cfo - capex) if (cfo is not None and capex is not None) else None

        cash = pick_value(
            concepts,
            [
                "cashandcashequivalentsatcarryingvalue",
                "cashcashequivalentsandshortterminvestments",
                "cashandequivalents",
            ],
        )
        debt = pick_debt(concepts)

        end_date = item.get("endDate") or item.get("year")

        rows.append(
            {
                "end_date": end_date,
                "revenue": revenue,
                "ebit": ebit,
                "ebit_margin": (ebit / revenue) if (ebit is not None and revenue not in (None, 0)) else None,
                "cfo": cfo,
                "capex": capex,
                "fcf": fcf,
                "cash": cash,
                "debt": debt,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    df = df.dropna(subset=["end_date"]).sort_values("end_date").reset_index(drop=True)
    return df


def infer_shares_from_metric(metrics: dict[str, Any]) -> float | None:
    metric_map = metrics.get("metric", {}) if isinstance(metrics.get("metric"), dict) else {}

    candidates = [
        metric_map.get("shareOutstanding"),
        metric_map.get("sharesOutstanding"),
        metric_map.get("weightedAverageShsOutDil"),
    ]

    for value in candidates:
        v = to_float(value)
        if v is None:
            continue

        # Many APIs provide share counts in millions, so normalize to absolute shares.
        if v < 1_000_000:
            return v * 1_000_000

        return v

    return None


def infer_net_debt(df: pd.DataFrame, metrics: dict[str, Any]) -> float:
    if not df.empty:
        latest = df.iloc[-1]
        debt = to_float(latest.get("debt"))
        cash = to_float(latest.get("cash"))
        if debt is not None and cash is not None:
            return debt - cash

    metric_map = metrics.get("metric", {}) if isinstance(metrics.get("metric"), dict) else {}
    net_debt = to_float(metric_map.get("netDebt"))
    if net_debt is not None:
        # Same magnitude normalization heuristic as shares.
        if abs(net_debt) < 10_000_000:
            return net_debt * 1_000_000
        return net_debt

    return 0.0


def infer_base_fcf(df: pd.DataFrame, lookback_years: int) -> float | None:
    if df.empty or "fcf" not in df.columns:
        return None

    sample = df.dropna(subset=["fcf"]).tail(lookback_years)
    if sample.empty:
        return None

    return float(sample["fcf"].mean())


def format_billions(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "-"
    return f"{value / 1_000_000_000:,.2f}B"


def run_dcf(
    base_fcf: float,
    years: int,
    net_debt: float,
    shares_outstanding: float,
    current_price: float,
    scenario: ScenarioAssumptions,
) -> dict[str, Any]:
    wacc = scenario.wacc_pct / 100.0
    terminal_growth = scenario.terminal_growth_pct / 100.0

    if wacc <= terminal_growth:
        raise ValueError(f"{scenario.name}: WACC must be greater than terminal growth")

    growths = np.linspace(scenario.growth_start_pct / 100.0, scenario.growth_end_pct / 100.0, years)

    projected_rows: list[dict[str, Any]] = []
    fcf = base_fcf

    for idx, growth in enumerate(growths, start=1):
        fcf = fcf * (1.0 + growth)
        discount_factor = (1.0 + wacc) ** idx
        pv_fcf = fcf / discount_factor

        projected_rows.append(
            {
                "year": idx,
                "growth_pct": growth * 100,
                "projected_fcf": fcf,
                "discount_factor": discount_factor,
                "pv_fcf": pv_fcf,
            }
        )

    terminal_fcf = projected_rows[-1]["projected_fcf"] * (1.0 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    terminal_pv = terminal_value / ((1.0 + wacc) ** years)

    pv_stage_1 = float(sum(row["pv_fcf"] for row in projected_rows))
    enterprise_value = pv_stage_1 + terminal_pv
    equity_value = enterprise_value - net_debt
    implied_price = equity_value / shares_outstanding
    upside_pct = ((implied_price / current_price) - 1.0) * 100 if current_price > 0 else np.nan

    return {
        "scenario": scenario,
        "projection_table": pd.DataFrame(projected_rows),
        "pv_stage_1": pv_stage_1,
        "terminal_value": terminal_value,
        "terminal_pv": terminal_pv,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "implied_price": implied_price,
        "upside_pct": upside_pct,
    }


def generate_sensitivity_table(
    base_fcf: float,
    years: int,
    net_debt: float,
    shares_outstanding: float,
    current_price: float,
    base_growth_start_pct: float,
    base_growth_end_pct: float,
    wacc_values: np.ndarray,
    terminal_growth_values: np.ndarray,
) -> pd.DataFrame:
    table = pd.DataFrame(index=np.round(wacc_values, 2), columns=np.round(terminal_growth_values, 2), dtype=float)

    for wacc in wacc_values:
        for tg in terminal_growth_values:
            try:
                scenario = ScenarioAssumptions(
                    name="Sensitivity",
                    growth_start_pct=base_growth_start_pct,
                    growth_end_pct=base_growth_end_pct,
                    wacc_pct=float(wacc),
                    terminal_growth_pct=float(tg),
                    probability_pct=100.0,
                )
                result = run_dcf(base_fcf, years, net_debt, shares_outstanding, current_price, scenario)
                table.loc[round(wacc, 2), round(tg, 2)] = result["implied_price"]
            except ValueError:
                table.loc[round(wacc, 2), round(tg, 2)] = np.nan

    table.index.name = "WACC (%)"
    table.columns.name = "Terminal Growth (%)"
    return table


@st.cache_data(ttl=3600)
def load_stock_data(symbol: str, api_key: str) -> dict[str, Any]:
    client = FinnhubClient(api_key)
    quote = client.get_quote(symbol)
    profile = client.get_profile(symbol)
    metrics = client.get_basic_financials(symbol)
    reported = client.get_financials_reported(symbol)

    reported_df = parse_reported_financials(reported)

    return {
        "quote": quote,
        "profile": profile,
        "metrics": metrics,
        "reported_df": reported_df,
    }


def recommendation_from_upside(upside_pct: float) -> str:
    if not math.isfinite(upside_pct):
        return "Insufficient signal"
    if upside_pct >= 25:
        return "Buy"
    if upside_pct >= 10:
        return "Accumulate"
    if upside_pct > -10:
        return "Hold"
    if upside_pct > -25:
        return "Reduce"
    return "Sell"


def render_projection_chart(results: list[dict[str, Any]]) -> None:
    fig = go.Figure()
    for item in results:
        table = item["projection_table"]
        fig.add_trace(
            go.Scatter(
                x=table["year"],
                y=table["projected_fcf"],
                mode="lines+markers",
                name=f"{item['scenario'].name} FCF",
            )
        )

    fig.update_layout(
        title="Projected FCF by Scenario",
        xaxis_title="Projection Year",
        yaxis_title="FCF",
        height=420,
        legend_title="Series",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_history_chart(df: pd.DataFrame) -> None:
    chart_df = df.copy()
    chart_df["year"] = chart_df["end_date"].dt.year

    fig = go.Figure()
    if chart_df["revenue"].notna().any():
        fig.add_trace(go.Bar(x=chart_df["year"], y=chart_df["revenue"], name="Revenue", opacity=0.7))
    if chart_df["fcf"].notna().any():
        fig.add_trace(go.Scatter(x=chart_df["year"], y=chart_df["fcf"], mode="lines+markers", name="FCF"))

    fig.update_layout(
        title="Historical Fundamentals",
        xaxis_title="Fiscal Year",
        yaxis_title="Amount",
        barmode="group",
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="DCF Auto Analysis Workbench", layout="wide")
    st.title("DCF Auto Analysis Workbench")
    st.caption(
        "Scenario-based DCF with adjustable assumptions, sensitivity analysis, and transparent calculation breakdown."
    )

    default_api_key = os.getenv("FINNHUB_API_KEY") or ""

    st.sidebar.header("Data Source")
    api_key = st.sidebar.text_input("Finnhub API Key", value=default_api_key, type="password")
    symbol = st.sidebar.text_input("Ticker", value=DEFAULT_TICKER).strip().upper()

    if not api_key:
        st.warning("Please provide a Finnhub API key to fetch data.")
        return

    try:
        data = load_stock_data(symbol, api_key)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to load market data: {exc}")
        return

    quote = data["quote"]
    profile = data["profile"]
    metrics = data["metrics"]
    reported_df = data["reported_df"]

    current_price = to_float(quote.get("c")) or 0.0
    shares = infer_shares_from_metric(metrics) or 100_000_000.0
    net_debt = infer_net_debt(reported_df, metrics)

    st.subheader(f"Company Snapshot: {profile.get('name') or symbol} ({symbol})")

    kpi_cols = st.columns(5)
    kpi_cols[0].metric("Current Price", f"{current_price:,.2f}")
    market_cap = to_float(profile.get("marketCapitalization"))
    kpi_cols[1].metric("Market Cap", format_billions(market_cap * 1_000_000 if market_cap is not None else None))
    kpi_cols[2].metric("Shares Out.", f"{shares:,.0f}")
    kpi_cols[3].metric("Net Debt", format_billions(net_debt))

    lookback_years = st.sidebar.slider("Base FCF Lookback Years", min_value=2, max_value=8, value=4)
    inferred_base_fcf = infer_base_fcf(reported_df, lookback_years)
    fallback_base_fcf = current_price * shares * 0.06
    base_fcf_initial = inferred_base_fcf if inferred_base_fcf is not None else fallback_base_fcf

    kpi_cols[4].metric("Base FCF", format_billions(base_fcf_initial))

    if reported_df.empty:
        st.warning("No annual financial statements returned by Finnhub for this ticker. You can still run DCF using manual overrides.")
    else:
        st.markdown("### Fundamentals")
        fundamentals_table = reported_df.copy()
        fundamentals_table["fiscal_year"] = fundamentals_table["end_date"].dt.year
        st.dataframe(
            fundamentals_table[
                ["fiscal_year", "revenue", "ebit", "ebit_margin", "cfo", "capex", "fcf", "cash", "debt"]
            ],
            use_container_width=True,
            hide_index=True,
        )
        render_history_chart(reported_df)

    st.markdown("---")
    st.markdown("## DCF Assumptions")

    global_cols = st.columns(4)
    projection_years = global_cols[0].slider("Projection Years", min_value=5, max_value=15, value=10)
    base_fcf = global_cols[1].number_input("Base FCF (manual override)", value=float(base_fcf_initial), step=10_000_000.0)
    net_debt_input = global_cols[2].number_input("Net Debt", value=float(net_debt), step=10_000_000.0)
    shares_input = global_cols[3].number_input("Shares Outstanding", value=float(shares), step=1_000_000.0)

    st.markdown("### Scenario Sliders")

    scenario_cols = st.columns(3)

    with scenario_cols[0]:
        st.markdown("#### Bull Case")
        bull_start = st.slider("Bull FCF Growth Start (%)", -5.0, 30.0, 14.0, 0.5)
        bull_end = st.slider("Bull FCF Growth End (%)", -5.0, 20.0, 6.0, 0.5)
        bull_wacc = st.slider("Bull WACC (%)", 4.0, 18.0, 8.0, 0.1)
        bull_tg = st.slider("Bull Terminal Growth (%)", 0.0, 6.0, 3.0, 0.1)
        bull_prob = st.slider("Bull Probability (%)", 0.0, 100.0, 25.0, 1.0)

    with scenario_cols[1]:
        st.markdown("#### Base Case")
        base_start = st.slider("Base FCF Growth Start (%)", -5.0, 30.0, 10.0, 0.5)
        base_end = st.slider("Base FCF Growth End (%)", -5.0, 20.0, 4.0, 0.5)
        base_wacc = st.slider("Base WACC (%)", 4.0, 18.0, 9.5, 0.1)
        base_tg = st.slider("Base Terminal Growth (%)", 0.0, 6.0, 2.5, 0.1)
        base_prob = st.slider("Base Probability (%)", 0.0, 100.0, 50.0, 1.0)

    with scenario_cols[2]:
        st.markdown("#### Bear Case")
        bear_start = st.slider("Bear FCF Growth Start (%)", -20.0, 20.0, 4.0, 0.5)
        bear_end = st.slider("Bear FCF Growth End (%)", -20.0, 12.0, 1.0, 0.5)
        bear_wacc = st.slider("Bear WACC (%)", 4.0, 20.0, 11.5, 0.1)
        bear_tg = st.slider("Bear Terminal Growth (%)", -2.0, 5.0, 1.5, 0.1)
        bear_prob = st.slider("Bear Probability (%)", 0.0, 100.0, 25.0, 1.0)

    scenarios = [
        ScenarioAssumptions("Bull", bull_start, bull_end, bull_wacc, bull_tg, bull_prob),
        ScenarioAssumptions("Base", base_start, base_end, base_wacc, base_tg, base_prob),
        ScenarioAssumptions("Bear", bear_start, bear_end, bear_wacc, bear_tg, bear_prob),
    ]

    total_prob = sum(s.probability_pct for s in scenarios)
    if total_prob <= 0:
        st.error("Scenario probabilities must sum to a positive number.")
        return

    normalized = [
        ScenarioAssumptions(
            name=s.name,
            growth_start_pct=s.growth_start_pct,
            growth_end_pct=s.growth_end_pct,
            wacc_pct=s.wacc_pct,
            terminal_growth_pct=s.terminal_growth_pct,
            probability_pct=(s.probability_pct / total_prob) * 100.0,
        )
        for s in scenarios
    ]

    results: list[dict[str, Any]] = []

    for scenario in normalized:
        try:
            result = run_dcf(
                base_fcf=base_fcf,
                years=projection_years,
                net_debt=net_debt_input,
                shares_outstanding=shares_input,
                current_price=current_price,
                scenario=scenario,
            )
            results.append(result)
        except ValueError as exc:
            st.error(str(exc))
            return

    summary_rows: list[dict[str, Any]] = []
    weighted_price = 0.0
    weighted_upside = 0.0

    for item in results:
        sc = item["scenario"]
        implied = item["implied_price"]
        upside = item["upside_pct"]
        p = sc.probability_pct / 100.0
        weighted_price += implied * p
        weighted_upside += upside * p

        summary_rows.append(
            {
                "Scenario": sc.name,
                "Probability %": round(sc.probability_pct, 2),
                "WACC %": sc.wacc_pct,
                "Terminal g %": sc.terminal_growth_pct,
                "Implied Price": implied,
                "Upside / Downside %": upside,
                "Recommendation": recommendation_from_upside(upside),
            }
        )

    summary_df = pd.DataFrame(summary_rows)

    st.markdown("---")
    st.markdown("## Valuation Output")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    output_cols = st.columns(3)
    output_cols[0].metric("Probability-Weighted Price", f"{weighted_price:,.2f}")
    output_cols[1].metric("Probability-Weighted Upside", f"{weighted_upside:,.2f}%")
    output_cols[2].metric("Weighted Signal", recommendation_from_upside(weighted_upside))

    render_projection_chart(results)

    st.markdown("### Calculation Process")
    st.markdown(
        "Enterprise Value = PV(Stage-1 FCF) + PV(Terminal Value); Equity Value = Enterprise Value - Net Debt; Implied Price = Equity Value / Shares Outstanding"
    )

    for item in results:
        sc = item["scenario"]
        with st.expander(f"{sc.name} Case Details"):
            st.write(
                {
                    "Base FCF": base_fcf,
                    "Projection Years": projection_years,
                    "WACC %": sc.wacc_pct,
                    "Terminal Growth %": sc.terminal_growth_pct,
                    "PV Stage-1 FCF": item["pv_stage_1"],
                    "Terminal Value": item["terminal_value"],
                    "PV Terminal Value": item["terminal_pv"],
                    "Enterprise Value": item["enterprise_value"],
                    "Equity Value": item["equity_value"],
                    "Implied Price": item["implied_price"],
                    "Upside / Downside %": item["upside_pct"],
                }
            )
            st.dataframe(item["projection_table"], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("## Sensitivity Analysis")

    sens_cols = st.columns(2)
    with sens_cols[0]:
        wacc_low, wacc_high = st.slider("WACC Range (%)", 4.0, 20.0, (base_wacc - 2.0, base_wacc + 2.0), 0.1)
    with sens_cols[1]:
        tg_low, tg_high = st.slider("Terminal Growth Range (%)", -1.0, 6.0, (base_tg - 1.0, base_tg + 1.0), 0.1)

    wacc_values = np.round(np.arange(wacc_low, wacc_high + 0.001, 0.25), 2)
    tg_values = np.round(np.arange(tg_low, tg_high + 0.001, 0.25), 2)

    sens_df = generate_sensitivity_table(
        base_fcf=base_fcf,
        years=projection_years,
        net_debt=net_debt_input,
        shares_outstanding=shares_input,
        current_price=current_price,
        base_growth_start_pct=base_start,
        base_growth_end_pct=base_end,
        wacc_values=wacc_values,
        terminal_growth_values=tg_values,
    )

    heatmap = px.imshow(
        sens_df,
        labels={"x": "Terminal Growth (%)", "y": "WACC (%)", "color": "Implied Price"},
        title="Implied Price Sensitivity (Base Growth Path)",
        aspect="auto",
        color_continuous_scale="RdYlGn",
    )
    st.plotly_chart(heatmap, use_container_width=True)
    st.dataframe(sens_df, use_container_width=True)

    st.markdown("### Projection Horizon Sensitivity")
    horizon_rows = []
    for years in range(5, 16):
        base_scenario = ScenarioAssumptions(
            name="Base",
            growth_start_pct=base_start,
            growth_end_pct=base_end,
            wacc_pct=base_wacc,
            terminal_growth_pct=base_tg,
            probability_pct=100,
        )
        result = run_dcf(
            base_fcf=base_fcf,
            years=years,
            net_debt=net_debt_input,
            shares_outstanding=shares_input,
            current_price=current_price,
            scenario=base_scenario,
        )
        horizon_rows.append({"Projection Years": years, "Implied Price": result["implied_price"]})

    horizon_df = pd.DataFrame(horizon_rows)
    horizon_fig = px.line(horizon_df, x="Projection Years", y="Implied Price", markers=True)
    horizon_fig.update_layout(title="Implied Price vs Projection Horizon")
    st.plotly_chart(horizon_fig, use_container_width=True)


if __name__ == "__main__":
    main()
