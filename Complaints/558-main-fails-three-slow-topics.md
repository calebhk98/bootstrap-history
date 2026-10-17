# Main fails three slow topics

**Status:** open

Measured on `origin/main` at f0ff751d with `python3 -m sim.tests --slow --only market_records_ownership,economy_tin_dearer_than_copper,insolvency_whole_game`:

- `market_records_ownership`: "no module outside the market writes a market record" names
  `sim/engine/economy_electricity.py` writing `market_flows`.
- `economy_tin_dearer_than_copper`: tin shows far cheaper against copper than the labour its recipe embodies
  (511).
- `insolvency_whole_game`: a ruined founder's debt climbs past the credit limit once the settlement has run,
  and the founder's cash keeps falling instead of rebuilding (524).

A red slow suite on the default branch means every branch's slow run starts red and its own regressions are
read against noise. Each failure needs a fix or, where the subject is an open design issue, a pinned status
with the test kept honest.
