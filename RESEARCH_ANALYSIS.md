# Academic Research Analysis — Volume Profile / Volumetric Supply & Demand Zones

*A critical, source-based review of the indicator family implemented in this repository
(VolSD v6–v9): volume-at-price analysis (POC, Value Area, HVN/LVN), supply & demand
zones, order blocks / smart-money concepts, and volume-delta confluence.*

*Method note: compiled from targeted searches of arXiv, SSRN, and journal sources.
An automated multi-agent verification pass was rate-limited mid-run; the core claims
below are anchored to primary sources (linked), with unverified or practitioner-grade
material explicitly flagged.*

---

## 1. Core Definition and Mathematical Foundation

**Volume profile.** Over a window, partition price into $B$ bins of width
$\Delta = (P_{max}-P_{min})/B$ and accumulate traded volume per bin (each bar's volume
spread across the bins its range spans):

$$V_b = \sum_{i} \frac{v_i}{\#\text{bins}(i)} \cdot \mathbb{1}[\,\text{bar } i \text{ spans bin } b\,]$$

- **POC** (Point of Control): $\arg\max_b V_b$ — the modal traded price.
- **Value Area** (typically 70%): smallest contiguous interval around the POC with
  $\sum V_b \ge 0.7 \sum_b V_b$, built by greedy expansion from the mode; boundaries are
  VAH/VAL. HVN = local maxima of $V_b$ (acceptance), LVN = local minima (rejection/transit).
- Market Profile (Steidlmayer, CBOT 1980s) is the time-at-price ancestor; volume profile
  replaces TPO counts with actual volume.

**Supply/demand zones.** Practitioner definition: a consolidation ("base") followed by an
impulsive departure; the base range is marked as residual unfilled institutional interest.
Formalizable (as in this repo) as: base range $< k_1 \cdot ATR$, departure bar range
$> k_2 \cdot ATR$ with volume z-score $> k_3$ and body/range $> k_4$.

**Delta / order flow.** Per-bar signed volume $\delta_t = V^{buy}_t - V^{sell}_t$ (or the
close-location proxy when unavailable), and **order flow imbalance (OFI)** at the book level.

**Economic rationale.** Auction market theory: markets alternate between balance
(two-sided trade, HVNs) and imbalance (one-sided moves, LVNs); value-seeking behavior
makes high-volume prices "sticky." The *microstructure* rationale (below) is stronger:
volume-heavy levels coincide with resting limit-order depth, and depth mechanically
attenuates price impact.

---

## 2. Literature Review — Key Papers

| Paper | Venue/Year | Relevance to this indicator family |
|---|---|---|
| Cont, Kukanov & Stoikov, *The Price Impact of Order Book Events* ([arXiv:1011.6402](https://arxiv.org/abs/1011.6402)) | J. Financial Econometrics, 2014 | Price changes over short horizons are driven by **order-flow imbalance**, linearly, with slope inversely proportional to **market depth** — the cleanest mechanism for why deep (high-volume) levels resist price. Volume itself relates to price only noisily. Dataset: 50 NYSE TAQ stocks. *Caution for volume-profile logic: OFI ≫ raw volume as a driver.* |
| Osler, *Support for Resistance* ([FRBNY EPR 2000](https://www.newyorkfed.org/newsevents/news/research/2000/rp000622a); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=888805)) | FRBNY, 2000 | First rigorous test of published S/R levels (6 FX dealers, 1996–98): levels **predict intraday trend interruption** far above chance; power persists ≥5 days; varies by firm and pair. |
| Osler, *Currency Orders and Exchange-Rate Dynamics* ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=923370); [FRBNY SR](https://fraser.stlouisfed.org/files/docs/publications/frbnysr/frbny_sr125.pdf)) + *Stop-Loss Orders and Price Cascades* ([FRBNY SR150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf); [JIMF](https://www.sciencedirect.com/science/article/abs/pii/S0261560604001147)) | J. Finance 2003 / JIMF 2005 | Actual dealer order books (RBS, 9,655 orders, $55B): **take-profits cluster AT round numbers → reversals; stop-losses cluster just BEYOND → breakout cascades.** Direct causal evidence that S/R works because orders physically cluster there — and the exact mechanism behind "liquidity sweeps." |
| Kavajecz & Odders-White, *Technical Analysis and Liquidity Provision* ([RFS 2004](https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=315660)) | RFS, 2004 | **S/R levels coincide with peaks in limit-order-book depth**; moving averages track depth position. Technical levels "work" by *locating liquidity already in place* — consistent with market efficiency. The single best academic justification for volume-profile-style zone logic. |
| Brock, Lakonishok & LeBaron ([J. Finance 1992](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1992.tb04681.x)) | JF, 1992 | Seminal positive result: MA + trading-range-break rules on DJIA 1897–1986 beat RW/AR(1)/GARCH nulls (bootstrap). |
| Sullivan, Timmermann & White ([J. Finance 1999](https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00163)) | JF, 1999 | The rebuttal: White's Reality Check over the full rule universe — BLL-era profits **do not survive data-snooping adjustment out-of-sample**; no profitable simple rule on DJIA/S&P post-adjustment. |
| Park & Irwin, *What Do We Know About the Profitability of Technical Analysis?* ([JES 2007](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-6419.2007.00519.x)) | J. Econ. Surveys, 2007 | Meta-survey of 95 modern studies: 56 positive / 20 negative / 19 mixed — but flags pervasive **data snooping, ex-post rule selection, cost mis-estimation**. Profits robust "at least until the early 1990s," decaying after. |
| Bailey & López de Prado, *Deflated Sharpe Ratio* ([SSRN 2460551](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)); Bailey et al., *Probability of Backtest Overfitting* ([PDF](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)) | 2014/2017 | The modern evaluation standard: correct Sharpe for multiple trials and non-normality; estimate PBO via combinatorial cross-validation. Directly applicable to scoring/weight-tuned indicators like this one. |
| Zhang, Zohren & Roberts, *DeepLOB* ([arXiv:1808.03668](https://arxiv.org/abs/1808.03668)); volume-centred range bars ([arXiv:2103.12419](https://arxiv.org/pdf/2103.12419)) | 2018/2021 | ML lineage: CNN/LSTM on order-book state predicts short-horizon moves; volume-based bar representations improve ML inputs. Order-flow features dominate price-only features. |

**Smart Money Concepts / order blocks:** no peer-reviewed literature exists as of this
writing. Practitioner backtests circulate (e.g., a 2,600-trade retail study claiming
60–65% win rates on displacement+FVG+sweep setups — [Medium, 2026](https://medium.com/@space.garaa/i-backtested-2-600-trades-using-smart-money-concepts-heres-what-actually-works-bb3c671098c6), *unaudited, low evidential weight*).
The academically defensible core of SMC is exactly the Osler mechanism: stop clusters
beyond swing points (sweeps) and order clusters at prior consolidation (blocks/zones).

---

## 3. Empirical Evidence and Performance

- **What is well-evidenced:** (a) S/R levels interrupt intraday trends (Osler, FX);
  (b) technical levels co-locate with LOB depth (Kavajecz & Odders-White, equities);
  (c) order clustering at/beyond round numbers generates reversals and cascades (Osler);
  (d) OFI moves price linearly, scaled by inverse depth (Cont et al.).
- **What is weakly evidenced:** stand-alone *profitability* of S/R or volume-profile
  rules after costs. The BLL→STW→Park-Irwin arc shows headline profits shrinking as
  data-snooping controls tighten and markets adapt post-1990s. No published,
  cost-adjusted, snooping-adjusted study demonstrates durable alpha for volume-profile
  zone trading specifically — absence of evidence, partly because academics rarely test
  practitioner composites.
- **Across assets/regimes:** FX evidence is strongest (order-book studies); equities
  evidence is mechanism-level (depth), not P&L-level; crypto/futures evidence is almost
  entirely practitioner-grade. Reaction-at-level effects are intraday-to-days phenomena;
  predictive power decays with horizon and after level publication/consumption — consistent
  with this repo's freshness/consumption decay design.
- **Transaction costs** flip marginal signal families negative (Park & Irwin); zone
  strategies survive better than high-frequency rules only because trade frequency is
  low and targeted R:R is high — but slippage at sweep moments is systematically adverse.

---

## 4. Theoretical Strengths and Weaknesses

**Why it can work (mechanisms, not folklore):**
1. **Depth attenuation:** impact per unit OFI ∝ 1/depth (Cont et al.); HVNs proxy depth → price decelerates there.
2. **Order clustering:** documented at round numbers and prior levels (Osler) → reversals at zones, cascades through them.
3. **Self-fulfilling coordination:** widely watched levels coordinate limit-order placement (Kavajecz & Odders-White show the depth is real, not imagined).

**Why it can fail:**
1. **Volume ≠ order flow:** raw volume relates to price "noisily" (Cont et al.); profiles built from volume without delta conflate absorption with churn. (Motivates this repo's delta features.)
2. **Ex-post zone subjectivity** → unfalsifiable discretionary use; only mechanical definitions are testable.
3. **Parameter sensitivity & overfitting:** bins, lookbacks, thresholds, and score weights are exactly the multiple-trial setting DSR/PBO warn about.
4. **Adaptation:** edges documented pre-1990s decayed (Park & Irwin); visible retail concepts (SMC) invite crowding and adverse selection at the obvious levels.
5. **EMH objection:** the Kavajecz–Odders-White reading is that levels *locate liquidity* (execution value) rather than forecast returns (alpha) — useful, but a humbler claim.

---

## 5. Advanced / Modern Applications

- **ML on microstructure:** DeepLOB-class models (CNN/LSTM/attention on book states, OFI features) predict short-horizon direction; volume-profile snapshots and volume-bar representations ([arXiv:2103.12419](https://arxiv.org/pdf/2103.12419)) are effective input encodings.
- **This repo's v8/v9 approach** — online logistic regression over normalized zone features with walk-forward-only labels, calibration buckets, and EV gating — is a legitimate small-data instance of the modern paradigm: *learn the weights, freeze predictions, measure calibration.* Its main academic vulnerabilities are per-chart sample sizes and no cross-asset pooling.
- **Evaluation stack to adopt:** Deflated Sharpe / PBO (Bailey–López de Prado), combinatorial purged cross-validation, and null controls (random levels; shuffled volume).

---

## 6. Practical Implementation Guide (condensed)

- Define zones **mechanically** (ATR/z-score normalized), never by eye; freeze at creation (no repaint).
- Weight **delta/OFI over raw volume** wherever a feed exists; treat CLV as a fallback proxy.
- Expect *reaction*, not reversal: first-touch, fresh zones; decay with touches/age (Osler's consumption logic).
- Trade the **edges of value** (VAH/VAL/zone boundaries), target **fair value** (POC) — the auction round-trip.
- Evaluate with event studies (MFE/MAE at touch, bucketed by score), DSR-adjusted Sharpe, and both null controls before sizing anything.
- Pseudocode for profile/zones/scoring: see `DOCUMENTATION*.md` in this repo.

---

## 7. Critical Synthesis and Outlook

**Verdict:** the *mechanisms* behind volume-anchored S/D zones are among the best-documented
in market microstructure (order clustering, depth-scaled impact, liquidity location) — but
published, cost- and snooping-adjusted evidence of *stand-alone alpha* is thin and dated.
The honest posture: this indicator family is a **high-quality conditioning/location tool**
(where liquidity sits, where reactions are probable, where execution is cheap) rather than
a proven money machine. Edges, if present, are regime-dependent, decay with popularity,
and must be re-proven per market with overfitting-robust statistics.

**Gaps:** no peer-reviewed test of volume-profile zone composites; no SMC academic
literature; little cross-asset pooled learning; delta-quality effects on zone reliability
unquantified.

---

## Follow-up Research Questions

1. **Depth-proxy validation:** on futures with full order-book data, how well does the
   volume-profile HVN map onto actual resting depth peaks (Kavajecz–Odders-White replication,
   modern data)? Does zone bounce rate rise monotonically with realized depth?
2. **Delta vs volume ablation:** re-run the v9 learner with (a) raw volume features only,
   (b) delta/OFI features only, (c) both — across FX/crypto/futures. Cont et al. predicts (b) ≫ (a).
3. **Sweep mechanics:** measure bounce probability conditional on a prior stop-run beyond a
   swing (Osler cascade) vs no sweep — quantify the SMC "liquidity grab" premium.
4. **Snooping-robust profitability:** full DSR/PBO evaluation of the mechanical v9 rule set
   across ≥20 instruments, with combinatorial purged CV and random-level nulls.
5. **Crowding decay:** has zone-reaction strength at *publicly obvious* levels (round numbers,
   session highs/lows) weakened since SMC's retail popularization (~2020→), controlling for
   volatility regime?
