# ─────────────────────────────────────────────
#  ai_analyst.py — Gemini API Commentary Layer
# ─────────────────────────────────────────────

import google.generativeai as genai
import json
from data_fetch import format_billions, format_pct, format_multiple


def build_analyst_prompt(row: dict) -> str:
    financials = f"""
Company: {row['name']} ({row['ticker']})
Industry: {row['industry']}
Business: {row.get('description', 'N/A')[:400]}

KEY FINANCIALS:
- Market Cap:       {format_billions(row.get('market_cap'))}
- Enterprise Value: {format_billions(row.get('enterprise_value'))}
- Revenue (TTM):    {format_billions(row.get('revenue'))}
- EBITDA (TTM):     {format_billions(row.get('ebitda'))}
- EBITDA Margin:    {format_pct(row.get('ebitda_margin'))}
- Net Margin:       {format_pct(row.get('net_margin'))}
- Revenue Growth:   {format_pct(row.get('revenue_growth'))}
- EV/EBITDA:        {format_multiple(row.get('ev_ebitda'))}
- EV/Revenue:       {format_multiple(row.get('ev_revenue'))}
- Net Debt/EBITDA:  {format_multiple(row.get('nd_ebitda'))}

M&A ATTRACTIVENESS SCORES (0-100):
- Valuation:        {row.get('score_valuation', 'N/A')}
- Profitability:    {row.get('score_profitability', 'N/A')}
- Leverage:         {row.get('score_leverage', 'N/A')}
- Growth:           {row.get('score_growth', 'N/A')}
- Scale:            {row.get('score_scale', 'N/A')}
- OVERALL SCORE:    {row.get('total_score', 'N/A')} / 100
"""
    prompt = f"""You are a senior M&A analyst at a bulge bracket investment bank.
Respond with valid JSON only — no markdown, no preamble.

{financials}

Provide M&A analysis in this exact JSON format:
{{
  "acquisition_rationale": "3-4 sentences explaining why a strategic or financial acquirer would want this company.",
  "strategic_fit": "2-3 sentences on what type of acquirer would find this most attractive and why.",
  "key_risks": ["risk 1 in 10-15 words", "risk 2 in 10-15 words", "risk 3 in 10-15 words"],
  "potential_acquirers": ["Company A", "Company B", "Company C"],
  "deal_structure_note": "1-2 sentences on likely deal structure given the leverage profile.",
  "analyst_verdict": "One punchy sentence — the bottom line on this target."
}}"""
    return prompt


def generate_commentary(row: dict, api_key: str) -> dict:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(build_analyst_prompt(row))
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"  ⚠  API error for {row['ticker']}: {e}")
        return _fallback_commentary(row)


def _fallback_commentary(row: dict) -> dict:
    return {
        "acquisition_rationale": f"{row['name']} presents a compelling acquisition target based on its financial profile and market position.",
        "strategic_fit": "Suitable for both strategic buyers seeking scale and financial sponsors looking for platform investments.",
        "key_risks": ["Integration complexity and execution risk", "Competitive dynamics in core markets", "Regulatory and antitrust considerations"],
        "potential_acquirers": ["Strategic Buyer A", "Strategic Buyer B", "Financial Sponsor"],
        "deal_structure_note": "Likely all-cash or mixed consideration given current leverage profile.",
        "analyst_verdict": "A solid target warranting further diligence."
    }


def enrich_with_commentary(df, api_key: str, top_n: int = 5):
    top = df.head(top_n).copy()
    commentaries = []

    print(f"🤖  Generating AI analysis for top {top_n} targets...")
    for _, row in top.iterrows():
        print(f"  → Analyzing {row['ticker']} ({row['name'][:40]})...", flush=True)
        commentary = generate_commentary(row.to_dict(), api_key)
        commentaries.append(commentary)
        print(f"     ✓")

    top["commentary"] = commentaries
    df = df.copy()
    df["commentary"] = None
    for i, idx in enumerate(top.index):
        df.at[idx, "commentary"] = commentaries[i]

    print()
    return df
