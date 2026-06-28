# ─────────────────────────────────────────────
#  tearsheet.py — PDF Tearsheet Generator
# ─────────────────────────────────────────────

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF
import os
import math
from datetime import date

from data_fetch import format_billions, format_pct, format_multiple
from scorer import get_score_label, get_score_color, SCORING_WEIGHTS
from config import OUTPUT_DIR

# ── Brand Colors ─────────────────────────────
NAVY     = colors.HexColor("#0A2342")
GOLD     = colors.HexColor("#C9A84C")
LGRAY    = colors.HexColor("#F5F6F7")
MGRAY    = colors.HexColor("#D0D3D8")
DGRAY    = colors.HexColor("#4A4F5C")
WHITE    = colors.white
GREEN    = colors.HexColor("#177345")
AMBER    = colors.HexColor("#D4A017")
RED      = colors.HexColor("#B22222")

PAGE_W, PAGE_H = letter
MARGIN = 0.5 * inch


def _score_bar(score: float, width=120, height=14) -> Drawing:
    """Render a horizontal score bar with fill."""
    d = Drawing(width, height)
    # background
    d.add(Rect(0, 2, width, height - 4, fillColor=colors.HexColor("#E0E3E8"), strokeColor=None))
    # fill
    fill_w = max(4, int(width * score / 100))
    r, g, b = get_score_color(score)
    bar_color = colors.Color(r, g, b)
    d.add(Rect(0, 2, fill_w, height - 4, fillColor=bar_color, strokeColor=None))
    return d


def _radar_chart(scores: dict, size=180) -> Drawing:
    """Draw a simple pentagon radar chart for the 5 score dimensions."""
    dims   = list(scores.keys())
    vals   = [scores[d] / 100.0 for d in dims]
    n      = len(dims)
    cx, cy = size / 2, size / 2
    R      = size * 0.38

    d = Drawing(size, size)

    # Grid rings
    for level in [0.25, 0.50, 0.75, 1.0]:
        pts = []
        for i in range(n):
            angle = math.pi / 2 + 2 * math.pi * i / n
            x = cx + R * level * math.cos(angle)
            y = cy + R * level * math.sin(angle)
            pts.append((x, y))
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            d.add(Line(x0, y0, x1, y1, strokeColor=colors.HexColor("#CBD0D8"), strokeWidth=0.5))

    # Spokes
    for i in range(n):
        angle = math.pi / 2 + 2 * math.pi * i / n
        x = cx + R * math.cos(angle)
        y = cy + R * math.sin(angle)
        d.add(Line(cx, cy, x, y, strokeColor=colors.HexColor("#CBD0D8"), strokeWidth=0.5))

    # Filled polygon (score area)
    score_pts = []
    for i in range(n):
        angle = math.pi / 2 + 2 * math.pi * i / n
        v = vals[i]
        x = cx + R * v * math.cos(angle)
        y = cy + R * v * math.sin(angle)
        score_pts.append((x, y))

    from reportlab.graphics.shapes import Polygon
    flat = [coord for pt in score_pts for coord in pt]
    d.add(Polygon(flat, fillColor=colors.Color(0.09, 0.45, 0.27, 0.25),
                  strokeColor=colors.Color(0.09, 0.45, 0.27), strokeWidth=1.5))

    # Labels
    label_map = {
        "valuation": "Val.", "profitability": "Prof.", "leverage": "Lev.",
        "growth": "Growth", "scale": "Scale"
    }
    for i, dim in enumerate(dims):
        angle = math.pi / 2 + 2 * math.pi * i / n
        lx = cx + (R + 16) * math.cos(angle)
        ly = cy + (R + 16) * math.sin(angle)
        label = label_map.get(dim, dim.title())
        d.add(String(lx, ly - 4, label, fontSize=7, fillColor=colors.HexColor("#4A4F5C"),
                     textAnchor="middle"))

    return d


def generate_tearsheet(row: dict, rank: int) -> str:
    """
    Generate a one-page PDF tearsheet for a single M&A target.
    Returns the output file path.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ticker  = row["ticker"]
    outpath = os.path.join(OUTPUT_DIR, f"{rank:02d}_{ticker}_tearsheet.pdf")

    doc = SimpleDocTemplate(
        outpath,
        pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── HEADER BANNER ─────────────────────────
    header_data = [[
        Paragraph(f"<font color='white'><b>{row['name']}</b> ({ticker})</font>",
                  ParagraphStyle("hd", fontSize=14, textColor=WHITE)),
        Paragraph(f"<font color='white'>#{rank} M&amp;A Target</font>",
                  ParagraphStyle("rk", fontSize=11, textColor=GOLD, alignment=TA_RIGHT)),
    ]]
    header_tbl = Table(header_data, colWidths=[4.5*inch, 2.5*inch])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",  (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0,0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",(0, 0), (-1, -1), 12),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 6))

    # ── SUBHEADER: industry + date ─────────────
    sub_data = [[
        Paragraph(f"<font color='#4A4F5C'>{row.get('industry','N/A')} | {row.get('sector','N/A')}</font>",
                  ParagraphStyle("sub", fontSize=9, textColor=DGRAY)),
        Paragraph(f"<font color='#4A4F5C'>Generated {date.today().strftime('%B %d, %Y')}</font>",
                  ParagraphStyle("dt", fontSize=9, textColor=DGRAY, alignment=TA_RIGHT)),
    ]]
    sub_tbl = Table(sub_data, colWidths=[4.5*inch, 2.5*inch])
    sub_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), LGRAY),
        ("TOPPADDING", (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 12),
        ("RIGHTPADDING",(0,0),(-1,-1), 12),
    ]))
    story.append(sub_tbl)
    story.append(Spacer(1, 10))

    # ── TWO-COLUMN BODY ───────────────────────
    # Left: financials + scores | Right: radar + verdict

    # -- Left column content --
    left_parts = []

    # Financials table
    left_parts.append(Paragraph("<b>Key Financials</b>",
        ParagraphStyle("sh", fontSize=9, textColor=NAVY, spaceAfter=4)))

    fin_rows = [
        ["Market Cap",      format_billions(row.get("market_cap"))],
        ["Enterprise Value",format_billions(row.get("enterprise_value"))],
        ["Revenue (TTM)",   format_billions(row.get("revenue"))],
        ["EBITDA (TTM)",    format_billions(row.get("ebitda"))],
        ["EBITDA Margin",   format_pct(row.get("ebitda_margin"))],
        ["Net Margin",      format_pct(row.get("net_margin"))],
        ["Revenue Growth",  format_pct(row.get("revenue_growth"))],
        ["EV / EBITDA",     format_multiple(row.get("ev_ebitda"))],
        ["EV / Revenue",    format_multiple(row.get("ev_revenue"))],
        ["Net Debt / EBITDA",format_multiple(row.get("nd_ebitda"))],
    ]
    fin_tbl = Table(fin_rows, colWidths=[1.6*inch, 1.2*inch])
    fin_tbl.setStyle(TableStyle([
        ("FONTSIZE",   (0,0),(-1,-1), 8),
        ("TEXTCOLOR",  (0,0),(0,-1), DGRAY),
        ("TEXTCOLOR",  (1,0),(1,-1), NAVY),
        ("FONTNAME",   (1,0),(1,-1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [WHITE, LGRAY]),
        ("TOPPADDING", (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("RIGHTPADDING",(0,0),(-1,-1), 6),
        ("GRID",       (0,0),(-1,-1), 0.25, MGRAY),
    ]))
    left_parts.append(fin_tbl)
    left_parts.append(Spacer(1, 10))

    # Score bars
    left_parts.append(Paragraph("<b>M&A Attractiveness Scores</b>",
        ParagraphStyle("sh2", fontSize=9, textColor=NAVY, spaceAfter=4)))

    score_dims = ["valuation","profitability","leverage","growth","scale"]
    score_labels = {"valuation":"Valuation","profitability":"Profitability",
                    "leverage":"Leverage","growth":"Growth","scale":"Scale"}

    score_rows = []
    for dim in score_dims:
        sc = row.get(f"score_{dim}", 50)
        bar = _score_bar(sc, width=110, height=12)
        score_rows.append([
            Paragraph(score_labels[dim],
                ParagraphStyle("sl", fontSize=8, textColor=DGRAY)),
            bar,
            Paragraph(f"<b>{sc:.0f}</b>",
                ParagraphStyle("sv", fontSize=8, textColor=NAVY, alignment=TA_RIGHT)),
        ])

    # Overall
    total = row.get("total_score", 0)
    label = get_score_label(total)
    r, g, b = get_score_color(total)
    lbl_color = colors.Color(r, g, b)
    score_rows.append([
        Paragraph("<b>OVERALL</b>",
            ParagraphStyle("ol", fontSize=9, textColor=NAVY)),
        Paragraph(f"<b>{total:.0f} / 100</b>",
            ParagraphStyle("ov", fontSize=9, textColor=lbl_color, alignment=TA_CENTER)),
        Paragraph(f"<b>{label}</b>",
            ParagraphStyle("olb", fontSize=9, textColor=lbl_color, alignment=TA_RIGHT)),
    ])

    score_tbl = Table(score_rows, colWidths=[1.1*inch, 1.3*inch, 0.7*inch])
    score_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ("LINEABOVE",     (0,-1),(-1,-1), 0.5, MGRAY),
        ("BACKGROUND",    (0,-1),(-1,-1), LGRAY),
    ]))
    left_parts.append(score_tbl)

    # -- Right column content --
    right_parts = []

    # Radar chart
    score_dict = {dim: row.get(f"score_{dim}", 50) for dim in score_dims}
    radar = _radar_chart(score_dict, size=170)
    right_parts.append(radar)
    right_parts.append(Spacer(1, 8))

    # Analyst verdict
    commentary = row.get("commentary") or {}
    verdict = commentary.get("analyst_verdict", "")
    if verdict:
        right_parts.append(Paragraph("<b>Analyst Verdict</b>",
            ParagraphStyle("avh", fontSize=9, textColor=NAVY, spaceAfter=3)))
        right_parts.append(Paragraph(
            f'<i>"{verdict}"</i>',
            ParagraphStyle("av", fontSize=8.5, textColor=DGRAY, leading=12)))
        right_parts.append(Spacer(1, 8))

    # Potential acquirers
    acquirers = commentary.get("potential_acquirers", [])
    if acquirers:
        right_parts.append(Paragraph("<b>Potential Acquirers</b>",
            ParagraphStyle("pah", fontSize=9, textColor=NAVY, spaceAfter=3)))
        for acq in acquirers:
            right_parts.append(Paragraph(f"• {acq}",
                ParagraphStyle("pa", fontSize=8, textColor=DGRAY, leading=11)))
        right_parts.append(Spacer(1, 8))

    # Deal structure note
    deal_note = commentary.get("deal_structure_note", "")
    if deal_note:
        right_parts.append(Paragraph("<b>Deal Structure</b>",
            ParagraphStyle("dsh", fontSize=9, textColor=NAVY, spaceAfter=3)))
        right_parts.append(Paragraph(deal_note,
            ParagraphStyle("ds", fontSize=8, textColor=DGRAY, leading=11)))

    # Assemble two-column layout
    from reportlab.platypus import KeepInFrame
    left_frame  = KeepInFrame(3.3*inch, 7*inch, left_parts)
    right_frame = KeepInFrame(3.2*inch, 7*inch, right_parts)

    body_tbl = Table([[left_frame, right_frame]], colWidths=[3.4*inch, 3.4*inch])
    body_tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0),(0,-1), 0),
        ("RIGHTPADDING",  (0,0),(0,-1), 10),
        ("LEFTPADDING",   (1,0),(1,-1), 10),
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 0),
    ]))
    story.append(body_tbl)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MGRAY))
    story.append(Spacer(1, 6))

    # ── AI COMMENTARY SECTION ─────────────────
    commentary_style = ParagraphStyle("cs", fontSize=8.5, textColor=DGRAY, leading=13)
    head_style = ParagraphStyle("hs", fontSize=9, textColor=NAVY, spaceBefore=6, spaceAfter=3)

    rationale = commentary.get("acquisition_rationale", "")
    strat_fit = commentary.get("strategic_fit", "")
    risks     = commentary.get("key_risks", [])

    ai_rows = []
    if rationale:
        ai_rows.append([
            Paragraph("<b>Acquisition Rationale</b>", head_style),
            Paragraph("<b>Strategic Fit</b>", head_style),
        ])
        ai_rows.append([
            Paragraph(rationale, commentary_style),
            Paragraph(strat_fit, commentary_style),
        ])

    if risks:
        risk_text = "<br/>".join(f"<b>▸</b> {r}" for r in risks)
        ai_rows.append([
            Paragraph("<b>Key Risks</b>", head_style),
            Paragraph("", head_style),
        ])
        ai_rows.append([
            Paragraph(risk_text, commentary_style),
            Paragraph("", commentary_style),
        ])

    if ai_rows:
        ai_tbl = Table(ai_rows, colWidths=[3.4*inch, 3.4*inch])
        ai_tbl.setStyle(TableStyle([
            ("VALIGN",       (0,0),(-1,-1), "TOP"),
            ("TOPPADDING",   (0,0),(-1,-1), 2),
            ("BOTTOMPADDING",(0,0),(-1,-1), 2),
            ("LEFTPADDING",  (0,0),(-1,-1), 0),
            ("RIGHTPADDING", (0,0),(0,-1), 12),
        ]))
        story.append(ai_tbl)

    # ── FOOTER ───────────────────────────────
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MGRAY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "This analysis was generated by an AI-powered M&A screening tool. "
        "For illustrative and educational purposes only. Not investment advice.",
        ParagraphStyle("foot", fontSize=6.5, textColor=colors.HexColor("#9AA0A6"),
                       alignment=TA_CENTER)
    ))

    doc.build(story)
    return outpath
