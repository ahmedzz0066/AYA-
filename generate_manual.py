from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white, black
import math

# ── Brand palette (matches indicator colours) ────────────────────────────────
BG        = HexColor("#0d0f14")
PANEL     = HexColor("#1a1d26")
ACCENT    = HexColor("#2196f3")
GOLD      = HexColor("#ffeb3b")
RED       = HexColor("#f44336")
GREEN     = HexColor("#4caf50")
LIGHT_BLU = HexColor("#64b5f6")
LGREY     = HexColor("#8a8d99")
WHITE     = HexColor("#ffffff")
SUBHEAD   = HexColor("#b0b8d0")

C0 = HexColor("#5d606b")
C1 = HexColor("#64b5f6")
C2 = HexColor("#2196f3")
C3 = HexColor("#81c784")
C4 = HexColor("#4caf50")
C5 = HexColor("#fff176")
C6 = HexColor("#ffeb3b")
C7 = HexColor("#e57373")
C8 = HexColor("#f44336")
C9 = HexColor("#ffffff")

W, H = A4

# ── Page template with dark background ───────────────────────────────────────
class DarkBackground(Flowable):
    def __init__(self, w, h):
        self.w, self.h = w, h
    def draw(self):
        pass

def on_page(cv, doc):
    cv.saveState()
    cv.setFillColor(BG)
    cv.rect(0, 0, W, H, fill=1, stroke=0)
    # header bar
    cv.setFillColor(PANEL)
    cv.rect(0, H - 18*mm, W, 18*mm, fill=1, stroke=0)
    cv.setFillColor(ACCENT)
    cv.rect(0, H - 18*mm, W, 1.2*mm, fill=1, stroke=0)
    # footer bar
    cv.setFillColor(PANEL)
    cv.rect(0, 0, W, 12*mm, fill=1, stroke=0)
    cv.setFillColor(ACCENT)
    cv.rect(0, 12*mm, W, 0.5*mm, fill=1, stroke=0)
    # header text
    cv.setFillColor(LIGHT_BLU)
    cv.setFont("Helvetica-Bold", 8)
    cv.drawString(15*mm, H - 12*mm, "VOLUME BARS AND LINES  //  USER MANUAL")
    cv.setFillColor(LGREY)
    cv.setFont("Helvetica", 8)
    cv.drawRightString(W - 15*mm, H - 12*mm, "© mellowmichellehe  |  Pine Script v6")
    # footer text
    cv.setFillColor(LGREY)
    cv.setFont("Helvetica", 7.5)
    cv.drawString(15*mm, 4.5*mm, "CONFIDENTIAL — FOR EDUCATIONAL USE ONLY")
    cv.drawRightString(W - 15*mm, 4.5*mm, f"Page {doc.page}")
    cv.restoreState()

def on_first_page(cv, doc):
    cv.saveState()
    cv.setFillColor(BG)
    cv.rect(0, 0, W, H, fill=1, stroke=0)
    cv.restoreState()

# ── Styles ────────────────────────────────────────────────────────────────────
ss = getSampleStyleSheet()

def S(name, **kw):
    base = ss["Normal"]
    return ParagraphStyle(name, parent=base, **kw)

sTitle   = S("sTitle",   fontSize=34, leading=42, textColor=WHITE,
             fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)
sSubT    = S("sSubT",    fontSize=13, leading=18, textColor=LIGHT_BLU,
             fontName="Helvetica", alignment=TA_CENTER, spaceAfter=2)
sTag     = S("sTag",     fontSize=9,  leading=12, textColor=LGREY,
             fontName="Helvetica", alignment=TA_CENTER, spaceAfter=0)
sH1      = S("sH1",      fontSize=18, leading=24, textColor=ACCENT,
             fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=3)
sH2      = S("sH2",      fontSize=13, leading=18, textColor=LIGHT_BLU,
             fontName="Helvetica-Bold", spaceBefore=7, spaceAfter=2)
sH3      = S("sH3",      fontSize=10, leading=14, textColor=GOLD,
             fontName="Helvetica-Bold", spaceBefore=5, spaceAfter=2)
sBody    = S("sBody",    fontSize=9,  leading=14, textColor=SUBHEAD,
             fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=5)
sMono    = S("sMono",    fontSize=8,  leading=12, textColor=GREEN,
             fontName="Courier", backColor=PANEL, spaceAfter=3,
             leftIndent=6, rightIndent=6, borderPad=4)
sBullet  = S("sBullet",  fontSize=9,  leading=14, textColor=SUBHEAD,
             fontName="Helvetica", leftIndent=12, spaceAfter=2,
             bulletIndent=4, bulletFontName="Helvetica", bulletFontSize=9)
sCaption = S("sCaption", fontSize=7.5,leading=10, textColor=LGREY,
             fontName="Helvetica", alignment=TA_CENTER, spaceBefore=2, spaceAfter=6)
sFormula = S("sFormula", fontSize=10, leading=16, textColor=GOLD,
             fontName="Courier-Bold", alignment=TA_CENTER,
             backColor=PANEL, spaceAfter=6, borderPad=5)
sNote    = S("sNote",    fontSize=8,  leading=12, textColor=LGREY,
             fontName="Helvetica-Oblique", leftIndent=8, spaceAfter=4)
sWarn    = S("sWarn",    fontSize=8.5,leading=13, textColor=HexColor("#ffb74d"),
             fontName="Helvetica-Bold", leftIndent=8, spaceAfter=4)
sTOC     = S("sTOC",     fontSize=10, leading=18, textColor=SUBHEAD,
             fontName="Helvetica")
sTOCn    = S("sTOCn",    fontSize=9,  leading=15, textColor=LGREY,
             fontName="Helvetica", leftIndent=10)

def HR():
    return HRFlowable(width="100%", thickness=0.5, color=ACCENT, spaceAfter=6, spaceBefore=4)

def sp(n=4):
    return Spacer(1, n*mm)

def h1(t):  return Paragraph(t, sH1)
def h2(t):  return Paragraph(t, sH2)
def h3(t):  return Paragraph(t, sH3)
def body(t): return Paragraph(t, sBody)
def mono(t): return Paragraph(t, sMono)
def note(t): return Paragraph(f"ℹ  {t}", sNote)
def warn(t): return Paragraph(f"⚠  {t}", sWarn)
def formula(t): return Paragraph(t, sFormula)
def bullet(items, color=ACCENT):
    # hexval() returns '0x2196f3' — strip '0x' and prepend '#'
    hex_str = "#" + color.hexval().lstrip("0x").zfill(6)
    return [Paragraph(f'<font color="{hex_str}">▸</font>  {i}', sBullet)
            for i in items]

# ── Colour tier swatch table ──────────────────────────────────────────────────
def tier_table():
    tiers = [
        ("0", C0, "#5d606b", "Below threshold",          "< 1×",       "Inactive / no participation"),
        ("1", C1, "#64b5f6", "Light blue — Low",         "≥ 1×",       "Mild above-average interest"),
        ("2", C2, "#2196f3", "Blue — Moderate",          "≥ 2×",       "Notable liquidity building"),
        ("3", C3, "#81c784", "Light green — Elevated",   "≥ 4×",       "Institutional accumulation signal"),
        ("4", C4, "#4caf50", "Green — High",             "≥ 8×",       "Strong directional commitment"),
        ("5", C5, "#fff176", "Light yellow — Very high", "≥ 16×",      "Momentum inflection zone"),
        ("6", C6, "#ffeb3b", "Yellow — Extreme",         "≥ 32×",      "Climax / exhaustion watch"),
        ("7", C7, "#e57373", "Light red — Alert",        "≥ 64×",      "Liquidity vacuum risk"),
        ("8", C8, "#f44336", "Red — Critical",           "≥ 128×",     "Macro event / forced liquidation"),
        ("9", C9, "#ffffff", "White — Climactic",        "≥ 256×",     "Historic event volume"),
    ]
    header = [
        Paragraph('<font color="#2196f3"><b>Tier</b></font>', sBody),
        Paragraph('<font color="#2196f3"><b>Swatch</b></font>', sBody),
        Paragraph('<font color="#2196f3"><b>Name</b></font>', sBody),
        Paragraph('<font color="#2196f3"><b>RVOL Threshold (base 2)</b></font>', sBody),
        Paragraph('<font color="#2196f3"><b>Market Interpretation</b></font>', sBody),
    ]
    rows = [header]
    for tier, bg, hex_str, name, thresh, interp in tiers:
        txt_col = black if bg == C9 or bg == C5 or bg == C6 else white
        rows.append([
            Paragraph(f'<font color="#ffffff"><b>{tier}</b></font>', sBody),
            Table([[""]], colWidths=[12*mm], rowHeights=[5*mm],
                  style=TableStyle([("BACKGROUND",(0,0),(0,0),bg),
                                    ("GRID",(0,0),(-1,-1),0.3,LGREY)])),
            Paragraph(f'<font color="{hex_str}">{name}</font>', sBody),
            Paragraph(f'<font color="#ffeb3b">{thresh}</font>', sBody),
            Paragraph(f'<font color="#8a8d99">{interp}</font>', sBody),
        ])
    t = Table(rows,
              colWidths=[10*mm, 14*mm, 46*mm, 38*mm, 67*mm],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  PANEL),
        ("BACKGROUND",   (0,1), (-1,-1), BG),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [BG, PANEL]),
        ("GRID",         (0,0), (-1,-1), 0.3, HexColor("#2a2d3a")),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING",  (0,0), (-1,-1), 5),
    ]))
    return t

# ── Scale comparison table ────────────────────────────────────────────────────
def scale_table():
    header_vals = ["Tier", "Linear", "Quadratic", "True Exp (b=2)", "Fibonacci", "Log-Spaced"]
    linear  = [1,2,3,4,5,6,7,8,9]
    quad    = [1,4,9,16,25,36,49,64,81]
    trueexp = [round(2**i,1) for i in range(9)]
    fib     = [1,2,3,5,8,13,21,34,55]
    logs    = [round(10**(i/8),2) for i in range(9)]
    rows = [[Paragraph(f'<font color="#2196f3"><b>{h}</b></font>', sBody)
             for h in header_vals]]
    for i in range(9):
        rows.append([
            Paragraph(f'<font color="#ffffff"><b>{i}</b></font>', sBody),
            Paragraph(f'<font color="#8a8d99">{linear[i]}</font>', sBody),
            Paragraph(f'<font color="#8a8d99">{quad[i]}</font>', sBody),
            Paragraph(f'<font color="#ffeb3b">{trueexp[i]}</font>', sBody),
            Paragraph(f'<font color="#81c784">{fib[i]}</font>', sBody),
            Paragraph(f'<font color="#64b5f6">{logs[i]}</font>', sBody),
        ])
    t = Table(rows, colWidths=[14*mm,28*mm,28*mm,38*mm,28*mm,34*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  PANEL),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [BG, PANEL]),
        ("GRID",          (0,0),(-1,-1),  0.3, HexColor("#2a2d3a")),
        ("VALIGN",        (0,0),(-1,-1),  "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1),  4),
        ("BOTTOMPADDING", (0,0),(-1,-1),  4),
        ("LEFTPADDING",   (0,0),(-1,-1),  6),
    ]))
    return t

# ── Input reference table ─────────────────────────────────────────────────────
def input_table():
    rows_data = [
        ("USE RELATIVE VOLUME (RVOL)", "bool", "true",
         "Normalise volume against rolling SMA. Eliminates per-instrument manual calibration. Recommended ON for all assets."),
        ("RVOL Lookback Period", "int", "50",
         "Window length N for SMA(volume,N). Shorter = more reactive. Longer = more stable baseline. 20–100 covers most timeframes."),
        ("Tint Background by Z-Score", "bool", "false",
         "Overlays yellow (Z>2) or white (Z>3) background shading to flag statistically extreme volume events."),
        ("Magnitude", "int 1–9", "3",
         "Legacy only (RVOL OFF). Sets order of magnitude: 1=×1, 2=×10, … 9=×100M. Match to typical volume of the instrument."),
        ("Multiplier", "int 1–9", "2",
         "Legacy only. Fine-tunes base unit within the chosen magnitude. base = 10^(mag–1) × mult."),
        ("Scale Type", "string", "True Exp",
         "Mathematical spacing of the 9 volume tiers. See Section 3 for full comparison. True Exponential recommended."),
        ("Exponential Base", "float", "2.0",
         "Base b for True Exponential scale. t_i = b^(i–1). b=2 → each tier requires double the volume of previous."),
        ("Time Frame", "resolution", "(chart)",
         "Override timeframe for Heikin-Ashi OHLC data used in wick plotting and pivot detection."),
        ("Pivot Length", "int", "4",
         "Symmetrical window for pivot detection. A pivot high at bar[L] requires no bar in [0,L–1] higher, and none in [L+1,2L] equal-or-higher."),
        ("Show Lines", "bool", "true",   "Toggle all pivot liquidity lines on/off."),
        ("Show Labels", "bool", "true",  "Toggle volume annotation labels on pivot lines."),
        ("Min Volume Tier (0–9)", "int", "2",
         "Only draw pivot lines where the pivot bar's volume tier ≥ this value. Eliminates low-liquidity noise pivots. Set 4–5 for cleaner charts."),
        ("High/Low Line Style", "string", "dotted",
         "Visual style of drawn lines: solid, dotted, dashed, or arrow variants."),
        ("Show Heikin-Ashi Wick", "bool", "true",
         "Render HA-smoothed wicks colour-matched to current volume tier, revealing candle direction without noise."),
    ]
    header = [Paragraph(f'<font color="#2196f3"><b>{h}</b></font>', sBody)
              for h in ["Parameter", "Type", "Default", "Description"]]
    rows = [header]
    for name, typ, dflt, desc in rows_data:
        rows.append([
            Paragraph(f'<font color="#ffffff"><b>{name}</b></font>', sBody),
            Paragraph(f'<font color="#ffeb3b">{typ}</font>', sBody),
            Paragraph(f'<font color="#4caf50">{dflt}</font>', sBody),
            Paragraph(f'<font color="#8a8d99">{desc}</font>', sBody),
        ])
    t = Table(rows, colWidths=[52*mm, 18*mm, 18*mm, 87*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  PANEL),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [BG, PANEL]),
        ("GRID",          (0,0),(-1,-1),  0.3, HexColor("#2a2d3a")),
        ("VALIGN",        (0,0),(-1,-1),  "TOP"),
        ("TOPPADDING",    (0,0),(-1,-1),  5),
        ("BOTTOMPADDING", (0,0),(-1,-1),  5),
        ("LEFTPADDING",   (0,0),(-1,-1),  5),
    ]))
    return t

# ── Build document ────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    "/home/user/AYA-/Volume_Bars_Lines_Manual.pdf",
    pagesize=A4,
    leftMargin=15*mm, rightMargin=15*mm,
    topMargin=22*mm, bottomMargin=16*mm,
)

story = []

# ══════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════════════════════
story.append(sp(28))
story.append(Paragraph("VOLUME BARS", sTitle))
story.append(Paragraph("AND LINES", sTitle))
story.append(sp(4))
story.append(HR())
story.append(sp(3))
story.append(Paragraph("Pine Script v6  |  Liquidity-Tier Volume Indicator", sSubT))
story.append(sp(2))
story.append(Paragraph("User Manual & Mathematical Reference", sTag))
story.append(sp(12))

# tier swatch showcase on cover
cover_swatches = []
tier_colors = [C0,C1,C2,C3,C4,C5,C6,C7,C8,C9]
tier_labels = ["T0","T1","T2","T3","T4","T5","T6","T7","T8","T9"]
swatch_row  = []
label_row   = []
for i,(c,l) in enumerate(zip(tier_colors, tier_labels)):
    txt = white if c not in (C5,C6,C9) else black
    swatch_row.append(
        Table([[""]], colWidths=[16*mm], rowHeights=[10*mm],
              style=TableStyle([("BACKGROUND",(0,0),(0,0),c),
                                ("GRID",(0,0),(-1,-1),0.5,PANEL)]))
    )
    label_row.append(Paragraph(f'<font color="#8a8d99">{l}</font>',
                                ParagraphStyle("lbl",parent=sBody,alignment=TA_CENTER,fontSize=7)))
swatch_t = Table([swatch_row, label_row],
                 colWidths=[16*mm]*10,
                 style=TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),
                                   ("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
story.append(swatch_t)
story.append(sp(6))
story.append(Paragraph(
    "10-tier volume colour scale  |  grey → light-blue → blue → green → yellow → red → white",
    sCaption))
story.append(sp(14))
story.append(Paragraph("© mellowmichellehe", sTag))
story.append(Paragraph(
    "Built on principles of relative volume analysis, true exponential mathematics,<br/>"
    "liquidity engineering, and statistical significance testing.",
    sTag))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS
# ══════════════════════════════════════════════════════════════════════════════
story.append(sp(4))
story.append(h1("Table of Contents"))
story.append(HR())
toc = [
    ("1.", "Indicator Overview & Philosophy"),
    ("2.", "Mathematical Foundations"),
    ("  2.1", "Relative Volume (RVOL) Normalisation"),
    ("  2.2", "Scale Types: Linear, Quadratic, True Exponential, Fibonacci, Log-Spaced"),
    ("  2.3", "Volume Z-Score & Statistical Significance"),
    ("  2.4", "Tier Assignment Algorithm"),
    ("3.", "Volume Colour Tier Reference"),
    ("4.", "Liquidity Pivot Detection"),
    ("  4.1", "Pivot Mathematics"),
    ("  4.2", "Volume-Tier Filtering"),
    ("  4.3", "RVOL Label Annotation"),
    ("5.", "Input Parameter Reference"),
    ("6.", "Recommended Configurations"),
    ("  6.1", "Crypto (BTC/ETH)"),
    ("  6.2", "Equities & Futures"),
    ("  6.3", "Forex & Low-Volume Assets"),
    ("7.", "Liquidity Engineering Interpretation Guide"),
    ("8.", "Mathematical Appendix"),
]
for num, title in toc:
    is_sub = num.startswith(" ")
    story.append(Paragraph(
        f'<font color="#2196f3">{num}</font>&nbsp;&nbsp;&nbsp;'
        f'<font color="#b0b8d0">{title}</font>',
        sTOCn if is_sub else sTOC))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
story.append(h1("1.  Indicator Overview & Philosophy"))
story.append(HR())
story.append(body(
    "Volume Bars and Lines is a liquidity-tier colouring and structural pivot indicator "
    "for TradingView Pine Script v6. Its core premise is that <b>volume is the footprint "
    "of institutional money</b>: every significant price level that acts as future support "
    "or resistance was created at a moment of abnormally high transactional activity. By "
    "quantifying and colour-coding that activity, the trader can see — at a glance — which "
    "bars carry genuine market conviction and which are low-participation noise."))
story.append(body(
    "The indicator operates on three interlocking layers:"))
story += bullet([
    "<b>Bar colouring</b> — each candlestick is recoloured according to its volume tier (0–9), "
    "giving an immediate visual heat map of market participation across time.",
    "<b>Heikin-Ashi wick overlay</b> — smoothed HA wicks are rendered in the same tier colour, "
    "reducing price noise while preserving directional information.",
    "<b>Liquidity pivot lines</b> — when a pivot high or low forms on a bar whose volume meets "
    "the minimum tier threshold, a horizontal line is extended to the right. These lines mark "
    "genuine liquidity nodes where unfilled orders are likely resting.",
])
story.append(sp(2))
story.append(note(
    "The indicator does NOT repaint. Pivot lines are drawn only after the full "
    "confirmation window (2 × Pivot Length bars) has closed."))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — MATHEMATICS
# ══════════════════════════════════════════════════════════════════════════════
story.append(h1("2.  Mathematical Foundations"))
story.append(HR())

# 2.1
story.append(h2("2.1  Relative Volume (RVOL) Normalisation"))
story.append(body(
    "Raw volume figures are instrument-specific and timeframe-specific: a volume of 1,000 is "
    "enormous for a thinly-traded small-cap but trivial for BTCUSDT. Manual calibration via "
    "Magnitude and Multiplier is therefore fragile and requires adjustment for every instrument. "
    "Relative Volume solves this by expressing each bar's volume as a multiple of its own "
    "rolling average:"))
story.append(formula("RVOL(t)  =  V(t)  /  SMA( V, N )(t)"))
story.append(body(
    "where V(t) is the raw volume at bar t and N is the lookback period (default 50). An RVOL "
    "of 1.0 means exactly average volume. An RVOL of 3.0 means three times the recent average. "
    "This ratio is then compared against the scale thresholds t₁ … t₉ to assign a colour tier:"))
story.append(formula("tier(t)  =  max { i ∈ {0,…,9}  :  RVOL(t) ≥ tᵢ }"))
story.append(body(
    "The SMA lookback N controls sensitivity. A shorter window (20–30) adapts quickly to regime "
    "changes in volume, while a longer window (100–200) provides a more stable baseline, making "
    "outliers more visually prominent."))

story.append(h2("2.2  Scale Types"))
story.append(body(
    "The nine threshold multipliers t₁ … t₉ define the boundaries between colour tiers. "
    "The choice of scale determines how sensitively the indicator responds to volume changes. "
    "Five mathematically distinct progressions are available:"))

story.append(h3("Linear  —  tᵢ = i"))
story.append(body(
    "Uniform steps of 1× RVOL per tier. Appropriate for instruments with stable, "
    "low-variance volume distributions. Provides maximum tier resolution at low "
    "multiples but compresses the upper tiers. Mathematically: an arithmetic sequence."))

story.append(h3("Quadratic (original)  —  tᵢ = i²"))
story.append(body(
    "The original script's 'exponential' mode was in fact a quadratic (polynomial of degree 2) "
    "sequence: 1, 4, 9, 16, 25, 36, 49, 64, 81. This provides moderate separation between "
    "lower tiers and aggressive compression of higher tiers. Growth rate d²tᵢ/di² = 2 "
    "(constant second derivative), characteristic of a parabola."))

story.append(h3("True Exponential  —  tᵢ = bⁱ⁻¹"))
story.append(body(
    "Each successive threshold is b times the previous: 1, b, b², b³, …, b⁸. "
    "With b = 2 the thresholds are 1, 2, 4, 8, 16, 32, 64, 128, 256 × RVOL. "
    "This is the mathematically correct exponential scale — the ratio between consecutive "
    "thresholds is constant (equal to b), which matches the log-normal distribution of "
    "financial volume. This is the <b>recommended default</b>."))
story.append(formula("tᵢ = b^(i−1)     ratio: tᵢ₊₁/tᵢ = b  (constant)"))

story.append(h3("Fibonacci  —  tᵢ ∈ {1, 2, 3, 5, 8, 13, 21, 34, 55}"))
story.append(body(
    "Uses the Fibonacci sequence as thresholds. The golden ratio φ ≈ 1.618 governs "
    "the growth rate of consecutive Fibonacci numbers asymptotically. This scale has "
    "denser resolution in the lower tiers (1–8×) and sparser resolution above, reflecting "
    "the natural clustering of volume events in financial markets."))

story.append(h3("Log-Spaced  —  tᵢ = 10^(i/8)"))
story.append(body(
    "Eight equally-spaced points on a base-10 logarithmic axis from 1 to 10: "
    "1.00, 1.33, 1.78, 2.37, 3.16, 4.22, 5.62, 7.50, 10.00. "
    "This scale is perceptually uniform — equal visual distance on a log chart corresponds "
    "to equal tier width. Useful when the analyst wants symmetric tier separation on a "
    "logarithmic price chart."))

story.append(sp(2))
story.append(h3("Scale Threshold Comparison Table"))
story.append(scale_table())
story.append(Paragraph(
    "All values are RVOL multiples (i.e., 4× = four times average volume). "
    "True Exponential with b=2 is the theoretically optimal choice for log-normally "
    "distributed volume data.", sCaption))

story.append(PageBreak())

# 2.3
story.append(h2("2.3  Volume Z-Score & Statistical Significance"))
story.append(body(
    "Beyond relative ranking, a statistically grounded measure of volume exceptionality "
    "is the Z-score — the number of standard deviations a bar's volume lies above the "
    "rolling mean:"))
story.append(formula("Z(t)  =  ( V(t) − μ(t) )  /  σ(t)"))
story.append(body(
    "where μ(t) = SMA(V, N)(t) and σ(t) = StdDev(V, N)(t) use the same lookback N as RVOL. "
    "Under the assumption that log-volume is approximately normally distributed:"))
story += bullet([
    "<b>|Z| > 2</b>  →  volume exceeds mean by 2σ; occurs in ~2.3% of bars (yellow background tint)",
    "<b>|Z| > 3</b>  →  volume exceeds mean by 3σ; occurs in ~0.13% of bars (white background tint)",
    "These events correspond to earnings releases, macro announcements, liquidation cascades, "
    "and other genuine market-structure-altering events.",
])
story.append(warn(
    "Z-score assumes approximate normality of volume. In crypto markets, volume "
    "distributions are heavily right-skewed (fat tails), so Z > 3 events occur more "
    "frequently than the Gaussian model predicts. Use Z-score tinting as a supplementary "
    "signal, not a primary filter."))

# 2.4
story.append(h2("2.4  Tier Assignment Algorithm"))
story.append(body("The complete tier assignment logic in pseudocode:"))
story.append(mono(
    "avgVol  ← SMA(volume, N)\n"
    "baseUnit ← avgVol               // RVOL mode\n"
    "           OR  10^(mag−1) × mult  // legacy mode\n\n"
    "volNorm ← volume / max(baseUnit, ε)\n\n"
    "tier ← 0 if volNorm < t1\n"
    "        1 if t1 ≤ volNorm < t2\n"
    "        2 if t2 ≤ volNorm < t3\n"
    "        ...\n"
    "        9 if volNorm ≥ t9\n\n"
    "colour ← colourMap[tier]"))
story.append(body(
    "The thresholds t₁ … t₉ are computed once per bar from the selected scale type and base, "
    "then compared against the normalised volume. The assignment is a simple ordered lookup "
    "with O(1) complexity per bar — there is no loop over tiers at runtime."))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — COLOUR TIERS
# ══════════════════════════════════════════════════════════════════════════════
story.append(h1("3.  Volume Colour Tier Reference"))
story.append(HR())
story.append(body(
    "The ten colour tiers form a continuous spectrum from market inactivity (grey) through "
    "moderate participation (blue / green) to extreme liquidity events (red / white). "
    "The thresholds below assume True Exponential scale with base 2 and RVOL mode:"))
story.append(sp(2))
story.append(tier_table())
story.append(sp(2))
story.append(Paragraph(
    "Thresholds shown are RVOL multiples for True Exponential scale b=2. "
    "Under other scales the RVOL values differ — see Section 2.2.",
    sCaption))
story.append(sp(3))
story.append(body(
    "The colour progression follows the visible light spectrum in reverse — cold colours "
    "(blue) for moderate activity, warm colours (yellow → red) for high activity, and white "
    "for the most extreme events. This is consistent with heat-map conventions used in "
    "institutional order-flow analysis tools."))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — PIVOT DETECTION
# ══════════════════════════════════════════════════════════════════════════════
story.append(h1("4.  Liquidity Pivot Detection"))
story.append(HR())

story.append(h2("4.1  Pivot Mathematics"))
story.append(body(
    "A pivot high at bar index p (i.e., bar_index[L] where L = Pivot Length) is defined as:"))
story.append(formula(
    "PivotHigh(p, L)  ≡  ∀ i ∈ [p−L, p−1]: high[i] < high[p]\n"
    "                     ∧  ∀ i ∈ [p+1, p+L]: high[i] ≤ high[p]"))
story.append(body(
    "The left window uses a strict inequality (no bar may exceed the pivot), while the right "
    "window uses a non-strict inequality (bars may equal but not exceed). This asymmetry "
    "prevents double-counting of plateau tops and ensures the most recent occurrence of a "
    "repeated high is selected."))
story.append(body(
    "Symmetrically, a pivot low at bar p is:"))
story.append(formula(
    "PivotLow(p, L)  ≡  ∀ i ∈ [p−L, p−1]: low[i] > low[p]\n"
    "                    ∧  ∀ i ∈ [p+1, p+L]: low[i] ≥ low[p]"))
story.append(body(
    "The total detection window is 2L bars. Increasing L produces fewer, more structurally "
    "significant pivots. Decreasing L produces more frequent, shorter-term pivots. "
    "A value of L = 4–8 is appropriate for swing trading; L = 1–2 for scalping."))
story.append(warn(
    "Pivots are confirmed only after 2L bars have elapsed since the candidate bar. "
    "Lines therefore appear L bars 'late' relative to the pivot price level. "
    "This is non-repainting by design."))

story.append(h2("4.2  Volume-Tier Filtering"))
story.append(body(
    "Not all structural pivots are meaningful liquidity nodes. A pivot formed on below-average "
    "volume indicates that the price level was created without genuine institutional participation "
    "— it is unlikely to act as a strong support or resistance in the future. The Min Volume Tier "
    "parameter filters out these low-quality pivots:"))
story.append(formula("DrawLine(p)  ≡  PivotConfirmed(p)  ∧  Tier(p) ≥ MinTier"))
story.append(body(
    "Recommended values for MinTier:"))
story += bullet([
    "<b>0</b> — Draw all pivots regardless of volume (noisy; useful for debugging or scalping)",
    "<b>2</b> — Blue tier and above: moderate liquidity filter (default)",
    "<b>4</b> — Green tier and above: institutional-grade pivots only",
    "<b>5+</b> — Yellow and above: extreme events only (very sparse; macro timeframes)",
])

story.append(h2("4.3  RVOL Label Annotation"))
story.append(body(
    "Each pivot line is annotated with a label displaying the raw volume and, when RVOL mode "
    "is active, the RVOL ratio at the pivot bar:"))
story.append(formula('Label: "1 234 567  (3.2×)"'))
story.append(body(
    "The raw volume provides an absolute reference for cross-timeframe comparison. "
    "The RVOL multiple immediately communicates how exceptional the event was relative "
    "to the instrument's own history at that time — a 3.2× event means the pivot formed "
    "on volume 3.2 times the 50-bar average, regardless of whether that average is 100 "
    "or 10,000,000 contracts."))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — INPUT REFERENCE
# ══════════════════════════════════════════════════════════════════════════════
story.append(h1("5.  Input Parameter Reference"))
story.append(HR())
story.append(input_table())
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — CONFIGURATIONS
# ══════════════════════════════════════════════════════════════════════════════
story.append(h1("6.  Recommended Configurations"))
story.append(HR())

configs = [
    ("6.1  Cryptocurrency (BTC / ETH / Major Alts)",
     [("Use RVOL",         "ON"),
      ("RVOL Lookback",    "50 (daily)  /  20 (4H)"),
      ("Scale Type",       "True Exponential"),
      ("Exp Base",         "2.0"),
      ("Pivot Length",     "5–8 (daily)  /  3–4 (4H)"),
      ("Min Volume Tier",  "3 (green)"),
      ("Z-Score Tint",     "ON — crypto has frequent outliers")],
     "Crypto volume distributions are highly right-skewed due to leverage liquidations "
     "and exchange-specific flow. RVOL with True Exponential b=2 handles this well. "
     "Enable Z-Score tinting to identify liquidation cascades (Z>3 = white tint)."),

    ("6.2  Equities & Futures (ES, NQ, SPY, Single Stocks)",
     [("Use RVOL",         "ON"),
      ("RVOL Lookback",    "50–100 (aligns with ~2 trading months)"),
      ("Scale Type",       "True Exponential  OR  Fibonacci"),
      ("Exp Base",         "1.5–2.0"),
      ("Pivot Length",     "4–6"),
      ("Min Volume Tier",  "2–3"),
      ("Z-Score Tint",     "ON for earnings plays; OFF otherwise")],
     "Equity volume follows cleaner log-normal distributions than crypto. "
     "Fibonacci scale works well because institutional order size tends to cluster "
     "at Fibonacci multiples of ADTV. The RVOL lookback should span at least one "
     "full earnings cycle (50–100 trading days)."),

    ("6.3  Forex & Low-Volume / Illiquid Assets",
     [("Use RVOL",         "ON  (essential — no absolute volume baseline possible)"),
      ("RVOL Lookback",    "100–200  (very stable baseline needed)"),
      ("Scale Type",       "Log-Spaced  OR  Linear"),
      ("Pivot Length",     "3–5"),
      ("Min Volume Tier",  "1–2  (volume is inherently lower)"),
      ("Z-Score Tint",     "ON — highlights the rare high-volume FX events")],
     "Forex tick volume is a proxy for true volume. Absolute calibration is meaningless. "
     "RVOL is mandatory. Use a long lookback (100–200) to establish a stable baseline "
     "across multiple sessions and DST transitions. Log-Spaced scale provides finer "
     "resolution in the lower RVOL ranges typical of FX."),
]

for title, settings, commentary in configs:
    story.append(h2(title))
    rows = [[Paragraph(f'<font color="#2196f3"><b>Parameter</b></font>', sBody),
             Paragraph(f'<font color="#2196f3"><b>Recommended Value</b></font>', sBody)]]
    for param, val in settings:
        rows.append([
            Paragraph(f'<font color="#ffffff">{param}</font>', sBody),
            Paragraph(f'<font color="#ffeb3b">{val}</font>', sBody),
        ])
    t = Table(rows, colWidths=[60*mm, 115*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  PANEL),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [BG, PANEL]),
        ("GRID",          (0,0),(-1,-1),  0.3, HexColor("#2a2d3a")),
        ("VALIGN",        (0,0),(-1,-1),  "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1),  5),
        ("BOTTOMPADDING", (0,0),(-1,-1),  5),
        ("LEFTPADDING",   (0,0),(-1,-1),  5),
    ]))
    story.append(t)
    story.append(sp(2))
    story.append(body(commentary))
    story.append(sp(3))

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — LIQUIDITY INTERPRETATION GUIDE
# ══════════════════════════════════════════════════════════════════════════════
story.append(h1("7.  Liquidity Engineering Interpretation Guide"))
story.append(HR())
story.append(body(
    "Volume is the mechanism by which price levels acquire significance. A price level "
    "that traded on high volume has a large inventory of filled orders at that level — "
    "both from participants who profited and those who are offside. Both groups create "
    "future order flow at and around that price:"))
story += bullet([
    "<b>Profitable longs at a high-volume low</b> will add to positions on retests "
    "(demand zone reinforcement)",
    "<b>Breakeven / losing longs at a high-volume high that reversed</b> will sell on "
    "retests to exit flat (supply zone / resistance)",
    "<b>Short sellers who sold into a high-volume spike</b> will cover on any revisit "
    "(buy-side demand on pullback)",
])
story.append(sp(2))

story.append(h2("Tier-Based Market Structure Interpretation"))
story += bullet([
    "<font color='#5d606b'>■</font>  <b>Tier 0 (grey):</b> Market is in low-participation drift. "
    "No directional commitment. Avoid entries — any move is easily reversed.",
    "<font color='#64b5f6'>■</font>  <b>Tier 1–2 (light/mid blue):</b> Baseline participation. "
    "Normal trending conditions. Standard S/R analysis applies.",
    "<font color='#81c784'>■</font>  <b>Tier 3–4 (green):</b> Institutional accumulation or distribution. "
    "Pivots at these tiers are high-probability S/R levels. Monitor for follow-through.",
    "<font color='#ffeb3b'>■</font>  <b>Tier 5–6 (yellow):</b> Momentum-driven participation. Often "
    "accompanies breakouts from consolidation or news-driven moves. Lines drawn here are "
    "strong magnet levels for future price action.",
    "<font color='#f44336'>■</font>  <b>Tier 7–8 (red):</b> Potential exhaustion / climax. High "
    "probability of mean reversion following a tier-8 bar. If price reverses at a tier-8 "
    "bar, the resulting pivot line is an extremely high-conviction level.",
    "<font color='#ffffff'>■</font>  <b>Tier 9 (white):</b> Historic event. Black swan / liquidation "
    "cascade / macro catalyst. These levels are permanent structural references. Price will "
    "often return to the Tier-9 bar's high or low years later.",
])
story.append(sp(3))

story.append(h2("Confluence Framework"))
story.append(body(
    "The highest-probability trades occur when multiple signals converge at the same price level:"))

conf_rows = [
    [Paragraph('<font color="#2196f3"><b>Signal</b></font>', sBody),
     Paragraph('<font color="#2196f3"><b>Condition</b></font>', sBody),
     Paragraph('<font color="#2196f3"><b>Conviction</b></font>', sBody)],
    [Paragraph('<font color="#ffffff">Tier-4+ pivot line</font>', sBody),
     Paragraph('<font color="#8a8d99">Price approaches a green-tier pivot level</font>', sBody),
     Paragraph('<font color="#ffeb3b">HIGH</font>', sBody)],
    [Paragraph('<font color="#ffffff">Multi-tier pivot cluster</font>', sBody),
     Paragraph('<font color="#8a8d99">Two or more pivot lines within 0.1% of each other</font>', sBody),
     Paragraph('<font color="#f44336">VERY HIGH</font>', sBody)],
    [Paragraph('<font color="#ffffff">Z-Score tint + pivot</font>', sBody),
     Paragraph('<font color="#8a8d99">Z>2 bar coincides with confirmed pivot</font>', sBody),
     Paragraph('<font color="#f44336">VERY HIGH</font>', sBody)],
    [Paragraph('<font color="#ffffff">Tier escalation</font>', sBody),
     Paragraph('<font color="#8a8d99">3+ consecutive rising-tier bars in a trend</font>', sBody),
     Paragraph('<font color="#4caf50">MODERATE-HIGH</font>', sBody)],
    [Paragraph('<font color="#ffffff">Tier collapse</font>', sBody),
     Paragraph('<font color="#8a8d99">Tier drops from 5+ to 0–1 after a spike</font>', sBody),
     Paragraph('<font color="#8a8d99">EXHAUSTION SIGNAL</font>', sBody)],
]
conf_t = Table(conf_rows, colWidths=[55*mm, 90*mm, 30*mm], repeatRows=1)
conf_t.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,0),  PANEL),
    ("ROWBACKGROUNDS",(0,1),(-1,-1), [BG, PANEL]),
    ("GRID",          (0,0),(-1,-1),  0.3, HexColor("#2a2d3a")),
    ("VALIGN",        (0,0),(-1,-1),  "MIDDLE"),
    ("TOPPADDING",    (0,0),(-1,-1),  5),
    ("BOTTOMPADDING", (0,0),(-1,-1),  5),
    ("LEFTPADDING",   (0,0),(-1,-1),  5),
]))
story.append(conf_t)
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — APPENDIX
# ══════════════════════════════════════════════════════════════════════════════
story.append(h1("8.  Mathematical Appendix"))
story.append(HR())

story.append(h2("A.  Scale Type Formulae"))
math_rows = [
    [Paragraph('<font color="#2196f3"><b>Scale</b></font>', sBody),
     Paragraph('<font color="#2196f3"><b>Formula</b></font>', sBody),
     Paragraph('<font color="#2196f3"><b>Growth Type</b></font>', sBody),
     Paragraph('<font color="#2196f3"><b>Ratio tᵢ₊₁/tᵢ</b></font>', sBody)],
    [Paragraph('<font color="#ffffff">Linear</font>', sBody),
     Paragraph('<font color="#64b5f6">tᵢ = i</font>', sBody),
     Paragraph('<font color="#8a8d99">Arithmetic</font>', sBody),
     Paragraph('<font color="#ffeb3b">→ 1  (constant additive step)</font>', sBody)],
    [Paragraph('<font color="#ffffff">Quadratic</font>', sBody),
     Paragraph('<font color="#64b5f6">tᵢ = i²</font>', sBody),
     Paragraph('<font color="#8a8d99">Polynomial, degree 2</font>', sBody),
     Paragraph('<font color="#ffeb3b">(i+1)²/i²  →  1 as i→∞</font>', sBody)],
    [Paragraph('<font color="#ffffff">True Exponential</font>', sBody),
     Paragraph('<font color="#64b5f6">tᵢ = bⁱ⁻¹</font>', sBody),
     Paragraph('<font color="#8a8d99">Geometric (exponential)</font>', sBody),
     Paragraph('<font color="#ffeb3b">b  (constant multiplicative)</font>', sBody)],
    [Paragraph('<font color="#ffffff">Fibonacci</font>', sBody),
     Paragraph('<font color="#64b5f6">tᵢ = Fᵢ  (Fibonacci)</font>', sBody),
     Paragraph('<font color="#8a8d99">Sub-exponential</font>', sBody),
     Paragraph('<font color="#ffeb3b">→ φ ≈ 1.618</font>', sBody)],
    [Paragraph('<font color="#ffffff">Log-Spaced</font>', sBody),
     Paragraph('<font color="#64b5f6">tᵢ = 10^(i/8)</font>', sBody),
     Paragraph('<font color="#8a8d99">Geometric in log-space</font>', sBody),
     Paragraph('<font color="#ffeb3b">10^(1/8) ≈ 1.334 (constant)</font>', sBody)],
]
mt = Table(math_rows, colWidths=[36*mm, 36*mm, 44*mm, 59*mm], repeatRows=1)
mt.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,0),  PANEL),
    ("ROWBACKGROUNDS",(0,1),(-1,-1), [BG, PANEL]),
    ("GRID",          (0,0),(-1,-1),  0.3, HexColor("#2a2d3a")),
    ("VALIGN",        (0,0),(-1,-1),  "MIDDLE"),
    ("TOPPADDING",    (0,0),(-1,-1),  5),
    ("BOTTOMPADDING", (0,0),(-1,-1),  5),
    ("LEFTPADDING",   (0,0),(-1,-1),  5),
]))
story.append(mt)
story.append(sp(4))

story.append(h2("B.  Why True Exponential Fits Financial Volume"))
story.append(body(
    "Empirical studies of financial market volume consistently find that the distribution "
    "of daily volume is approximately log-normal: log(V) ~ N(μ, σ²). This means the "
    "appropriate measure of 'how exceptional' a volume event is should be expressed on a "
    "logarithmic scale. A threshold system whose boundaries are equally spaced on a log axis "
    "— i.e., a geometric/exponential sequence — will therefore produce tiers that are "
    "equally probable under the log-normal model. Specifically, for a geometric threshold "
    "sequence with base b:"))
story.append(formula(
    "P(Tier = k)  =  Φ( (log(tₖ₊₁) − μ) / σ )  −  Φ( (log(tₖ) − μ) / σ )"))
story.append(body(
    "When tₖ = bᵏ, the log-spacing log(tₖ₊₁) − log(tₖ) = log(b) is constant, "
    "and all tiers span equal intervals on the log-normal CDF. This means — in expectation — "
    "each tier is equally likely to occur, giving maximum information content per tier."))

story.append(h2("C.  RVOL Lookback Selection"))
story.append(body(
    "The RVOL lookback N controls the reference period. The optimal N minimises the "
    "variance of the RVOL estimator while tracking real changes in the volume regime. "
    "A heuristic: N should be long enough to span at least one full market cycle "
    "(accumulation → markup → distribution → markdown), which on daily charts is typically "
    "20–100 bars. For intraday charts, N should span at least one full trading week "
    "(5–7 sessions × bars per session). The default N=50 is a practical compromise "
    "that works across most asset classes and timeframes."))

story.append(h2("D.  Non-Repainting Guarantee"))
story.append(body(
    "The pivot detection algorithm evaluates the candidate bar at offset L only after "
    "both the left window [0, L−1] and right window [L+1, 2L] have fully closed. "
    "At the current bar (offset 0), the earliest pivot that can be confirmed is at "
    "offset 2L. No line is drawn until this confirmation is complete, ensuring the "
    "indicator does not repaint on bar close or during real-time bar formation."))
story.append(formula("Earliest confirmed pivot  =  bar_index − 2L"))
story.append(note(
    "Lines extend to the right with extend.right, so they will appear to 'grow' "
    "as new bars form. This is not repainting — the anchor price and location are "
    "fixed at the moment of confirmation."))
story.append(sp(6))
story.append(HR())
story.append(Paragraph(
    "End of Manual  |  Volume Bars and Lines v6  |  © mellowmichellehe",
    sCaption))

# ── Build ─────────────────────────────────────────────────────────────────────
doc.build(story,
          onFirstPage=on_first_page,
          onLaterPages=on_page)

print("PDF written: Volume_Bars_Lines_Manual.pdf")
