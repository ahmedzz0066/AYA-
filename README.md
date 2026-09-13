# AYA-Claude

Trading indicators, derived from first principles.

## Indicators

### [Hidden Liquidity Profile (HLP)](indicators/hidden_liquidity_profile.pine) · Pine Script v6

Estimates where resting orders are hiding, by inverting the one thing a matching engine
guarantees: price moves only when aggressive orders exhaust resting ones. So **volume that
did not move price is evidence of hidden size**, and displacement per unit of volume becomes
an inverse measure of it.

Where a volume profile asks *"where did trade happen?"*, HLP asks *"where did trade happen
without result?"* — set its `γ` to 0 and it degenerates exactly into a volume profile; raise
it and the two start pointing at different prices.

Three terms of evidence: **absorption** (volume that did no work), **stop pools** (swept
extremes), and **voids** (prices that traded on nothing, subtracted). Bar settlement recovers
which side the resting orders were on.

📖 **[Full derivation, reading guide and limitations](docs/hidden-liquidity-profile.md)**
