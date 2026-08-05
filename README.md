# AYA-

## AXIOM — Institutional Price-Action Framework

**Adaptive eXecution & Institutional Order-flow Mapping** — a non-repainting, self-calibrating
price-action system designed to replace Smart Money Concepts (Order Blocks, FVG/IFVG, BOS/CHoCH,
CISD, Liquidity Sweeps, Premium/Discount) with a single deterministic, causally-sequenced,
score-gated decision framework.

📄 **[Full specification → `docs/AXIOM-Institutional-Price-Action-Spec.md`](docs/AXIOM-Institutional-Price-Action-Spec.md)**

### What it is

A logic specification (no code, by design) for a closed-source Pine Script v6 implementation.
Eight engines, one master state machine:

| Engine | Replaces | Core idea |
|---|---|---|
| **IIDE** — Institutional Intent Detection | Order Blocks | 100-point scored zones with 10 mandatory Tier-1 gates; absorption/initiative decomposition; one-shot test rule |
| **AIE** — Adaptive Imbalance | FVG / IFVG | ATR-normalised dual-gated gaps, A/B/C grading, 50% rendering, 6-gate inversion filter |
| **MSE** — Macro Structure | BOS / CHoCH | ATR-filtered swings, displacement-gated breaks, asymmetric reversal burden of proof |
| **SSE** — State-Shift Trigger | CISD | Precise origin-break with 8 gates including mandatory HTF alignment |
| **CDE** — Confirmation & Decision | *(no analogue)* | Final-edge retest, market/pending arbitration, opposing-setup arbitrator with Hold/Watch/Switch/Stand-Down |
| **MTC** — Multi-Timeframe Confluence | HTF overlays | Auto HTF ladder, dynamic ★ zone upgrades, filter-only HTF POIs |
| **LCC** — Liquidity & Clutter Control | Liquidity tools | Sweep-gated display, sub-additive zone merging, proximity-ranked display cap |
| **RMD** — Risk & Trade Desk | *(no analogue)* | Universal cross-asset sizing, R-sanity vetoes, mobile Trade Guide Panel |

### The two central innovations

1. **The Sequence Lock** — SMC's noise comes from four primitives firing independently, where any
   coincidental overlap gets narrated as "confluence." AXIOM requires stages to occur *in causal
   order, each inside a bounded expiry window*, collapsing signal count by 1–2 orders of magnitude
   while making every survivor mechanistically coherent.

2. **The Dual Gate** — every threshold is an absolute floor *AND* a rolling percentile of that
   metric's own recent distribution, so the system self-calibrates to any instrument, timeframe, and
   volatility regime without re-tuning.

### Scope of claims

Structural superiority (fewer signals, zero repainting, cross-asset portability, deterministic
opposing-trade decisions) is verifiable by inspection. Win rate and expectancy are **not** asserted —
§19 of the spec defines the validation protocol, including a gate ablation study designed to identify
and delete filters that turn out to be decoration.
