# One concern shows a different running cost on every screen, and the opening charge is never printed

**Status:** closed - every screen quotes running cost now and at full staffing; open names its charge

In a Rome game (`play --civ rome_100ad --kit merchant --seed real25`), `workshop_first` showed one running
cost under `why`, a cost about five times larger in the `open` message, and a third figure in `ventures`
that later grew to match the `open` one as staff were hired. Opening it also took a charge, which the
`cashbook` shows as "opening a venture" but no text screen mentions.

Why the figures differ: for a capability institution, upkeep scales with occupancy (headcount over the
institution's places, with a floor; `sim/engine/economy_production.py` `institution_upkeep`). Only some
callers use that rule:

- `venture_real_upkeep(node_id)` with no units applies occupancy. `why` (`sim/ui/proto/techtree.py`),
  `ventures` and the ledger use it.
- `venture_real_upkeep(node_id, units)` returns the full `up * units * price_index` and skips occupancy
  (`sim/engine/projects_venture_quotes.py`). The `open` message (`sim/engine/projects_ventures.py`) and
  `quote open` (`quote_spending.py`) use it.

So `why` and `ventures` give the cost at today's staffing, while `open` gives the cost at full staffing.
None of them says which it is.

The opening charge (`opening_fee`, from `venture_capex` in `projects_ventures.py`) goes into the JSON reply
as `opening_charge` and `paid_now` (`sim/ui/proto/dispatch_ventures.py`), but no text renderer prints those
fields.

Why it matters: a player can't plan a budget when three screens disagree about one number, and a charge
they never see lands in their cash.

What it would take: one function that returns both "now" and "at full staffing" (both through
`institution_upkeep`), used by every screen, with labels on each. Print `opening_charge` in the `open`
message. Add a test that `why`, `open`, `quote open` and `ventures` agree on the same game state.

## Resolution

`venture_upkeep_quote` (through `institution_upkeep`) gives `now` and `at_full_staffing`; `why`, `quote open`,
`ventures` and the `open` message use it and label both. The `open` message states the opening charge.
Regression: `sim/tests/test_start_and_upkeep_quotes.py`.
