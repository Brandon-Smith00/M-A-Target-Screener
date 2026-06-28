# AI-Powered M&A Target Screener
Please read the Tear Sheets and the excel file if you are just looking for the outputs.

An automated pipeline that screens public companies for M&A attractiveness, scores them across five financial dimensions, generates AI-written acquisition analysis via the Claude API, and outputs polished PDF tearsheets and an Excel summary workbook. 

---

## What It Does

1. **Fetches live financial data** for a universe of public companies in a target sector using Yahoo Finance (`yfinance`)
2. **Scores each company** across five M&A attractiveness dimensions (0–100 scale)
3. **Calls Claude API** to generate institutional-quality acquisition rationale, strategic fit analysis, risk flags, and potential acquirer lists
4. **Outputs one-page PDF tearsheets** per top target with radar charts, score bars, and AI commentary
5. **Generates an Excel summary** with color-coded scoring across all screened companies

---

## Scoring Methodology

| Dimension | Weight | Rationale |
|---|---|---|
| **Valuation** | 25% | Lower EV/EBITDA and EV/Revenue = cheaper to acquire |
| **Profitability** | 25% | Higher EBITDA and net margins = quality asset |
| **Leverage** | 20% | Lower Net Debt/EBITDA = easier to finance deal |
| **Growth** | 15% | Higher revenue growth = strategic premium justified |
| **Scale** | 15% | Sweet-spot market cap ($500M–$30B) = acquirable |

Each dimension scores 0–100. Final score = weighted average. Ratings: **Strong Buy** (≥80), **Attractive** (≥65), **Moderate** (≥50), **Cautious** (≥35), **Weak** (<35).

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/yourusername/ma-screener.git
cd ma-screener
pip install -r requirements.txt
```

### 2. Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Get an API key at [console.anthropic.com](https://console.anthropic.com).

### 3. Run

```bash
# Screen digital infrastructure sector (default)
python main.py digital_infrastructure

# Other available sectors
python main.py software
python main.py healthcare
python main.py industrials
python main.py financial_services
```

### 4. View outputs

All outputs saved to `./output/`:
- `01_<TICKER>_tearsheet.pdf` through `05_<TICKER>_tearsheet.pdf` — one-page tearsheets
- `ma_target_summary.xlsx` — color-coded summary workbook with score breakdown tab

---

## Output Examples

### PDF Tearsheet
Each tearsheet includes:
- Company header with M&A target ranking
- Key financials table (10 metrics)
- Score bars across 5 dimensions with overall rating
- Pentagon radar chart
- AI-generated acquisition rationale, strategic fit, key risks, potential acquirers, and deal structure commentary

### Excel Summary
- **Ranked Targets** tab: All screened companies with financials and scores, color-coded by rating
- **Score Breakdown** tab: Dimension-by-dimension scoring heatmap

---

## Configuration

Edit `config.py` to customize:

```python
# Add your own sector universe
SECTOR_UNIVERSES["my_sector"] = ["TICK1", "TICK2", ...]

# Adjust scoring weights (must sum to 1.0)
SCORING_WEIGHTS = {
    "valuation":     0.30,  # Weight valuation more heavily
    "profitability": 0.25,
    ...
}

# Change deal size sweet spot
TARGET_MARKET_CAP_MIN_B = 1.0   # $1B minimum
TARGET_MARKET_CAP_MAX_B = 20.0  # $20B maximum

# Generate more tearsheets
TOP_N_TARGETS = 8
```

---

## Project Structure

```
ma_screener/
├── main.py          # CLI entry point and orchestrator
├── data_fetch.py    # yfinance data pipeline with fallback
├── scorer.py        # Five-dimension scoring engine
├── ai_analyst.py    # Claude API commentary generator
├── tearsheet.py     # ReportLab PDF tearsheet builder
├── mock_data.py     # Curated demo data (fallback if rate-limited)
├── config.py        # Sector universes, weights, settings
└── requirements.txt
```

---

## Tech Stack

| Component | Library |
|---|---|
| Financial data | `yfinance` |
| AI commentary | `anthropic` (Claude claude-sonnet-4-6) |
| PDF generation | `reportlab` |
| Excel output | `openpyxl` |
| Data processing | `pandas`, `numpy` |
| Visualization | `matplotlib` (radar charts) |

---

## Notes

- **Rate limiting**: Yahoo Finance occasionally rate-limits server environments. The tool automatically falls back to a curated dataset of realistic public financial data in that case. Running locally with a residential IP works reliably.
- **Data freshness**: Financial data is pulled live from Yahoo Finance (TTM figures). For production use, consider a paid data provider (Alpha Vantage, Polygon.io, or Bloomberg API).
- **Disclaimer**: For educational and portfolio purposes only. Not investment advice.

---

*Built with Python + Claude API*
