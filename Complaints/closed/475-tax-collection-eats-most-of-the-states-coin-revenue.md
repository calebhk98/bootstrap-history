# Tax collection eats most of the state's coin revenue, and the state lends while it is short

**Status:** closed

In a default Rome the `tax_collection` line costs nearly all the coin the state collects in year one, so the
state is underfunded every year and never builds a surplus. The cost comes from the
`*_BASE_PER_COLLECTOR_WAGE_YEAR` heuristics in `sim/agents/tuning_spending.py` priced at scribe pay.
Measure: open a game with `harness.sim()`, step a year, and compare the treasury's `tax_collection`
outlay with its coin revenue (`state_budget` and `state_surplus` topics set up such games; `state_surplus`
now gives its "stable" state a reserve to work around this).

The same state also makes loans ("loans made" in its outlays) while it has unfunded need and unpaid bids in the
book (`sim/economy/lending.py`), which overdraws its purse once the market clears.

Both need an owner decision on how collection should be costed and whether a short state may lend.

## Playtest evidence (Rome, `play --civ rome_100ad --kit merchant --seed real25`)

What this looks like to a player: within the first two years, interest-group petitions report the state's
office-holders unpaid and army pay below expectation. From about the second decade the army mutinies
repeatedly ("the army, unpaid, has lost its loyalty"), while `money` says "the state owes: 0", because
unpaid pay is a yearly shortfall in `Government.pay_standing_need` (`sim/agents/government.py`) and never
becomes debt. Mutineers seize only a few hundred denarii, because `mutiny()` (`sim/agents/group_servants.py`)
takes from the purse left after the year's spending. Collection is priced at scribe pay, and the `market`
screen in the same game shows the scribe wage far above every other trade's (see 503), so the collection
cost may be most of this. Re-measure once 503 is settled.

## Resolution

- Collection cost, re-measured after 503 (`python3 -m sim.tests --only state_arrears`, first check): the
  `tax_collection` outlay of a default Rome is a small share of its coin revenue, well under half, so the
  per-collector heuristics in `sim/agents/tuning_spending.py` stay as they are, still labelled
  temporary heuristics; the regression check fails if collection ever again takes most of the coin.
- A state that left any standing need unpaid last year, or still owes pay, offers no funds on the loanable
  market (`market_funds` in `sim/engine/economy_capital_market.py`, via `Government.cannot_meet_own_need`).
- Unpaid army and office pay is booked as `record.arrears` by line (`sim/agents/arrears.py`), paid first from
  later revenue, counted in the money screen's "the state owes", and what a mutinous army takes
  (`sim/agents/group_servants.py`) is read from, and cleared out of, those arrears.
- The `state_surplus` topic no longer gives its stable state a reserve.

Foreign states (`ForeignGovernment`) keep no arrears by their own design.
