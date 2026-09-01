# 00 — Session Context and Market Structure Changelog

## Research session record

**Session:** RS-001
**Date:** 2026-09-01
**ALAT version produced:** v0.1
**Research access:** Web search available. Model knowledge cutoff May 2026; the ~4-month gap was
checked by targeted search (see changelog). Coverage is partial, not exhaustive.

---

## 1. Live instrument context (required at the start of every session)

The framework is instrument-specific. Two primary research instruments are proposed, with a third
for regime-diversity testing. Every field below must be re-established at each session — none of it
is permanent.

### Primary instrument A — CME E-mini S&P 500 (ES)

| Field | Value | Confidence |
|---|---|---|
| Instrument | ES front-month future (roll: quarterly, volume-based) | High |
| Market | Equity index futures | High |
| Venue | CME Globex (single central limit order book — no NMS fragmentation) | High |
| Trading hours | Sun 18:00 ET – Fri 17:00 ET, 60-min daily halt 17:00–18:00 ET | High — verify against current CME calendar |
| Tick size | 0.25 index points = $12.50 per contract | High |
| Typical spread | Overwhelmingly 1 tick at the touch during RTH; large resting queues | High (qualitative) — **quantitative distribution must be measured, not assumed** |
| Notional traded | Reported ≈ $500B/day notional, ~10× the value traded across S&P 500 ETFs | Medium — CME marketing material, verify independently |
| Volatility regime | **UNKNOWN — MUST BE MEASURED AT SESSION START.** No estimate is asserted here. |
| Liquidity regime | **UNKNOWN — MUST BE MEASURED AT SESSION START.** |
| Data resolution available | CME MDP 3.0 provides Market-By-Order (L3). This is the highest-value feed for ALAT. | High |

**Why ES is the primary research instrument:** it is the closest thing in existence to a *clean*
continuous double auction — one book, one venue, no Reg NMS routing, no payment for order flow, no
lit/dark split, no round-lot definition, no odd-lot problem, and full L3 order-level data. If the
core ALAT claims cannot be demonstrated on ES, fragmentation is not the reason they failed.

### Primary instrument B — SPY (US equities, fragmented)

| Field | Value | Confidence |
|---|---|---|
| Market | NMS stock (ETF) | High |
| Venue | Fragmented across ~16 lit exchanges + ~30 ATSs + wholesaler internalization | High |
| Trading hours | 09:30–16:00 ET RTH; pre/post sessions; **extended-hours regime changing Dec 2026 (see changelog)** | High |
| Tick size | $0.01 today; **$0.005 regime pending, see changelog CL-2026-01** | High |
| Typical spread | Commonly 1 tick, i.e. spread-constrained (this matters — see below) | Medium |
| Off-exchange share | Reported >50% of consolidated volume market-wide since 2024–25 | Medium — see changelog CL-2026-03 |

**Why SPY is included:** it is the adversarial case for ALAT. The visible book is a fraction of true
liquidity. If a resilience-based method works on ES but not SPY, the framework's domain of validity
is "consolidated books," which is a finding, not a failure.

### Diversity instrument C — a liquid crypto perpetual (e.g. BTC perp on a major venue)

Included solely to test **regime and market-structure generality**: 24/7, no auctions, no
circuit breakers, different participant mix, funding-rate mechanics, and full L3 data availability.
A rule that survives ES + SPY + BTC perp has survived three genuinely different microstructures.

### Regulatory environment (US, as of 2026-09-01)

- SEC Reg NMS as amended by the 2024 tick-size/access-fee/round-lot/odd-lot rules — phased
  compliance, see changelog.
- CFTC actively reshaping the boundaries of futures: perpetual contracts, 24/7 listing standards.
- 24-hour equities trading moving from ATS-only to exchange-operated.

### Major scheduled catalysts (must be re-pulled each session)

**NOT LISTED HERE ON PURPOSE.** A hardcoded calendar rots. Each session must pull the live
calendar: CPI, PPI, PCE, NFP, JOLTS, FOMC (statement, presser, minutes, SEP), Treasury auctions,
ISM, retail sales, quarterly index rebalance dates, monthly/quarterly OPEX, and the specific
instrument's earnings/settlement events. **UNTESTED HYPOTHESIS — DATA REQUIRED** for any claim about
event-conditional behavior.

---

## 2. MARKET STRUCTURE CHANGELOG

Append-only. Each entry records what changed, what it mechanically implies, and which ALAT rules
become suspect. **A rule is never assumed still valid because it worked historically.**

---

### CL-2026-01 — Sub-penny quoting for tick-constrained NMS stocks

- **DATE:** SEC adopted Sept 2024. Compliance originally first business day of Nov 2025;
  reporting indicates temporary exemptive relief moved implementation to **first business day of
  November 2026**. *Confidence: medium — verify current compliance date directly with SEC/SRO
  notices before relying on it.*
- **CHANGE:** Rule 612 amended to add a $0.005 minimum pricing increment for NMS stocks priced ≥$1
  whose Time Weighted Average Quoted Spread over an evaluation period is ≤$0.015. Rule 610 access
  fee caps lowered. Round-lot definition tiered by price.
- **MARKET AFFECTED:** US equities and ETFs — disproportionately the most tick-constrained,
  highest-volume names. **SPY is a canonical tick-constrained name.**
- **EXPECTED MICROSTRUCTURE CONSEQUENCE:**
  1. Queues at the touch fragment across twice as many price points → **average displayed size per
     price level falls, and queue priority becomes worth less.**
  2. Effective spread should compress; realized spread for liquidity providers compresses with it.
  3. Price-time priority weakens as a strategic barrier → **more quote flickering, higher
     cancel-to-trade ratios, faster book turnover.**
  4. Any statistic that is *counted in ticks* (levels swept, ticks displaced) becomes
     non-comparable across the boundary date.
- **WHICH ALAT RULES MAY NEED REVISION:**
  - Anything using **tick counts** rather than volatility-normalized or spread-normalized distance —
    `LDV`, sweep-depth measures, stop distances. **All must be defined in σ or spread units, never
    ticks.** (This has been made a standing design rule; see `docs/04-state-variables.md`.)
  - `RRI` (Replenishment Resilience Index): "restored at the same price" becomes a different event
    when the price grid halves. Requires re-estimation of the baseline, and results must not be
    pooled across the boundary.
  - Any passive-fill assumption in the cost model: queue position value changes discontinuously.
  - **Practical directive: for equities, treat Nov 2026 as a hard regime boundary. Do not pool
    training data across it without an explicit structural-break test.**

---

### CL-2026-02 — Exchange-operated near-24-hour US equity trading

- **DATE:** SEC approved a 23-hour trading rule 2026-04-10. Nasdaq overnight session (21:00–04:00
  ET) and NYSE Arca extended hours both targeting **2026-12-06** launch, contingent on further
  approval and SIP readiness. SEC roundtable on 24-hour trading preparations held/scheduled
  2026-09-17. *Confidence: medium-high on direction, medium on exact dates — re-verify.*
- **CHANGE:** Overnight trading migrates from FINRA-registered ATSs (already active, e.g. Blue
  Ocean, 24X) to primary exchanges, with a daily pause ~20:00–21:00 ET for trade-date rollover.
- **MARKET AFFECTED:** US equities and ETFs.
- **EXPECTED MICROSTRUCTURE CONSEQUENCE:**
  1. **The overnight gap begins to disappear as a discrete object.** Overnight risk becomes a
     continuous-but-thin trading session rather than a jump.
  2. The 09:30 opening auction loses some of its information-aggregation role — less accumulated
     unexpressed demand to clear. Opening-drive behavior should weaken in magnitude.
  3. A new, structurally thin session appears with its own liquidity supply function — likely
     dominated by a small number of automated providers with wide risk limits.
  4. Session-conditional statistics estimated on pre-2026 data may not transfer.
- **WHICH ALAT RULES MAY NEED REVISION:**
  - **The entire temporal-structure module** (`docs/03-cycle.md` §Session Architecture). Session
    definitions must become configuration, not constants.
  - Any rule keyed to "the open," "the gap," or "overnight range."
  - `LSI` (Liquidity Stress Index) thresholds must be estimated **per session**, because a normal
    overnight book will look like a daytime liquidity crisis on any pooled scale.

---

### CL-2026-03 — Sustained majority off-exchange execution

- **DATE:** Off-exchange share first exceeded 50% of consolidated volume in Nov 2024; reported to
  have remained at or above that level through 2025–2026. *Confidence: medium on the trend
  (Nasdaq/Cboe research corroborate direction); low on any specific percentage — several sources
  found are low-quality aggregators. **Do not use any specific figure without pulling TRF/CTA data
  directly.***
- **CHANGE:** The majority of US equity share volume prints away from lit exchanges — wholesaler
  internalization of retail flow plus ATS/dark execution.
- **MARKET AFFECTED:** US equities and ETFs.
- **EXPECTED MICROSTRUCTURE CONSEQUENCE:**
  1. The lit book is a **biased, non-random sample** of trading interest. Retail marketable flow is
     largely absent from it; what reaches the lit book is disproportionately institutional,
     algorithmic, and adverse-selecting.
  2. Consolidated tape prints arrive with venue-dependent latency and no reliable aggressor flag →
     signed-volume estimates on equities are noisier than on futures.
  3. "Absorption" observed on the lit book may be a wholesaler hedging an internalized position —
     i.e. an *echo* of a trade that already happened elsewhere, not new information.
- **WHICH ALAT RULES MAY NEED REVISION:**
  - **`OFI` and any signed-volume measure on equities.** Aggressor inference via Lee-Ready or tick
    rule must be validated, and its error rate carried through as measurement noise.
  - The absorption/exhaustion distinction (`APS`) — the echo problem is a direct alternative
    explanation and must be an explicit control.
  - **Standing directive: develop and validate every mechanism on ES (consolidated book, true
    aggressor flags) before attempting equities.**

---

### CL-2026-04 — 0DTE options as a dominant share of index options volume

- **DATE:** Ongoing; Cboe reported SPX 0DTE share reaching record levels in 2026 (a February 2026
  figure of ~63% of SPX volume is reported; ~3.3M contracts/day record in June 2026).
  *Confidence: medium-high that 0DTE is a majority of SPX volume; medium on specific figures —
  Cboe is the primary source and should be cited directly, not via secondary write-ups.*
- **CHANGE:** A majority of S&P 500 index option volume expires the same day.
- **MARKET AFFECTED:** SPX/SPY/ES complex, and by extension index-linked intraday behavior.
- **EXPECTED MICROSTRUCTURE CONSEQUENCE:**
  1. A large, **price-contingent, non-discretionary** hedging flow is superimposed on the
     underlying's order flow, with intensity that peaks intraday and concentrates near strikes.
  2. Dealer gamma sign plausibly modulates realized intraday range: long-dealer-gamma conditions
     mechanically damp displacement (dealers sell rallies / buy dips to stay neutral); short gamma
     amplifies it. **The direction of this mechanism is well-motivated; the magnitude and the
     reliability of estimating dealer sign are NOT established here.**
  3. This is the most distinctive structural feature separating 2026 intraday dynamics from any
     market Wyckoff observed. It is a *feedback loop*, not a participant.
- **WHICH ALAT RULES MAY NEED REVISION:**
  - Everything about continuation vs. reversion after displacement. This is the substance of
    hypothesis **H3**.
  - **Caution flag:** dealer positioning is *estimated*, never observed. Open interest does not
    reveal which side is the dealer. Any ALAT rule using gamma exposure must carry an explicit
    uncertainty band and must be tested for whether the sign model, not the mechanism, drives
    results.

---

### CL-2026-05 — CFTC opening the door to 24/7 futures and onshore perpetuals

- **DATE:** May–Aug 2026. CFTC approved a bitcoin perpetual futures contract on a registered DCM
  and issued a policy statement on perpetual submissions; issued a request for comment (comment
  period extended) on extending standard futures to 24/7 trading and on energy perpetuals. CME's
  1-oz gold contract moved to 24/7 on 2026-07-24; CME's 24/7 crude proposal was not permitted.
  CME filed suit against the CFTC in June 2026 over classification of perpetuals as futures rather
  than swaps. *Confidence: medium-high on the shape of events; verify specifics from CFTC releases.*
- **CHANGE:** The regulatory boundary between "futures," "perpetuals," and "24/7 markets" is
  actively being redrawn in the US.
- **MARKET AFFECTED:** Futures broadly; digital-asset and energy derivatives first.
- **EXPECTED MICROSTRUCTURE CONSEQUENCE:**
  1. If 24/7 spreads to major contracts, the daily settlement/maintenance halt — a structural
     anchor for session models and for the daily inventory-flattening cycle — weakens.
  2. Perpetual contracts introduce **funding-rate mechanics** as a new recurring, scheduled,
     position-contingent flow with no analogue in dated futures.
  3. Fragmentation risk: a contract listed as a perpetual on one DCM and as a dated future on
     another creates a new basis and a new arbitrage-propagation channel.
- **WHICH ALAT RULES MAY NEED REVISION:**
  - Session architecture (again). Any rule assuming a daily flat-inventory reset for market makers.
  - The crypto-perp diversity instrument must have **funding timestamps** included as a control —
    otherwise funding-driven flow will be misread as informational flow.

---

## 3. Standing directive on structural change

Every ALAT rule must record the **structural preconditions** it depends on (tick regime, session
architecture, aggressor-flag availability, venue consolidation, derivative overlay). When a
changelog entry invalidates a precondition, the rule reverts to **LEVEL 0** until re-tested. It is
not grandfathered.

## Sources consulted this session

- [SEC — Tick Sizes small entity compliance guide](https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/tick-sizes)
- [SEC press release 2024-137 — Reg NMS amendments](https://sec.gov/newsroom/press-releases/2024-137)
- [Davis Polk — Reg NMS resized: tick sizes, access fees, lot sizes](https://www.davispolk.com/insights/client-update/reg-nms-resized-sec-adjusts-tick-sizes-lowers-access-fees-and-accelerates)
- [Sidley — SEC adopts rules modifying minimum pricing increments](https://www.sidley.com/en/insights/newsupdates/2024/10/sec-adopts-rules-modifying-minimum-pricing-increments-access-fee-caps-and-order-transparency)
- [SEC — Roundtable on preparations for 24-hour trading](https://www.sec.gov/newsroom/press-releases/2026-69-sec-announces-roundtable-preparations-24-hour-trading)
- [NYSE — Extended Hours Trading FAQ (Aug 2026)](https://www.nyse.com/publicdocs/nyse/NYSE_Extended_Hours_Trading_FAQ.pdf)
- [Capco — US equities extended trading hours: 24x5 in 2026](https://www.capco.com/intelligence/capco-intelligence/us-equities-extended-trading-hours)
- [Cboe — SPX 0DTE options share](https://www.cboe.com/insights/posts/spx-0-dte-options-jumped-to-record-56-share-in-feb/)
- [Cboe — Evaluating the market impact of SPX 0DTE options](https://www.cboe.com/insights/posts/volatility-insights-much-ado-about-0dtes-evaluating-the-market-impact-of-spx-0dte-options)
- [CFTC — Comment request on 24/7 futures and energy perpetuals](https://www.cftc.gov/PressRoom/PressReleases/9259-26)
- [Cleary Gottlieb — Perpetual contracts and 24/7 trading on CFTC-regulated markets](https://www.clearygottlieb.com/news-and-insights/publication-listing/the-market-that-never-sleeps-perpetual-contracts-and-24-7-trading-on-cftc-regulated-markets)
- [Katten — Perpetual futures come onshore](https://katten.com/perpetual-futures-come-onshore-the-cftcs-new-regulatory-framework)
- [Nasdaq — Off-exchange trading increases across all types of stocks](https://www.nasdaq.com/articles/exchange-trading-increases-across-all-types-stocks)
- [CME — E-mini S&P 500 overview](https://www.cmegroup.com/markets/equities/sp/e-mini-sandp500.html)
