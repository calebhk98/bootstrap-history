# The state budget models only an army and officials, so every state is in surplus and the need-driven levy never fires

**Status:** partly - the budget lines, threat-driven army and reserve ceiling are built, revenue now comes from declared forms (315), and borrowing needs a technology (316, closed); what is left is the surplus 315 records

The government's standing need is an army (it wants the civilisation's opening `standing_army` share of the people and keeps what it can fund, changing by at most `ARMY_ADJUSTMENT_RATE` a year; paid at the labourer's wage and equipped by `military_logistics` iron) and a corps of officials (`ADMINISTRATIVE_SPAN`). Its revenue is society output times `starting_tax_share` times state capacity; a visible founder or firm pays the same share of its own income. Measure both over a long run:

    python3 sim/actor_ledger.py rome_100ad 200 1

Every civilisation runs a large surplus: the reserve grows every year, the state never goes short, so `Government.seek_shortfall` sets both levy rates to zero and the founder pays only the ordinary share and the confiscation tail. Before the budget a large founder paid a fixed per-civilisation share (up to about a quarter of income) once the state noticed him; now the ordinary share is a few per cent.

The cause is that revenue was fitted to represent all of a state's spending (`starting_tax_share` is read as a share of the whole economy) while the budget names only two of its uses. What is missing is what a state maintains and cannot skip: public works and roads (needs a stock of works to maintain), the court and the dole, a navy, and war (the army's size and equipment tempo should rise with the threat the civilisation's hazards describe, such as `sack_chance`, instead of only following the population and what the state can pay). Each needs a physical basis, not a share of revenue (CLAUDE.md 4.1).

Until then the baseline founder escapes taxation that the real state would have charged. Under a stress run (the same Rome with eight times the army, or Han with twenty times) the mechanism works end to end: reserve drains, spending is cut, the levy rises to the ceiling, the founder is taxed from the notice line.

Built since: `budget_lines.py` (each line from a stock: road length and coast from the tiles in `sim/world/territory.py`, town dwellers, officials), `army_wanted` raised by the civilisation's active `sack_chance` hazards, and a reserve ceiling (`RESERVE_CEILING_YEARS_OF_NEED`) beyond which a surplus is spent on unnamed things. Re-measure with `python3 sim/budget_series.py rome_100ad 200 1` (the strategy-driven run is slow after the founder grows; `BUDGET_SERIES_IDLE_FOUNDER=1` runs the state alone). What is left is in 315.

Update: the revenue half of this complaint (a fitted share standing for every use of revenue) is replaced by declared forms on modelled bases (315); the levy still fires only when the state goes short, which a healthy state does not, so the remaining work is spending the surplus on named things with a physical basis (315).
