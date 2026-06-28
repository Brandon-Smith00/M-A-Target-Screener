# ─────────────────────────────────────────────
#  scorer.py — M&A Attractiveness Scoring Engine
# ─────────────────────────────────────────────
#
#  Each dimension scores 0–100.
#  Final score = weighted average across 5 dimensions.
#
#  Scoring philosophy:
#    Valuation   → lower multiples = higher score (cheaper to acquire)
#    Profitability → higher margins = higher score
#    Leverage    → lower net debt/EBITDA = higher score (easier to finance)
#    Growth      → higher revenue growth = higher score
#    Scale       → sweet-spot market cap = higher score (not too big, not tiny)

import numpy as np
import pandas as pd
from config import SCORING_WEIGHTS, TARGET_MARKET_CAP_MIN_B, TARGET_MARKET_CAP_MAX_B


def _clamp(val, lo=0.0, hi=100.0) -> float:
    return max(lo, min(hi, val))


def score_valuation(row: pd.Series) -> float:
    """
    Score based on EV/EBITDA and EV/Revenue.
    Lower multiples → more attractive acquisition target.
    Benchmarks: EV/EBITDA 6x = 100pts, 20x+ = 0pts
                EV/Revenue 1x = 100pts, 10x+ = 0pts
    """
    scores = []

    ev_ebitda = row.get("ev_ebitda")
    if ev_ebitda is not None and not np.isnan(ev_ebitda) and ev_ebitda > 0:
        # Linear scale: 6x→100, 20x→0
        s = _clamp((20 - ev_ebitda) / (20 - 6) * 100)
        scores.append(s)

    ev_revenue = row.get("ev_revenue")
    if ev_revenue is not None and not np.isnan(ev_revenue) and ev_revenue > 0:
        # Linear scale: 1x→100, 10x→0
        s = _clamp((10 - ev_revenue) / (10 - 1) * 100)
        scores.append(s)

    return np.mean(scores) if scores else 50.0   # neutral if no data


def score_profitability(row: pd.Series) -> float:
    """
    Score based on EBITDA margin and net margin.
    Benchmarks: EBITDA margin 40%+ = 100pts, 0% = 0pts
                Net margin 20%+ = 100pts, 0% = 0pts
    """
    scores = []

    ebitda_margin = row.get("ebitda_margin")
    if ebitda_margin is not None and not np.isnan(ebitda_margin):
        s = _clamp(ebitda_margin / 0.40 * 100)
        scores.append(s)

    net_margin = row.get("net_margin")
    if net_margin is not None and not np.isnan(net_margin):
        s = _clamp(net_margin / 0.20 * 100)
        scores.append(s)

    return np.mean(scores) if scores else 40.0


def score_leverage(row: pd.Series) -> float:
    """
    Score based on Net Debt / EBITDA.
    Lower leverage = easier for acquirer to layer on deal debt.
    Benchmarks: ≤0x = 100pts (net cash), 6x+ = 0pts
    """
    nd_ebitda = row.get("nd_ebitda")

    if nd_ebitda is None or np.isnan(nd_ebitda):
        return 50.0  # neutral

    if nd_ebitda <= 0:
        return 100.0   # net cash position — great for acquirer

    # Linear: 0x→100, 6x→0
    s = _clamp((6 - nd_ebitda) / 6 * 100)
    return s


def score_growth(row: pd.Series) -> float:
    """
    Score based on YoY revenue growth.
    Higher growth = more strategic value.
    Benchmarks: 30%+ = 100pts, 0% = 40pts, negative = scaled down
    """
    growth = row.get("revenue_growth")

    if growth is None or np.isnan(growth):
        return 40.0   # neutral-low if no data

    if growth >= 0.30:
        return 100.0
    elif growth >= 0:
        # 0%→40, 30%→100
        return _clamp(40 + (growth / 0.30) * 60)
    else:
        # Negative growth: penalize
        return _clamp(40 + growth * 100)   # growth is negative decimal


def score_scale(row: pd.Series) -> float:
    """
    Score based on market cap — we want the acquirable sweet spot.
    Too small = integration risk / limited synergies
    Too large = difficult to finance
    Sweet spot: $500M – $30B → 100pts
    Outside: scaled down linearly
    """
    mc = row.get("market_cap")
    if mc is None or np.isnan(mc):
        return 40.0

    mc_b = mc / 1e9   # convert to billions

    lo = TARGET_MARKET_CAP_MIN_B
    hi = TARGET_MARKET_CAP_MAX_B

    if lo <= mc_b <= hi:
        return 100.0
    elif mc_b < lo:
        # Below sweet spot: scale from 0 (at $0) to 100 (at lo)
        return _clamp(mc_b / lo * 100)
    else:
        # Above sweet spot: penalize as it gets bigger
        # 30B→100, 100B→0
        return _clamp((100 - mc_b) / (100 - hi) * 100)


# ── Dimension scorer map ─────────────────────
_SCORERS = {
    "valuation":     score_valuation,
    "profitability": score_profitability,
    "leverage":      score_leverage,
    "growth":        score_growth,
    "scale":         score_scale,
}


def score_all(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all dimension scores to the DataFrame.
    Adds columns: score_valuation, score_profitability, etc. + total_score.
    Returns DataFrame sorted by total_score descending.
    """
    df = df.copy()

    for dim, fn in _SCORERS.items():
        col = f"score_{dim}"
        df[col] = df.apply(fn, axis=1).round(1)

    # Weighted total score
    df["total_score"] = sum(
        df[f"score_{dim}"] * weight
        for dim, weight in SCORING_WEIGHTS.items()
    ).round(1)

    df = df.sort_values("total_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    print("🏆  Scoring complete. Top 5 targets:")
    print(df[["rank", "ticker", "name", "total_score"]].head(5).to_string(index=False))
    print()

    return df


def get_score_label(score: float) -> str:
    """Convert numeric score to qualitative label."""
    if score >= 80:  return "Strong Buy"
    if score >= 65:  return "Attractive"
    if score >= 50:  return "Moderate"
    if score >= 35:  return "Cautious"
    return "Weak"


def get_score_color(score: float) -> tuple:
    """Return RGB tuple for score band (for PDF coloring)."""
    if score >= 80:  return (0.09, 0.45, 0.27)   # dark green
    if score >= 65:  return (0.20, 0.63, 0.40)   # green
    if score >= 50:  return (0.85, 0.65, 0.13)   # amber
    if score >= 35:  return (0.85, 0.40, 0.13)   # orange
    return (0.75, 0.15, 0.15)                     # red
