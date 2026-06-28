# ─────────────────────────────────────────────
#  data_fetch.py — Live financial data via yfinance
# ─────────────────────────────────────────────

import yfinance as yf
import pandas as pd
import numpy as np
from config import SECTOR_UNIVERSES
import warnings
warnings.filterwarnings("ignore")


def safe_get(info: dict, *keys, default=None):
    """Try multiple key names; return first hit or default."""
    for k in keys:
        v = info.get(k)
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            return v
    return default


def fetch_company_data(ticker: str) -> dict | None:
    """
    Pull key financial metrics for a single ticker.
    Returns a dict of metrics or None if data is insufficient.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info

        # Basic identity
        name          = safe_get(info, "longName", "shortName", default=ticker)
        sector        = safe_get(info, "sector", default="N/A")
        industry      = safe_get(info, "industry", default="N/A")
        description   = safe_get(info, "longBusinessSummary", default="")

        # Market data
        market_cap    = safe_get(info, "marketCap", default=None)
        price         = safe_get(info, "currentPrice", "regularMarketPrice", default=None)
        ev            = safe_get(info, "enterpriseValue", default=None)

        # Income statement
        revenue       = safe_get(info, "totalRevenue", default=None)
        ebitda        = safe_get(info, "ebitda", default=None)
        net_income    = safe_get(info, "netIncomeToCommon", default=None)
        gross_profit  = safe_get(info, "grossProfits", default=None)
        rev_growth    = safe_get(info, "revenueGrowth", default=None)    # YoY decimal

        # Balance sheet
        total_debt    = safe_get(info, "totalDebt", default=0) or 0
        cash          = safe_get(info, "totalCash", default=0) or 0
        net_debt      = total_debt - cash

        # Skip companies with missing critical data
        if not all([market_cap, revenue, ev]):
            return None

        # Derived multiples
        ev_ebitda  = (ev / ebitda)   if ebitda and ebitda > 0 else None
        ev_revenue = (ev / revenue)  if revenue and revenue > 0 else None
        nd_ebitda  = (net_debt / ebitda) if ebitda and ebitda > 0 else None
        ebitda_margin = (ebitda / revenue) if revenue and revenue > 0 else None
        net_margin    = (net_income / revenue) if net_income and revenue and revenue > 0 else None

        return {
            # Identity
            "ticker":       ticker,
            "name":         name,
            "sector":       sector,
            "industry":     industry,
            "description":  description[:600] if description else "",

            # Scale (raw $)
            "market_cap":   market_cap,
            "enterprise_value": ev,
            "revenue":      revenue,
            "ebitda":       ebitda,

            # Valuation multiples
            "ev_ebitda":    ev_ebitda,
            "ev_revenue":   ev_revenue,

            # Leverage
            "net_debt":     net_debt,
            "nd_ebitda":    nd_ebitda,

            # Profitability
            "ebitda_margin": ebitda_margin,
            "net_margin":    net_margin,

            # Growth
            "revenue_growth": rev_growth,

            # Price
            "price":        price,
        }

    except Exception as e:
        print(f"  ⚠  {ticker}: fetch error — {e}")
        return None


def fetch_sector_universe(sector_key: str) -> pd.DataFrame:
    """
    Fetch data for all tickers in a sector universe.
    Falls back to realistic mock data if live fetch fails (e.g. rate limiting).
    Returns a cleaned DataFrame sorted by market cap.
    """
    tickers = SECTOR_UNIVERSES.get(sector_key)
    if not tickers:
        available = ", ".join(SECTOR_UNIVERSES.keys())
        raise ValueError(f"Unknown sector '{sector_key}'. Available: {available}")

    print(f"\n📡  Fetching live data for {len(tickers)} companies in '{sector_key}'...")
    results = []
    blocked_count = 0

    for ticker in tickers:
        print(f"  → {ticker}", end="  ", flush=True)
        data = fetch_company_data(ticker)
        if data:
            results.append(data)
            print("✓")
        else:
            blocked_count += 1
            print("✗ (skipped)")

    # If most tickers failed (likely rate-limited), use mock data
    if len(results) < len(tickers) * 0.4:
        print(f"\n⚠  Live fetch returned insufficient data ({len(results)}/{len(tickers)} tickers).")
        print("   Yahoo Finance may be rate-limiting this environment.")
        print("   → Switching to curated demo dataset (realistic public data).\n")
        from mock_data import get_mock_data
        mock = get_mock_data(sector_key)
        if mock:
            df = pd.DataFrame(mock)
            print(f"✅  Loaded {len(df)} companies from demo dataset\n")
            return df

    df = pd.DataFrame(results)
    print(f"\n✅  {len(df)} companies with sufficient data\n")
    return df


def format_billions(val):
    """Format a dollar value into readable billions/millions string."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    if abs(val) >= 1e9:
        return f"${val/1e9:.1f}B"
    elif abs(val) >= 1e6:
        return f"${val/1e6:.0f}M"
    else:
        return f"${val:,.0f}"


def format_pct(val):
    """Format a decimal as percentage string."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    return f"{val*100:.1f}%"


def format_multiple(val, suffix="x"):
    """Format a multiple with one decimal."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    return f"{val:.1f}{suffix}"
