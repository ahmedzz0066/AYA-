# 06 — Exact Data Required

> Nothing in this repository can advance beyond **Level 1** until this data is acquired.
> Everything below is a shopping list with justification, cost tiers, and the specific
> failure mode that occurs if the tier is not met.

## Principle

Each dataset is justified by the **specific variable it enables**, and each carries a **degradation
path** stating what is lost if only a cheaper tier is available. This is deliberate: the honest
answer to "do you need L3 data?" is "we do not know yet, and RQ-8/RQ-9 are designed to find out."
Buying MBO before running the information-value test is buying an answer to an unasked question.

---

## Tier 1 — Minimum viable (enables H2 only)

| Dataset | Specification | Enables |
|---|---|---|
| **CME MDP 3.0 MBP-10, ES front month** | Nanosecond exchange timestamps, 10 levels each side, every book update, with aggressor side on trades | `OFI`, `LAM`, `PRE`, `AAS`, `LSI` |
| **Trade tape with aggressor flags** | CME publishes aggressor side directly — this is a major advantage over equities | Signed volume, trade intensity, trade-size distribution |
| **Contract roll schedule** | Volume-based roll dates, front-month identification | Continuous series construction |
| **Session calendar** | Holidays, early closes, halts, maintenance windows | Session-conditional statistics |
| **Fee schedule** | Exchange + clearing + NFA fees per contract, by membership tier | Cost model |

**History required.** Minimum 3 years; **5+ preferred**, and the requirement is *not* about sample
size — it is about **regime count**. Three calm years is one regime. The dataset must contain at
minimum: a low-volatility grind, a volatility shock, and a sustained high-volatility period. If the
available history contains only one regime, no result can reach Level 5, and that limitation must be
stated in the results rather than glossed.

**Vendors.** Databento (CME MDP 3.0, MBP-10 and MBO), CME DataMine (authoritative), Nasdaq Data
Link. **Verification requirement:** reconstruct the book from the feed and confirm the reconstructed
BBO matches published BBO message-for-message (this is the direct audit of `A1`, and it also
smoke-tests the entire ingestion pipeline before any research is done on top of it).

---

## Tier 2 — Order-level (required for H1; enables RQ-8)

| Dataset | Specification | Enables |
|---|---|---|
| **CME MDP 3.0 MBO (Market-By-Order), ES** | Individual order add / modify / cancel / trade messages with order IDs and queue position | **`RRI`, `CIR`** — and nothing else does |

**Why it is not optional for H1.** `CIR` requires separating cancelled volume from executed volume.
MBP feeds report *net depth change* and cannot distinguish them at all. `RRI` requires knowing
whether restored depth is a *new* order or a *modified* one — again only visible with order IDs.

**Cost note.** MBO is substantially larger and more expensive than MBP-10 in both storage and
processing. **Recommended sequence: run H2 on Tier 1 first.** If H2 fails, Tier 2 is not purchased,
and a great deal of money is saved by an experiment that cost almost nothing. This ordering is a
research-design decision, not a budget compromise.

---

## Tier 3 — Derivatives overlay (required for H3)

| Dataset | Specification | Enables | Trap |
|---|---|---|---|
| **OPRA trades & quotes, SPX + SPXW** | Full quote and trade history; nanosecond stamps | Implied vol, skew, 0DTE activity | Enormous volume; requires filtering strategy declared in advance |
| **OCC / Cboe open interest** | Per-strike, per-expiry, **with publication timestamps** | $\widehat{G}$, $d^{\text{strike}}$ | **Published post-session. Same-day OI is look-ahead. Prior session only.** |
| **Dividend & rate curve** | For Greeks | $\widehat{G}$ | Small effect intraday; use a documented approximation |
| **Index level (SPX), ETF (SPY), futures (ES)** | Synchronized | Basis $B_t$, cross-market tests | **Timestamp alignment is the dominant risk** — see `A8` |

**Explicit warning carried forward from `A5` / SV7:** no OI dataset reveals dealer positioning. Every
$\widehat{G}$ is a sign model applied to observed OI. This is the weakest data dependency in the
entire program and it must be stated in any result that uses it.

---

## Tier 4 — Generality testing (required for Level 5)

| Dataset | Purpose |
|---|---|
| **Nasdaq TotalView-ITCH or Databento DBEQ (SPY)** | Fragmented-market test; MBO available for one venue only — the consolidated picture is *not* available at order level, which is itself a finding about `CL-2026-03` |
| **Crypto perpetual L3 (major venue)** | 24/7, no auctions, different participant mix, **funding timestamps mandatory as a control** |
| **A second futures contract (e.g. NQ, CL, ZN)** | Cross-asset generality within a consolidated-book structure |

---

## Execution-realism data (required before any Level 6/7 claim)

| Dataset | Why it cannot be skipped |
|---|---|
| **Measured latency distribution** (own infrastructure → venue) | Decision lag $\delta$ is a *measured* parameter, not a guess |
| **Own historical fills, if any exist** | The only way to calibrate a slippage model against reality rather than assumption |
| **Historical margin requirements** | Position sizing and risk-of-ruin are wrong without them |
| **Historical exchange fee schedules** | Fees change; using today's schedule on five-year-old data is a small but systematic bias |

---

## Data hygiene requirements

1. **Point-in-time integrity.** Every field must be usable only from the moment it was actually
   published. OI, settlement prices, and index constituent lists are the classic offenders.
2. **No survivorship in instrument selection.** ES/SPY are chosen for liquidity, and this is a
   *known* selection: results transfer only to comparably liquid instruments, and that limitation is
   part of the result.
3. **Clock discipline.** Exchange timestamps only. Never vendor receipt timestamps for anything
   cross-venue. Record the clock source for every dataset.
4. **Corporate actions** (equities) applied point-in-time, not retroactively.
5. **Raw data is immutable.** All cleaning is a reproducible transformation from raw, version
   controlled and re-runnable. If a cleaning step cannot be re-run from raw, its output cannot be
   used in a result.

---

## Recommended acquisition sequence

| Step | Action | Decision gate |
|---|---|---|
| 1 | Tier 1 on ES, ~1 year | Pipeline built; book reconstruction audit passes (`A1` verified) |
| 2 | Extend Tier 1 to full history | **Run H2.** If H2 fails → stop, record in graveyard, do not buy Tier 2 |
| 3 | Tier 2 (MBO), 1 year | **Run RQ-8/RQ-9 information-value tests.** If `CIR`/`RRI` add nothing → do not extend |
| 4 | Extend Tier 2 | Run H1 |
| 5 | Tier 3 | Run H3 |
| 6 | Tier 4 | Generality; Level 5 attempt |

**The gates are the point.** Each step is authorized only by the result of the previous one. A
research program that buys all the data first has committed to finding something.
