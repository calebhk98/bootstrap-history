# The state budget models only an army and officials, so every state is in surplus and the need-driven levy never fires

**Status:** open - found while building 109; next: more standing lines (works, court, dole, navy, war), then re-measure

The government's standing need is an army (the civilisation's opening `standing_army`, held at the same share of the people, paid at the labourer's wage and equipped by `military_logistics` iron) and a corps of officials (`ADMINISTRATIVE_SPAN`). Its revenue is the economy's yield (society output times `starting_tax_share` times state capacity). Measure both over a long run:

    python3 sim/actor_ledger.py rome_100ad 200 1

Every civilisation runs a large surplus: the reserve grows every year, the state never goes short, so `Government.seek_shortfall` sets both levy rates to zero and the founder is never levied (only the confiscation tail and nothing else reaches the treasury from the founder). Before this change a large founder paid a fixed per-civilisation share once the state noticed him; now he pays only when the state is short.

The cause is that revenue was fitted to represent all of a state's spending (`starting_tax_share` is read as a share of the whole economy) while the budget names only two of its uses. What is missing is what a state maintains and cannot skip: public works and roads (needs a stock of works to maintain), the court and the dole, a navy, and war (the army's size and equipment tempo should rise with the threat the civilisation's hazards describe, such as `sack_chance`, instead of staying at the opening share). Each needs a physical basis, not a share of revenue (CLAUDE.md 4.1).

Until then the baseline founder escapes taxation that the real state would have charged. Under a stress run (the same Rome with eight times the army, or Han with twenty times) the mechanism works end to end: reserve drains, spending is cut, the levy rises to the ceiling, the founder is taxed from the notice line.
