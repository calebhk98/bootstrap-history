# Adding `hardcoded_historical_outcome`, and auditing every `declare()` call for more of it

**Type:** Registry design / §3.1 compliance
**Priority:** Informational. The mechanism is built; nothing new and confirmed
was found to put in it yet.

## What this does

Complaints/36 asked for a seventh kind so "no mechanism exists yet" and "a
historical outcome was copied in" stop sorting identically in the burndown.
This adds it - `hardcoded_historical_outcome` - and reclassifies the two
entries Complaints/36 named, both in `sim/engine/economy.py`:

- `DEBT_BASE_RATE` (0.12) - the Roman legal ceiling on ordinary loans
  (*centesimae usurae*), used as the baseline arrears rate and reused
  unchanged by every other civilisation.
- `LIVING_COST_TAX_RATE` (0.06) - *portoria*, the *vicesima* and local dues
  flattened into one share of revenue.

`python3 sim/constants.py --burndown` now reports this count separately and
loudly, states that it is expected to reach **zero** (unlike
`temporary_heuristic`, which never will), and names each entry. The existing
`stdout.split()[0]` contract (the total declared count, which
`sim/tests/test_constants_burndown.py`'s other tests already parse) is
unchanged - the new section is printed after it, not instead of it.

## The audit

Complaints/36 was explicit that finding the rest is "a review job, not a
regex." This read every `declare()` call in the repository as it stood
during this task, not just grepped for keywords, though keyword searches
(attested/historical/documented/edict/wage/price/tax/revenue/population/
census/etc.) were used to prioritise where to look closely.

**Coverage at the time of this audit**, since the registry is growing under
concurrent work (CLAUDE.md's own warning to expect this):

- `sim/engine/economy.py` - 240 declared, both known reclassifications
  applied (the file was not being edited by anyone else at the time).
- `sim/world/agriculture.py`, `transport.py`, `military_logistics.py`,
  `demography.py`, `deposits.py` - 138 declared between them, all read in
  full.
- `sim/engine/core.py`, `labour.py`, `society.py` - **mid-edit by other
  agents throughout this audit**, working-tree snapshot only (not yet in
  `sim/constants.py`'s `_import_declaring_modules()`, and not committed).
  74 `declare()` calls present in that snapshot, all read. `sim/engine/cli.py`
  and `sim/engine/proto/typed.py` were also touched during the audit window
  but carried no `declare()` calls in the diff at the time of reading.
- `sim/world/demand.py` - a new file that appeared mid-audit (untracked, not
  yet claimed by any commit), 10 `declare()` calls, all read. Added to
  `_import_declaring_modules()` in this same change - it is not itself
  `sim/world/`'s or my scope's edit, but the list it is added to lives in
  `sim/constants.py`, and leaving it out would have made
  `test_every_declaring_module_under_sim_world_is_in_the_list` fail and the
  burndown quietly undercount by 10, which is precisely the failure mode
  this whole mechanism exists to prevent.

None of the in-flight or settled files turned up a **new** confirmed
`hardcoded_historical_outcome` beyond the two above. This audit should be
repeated once `core.py`/`labour.py`/`society.py` land and are added to
`_import_declaring_modules()`, both because they were changing under me and
because a fresh pair of eyes on a stabilised file is worth more than one on
a moving target.

### Calibration-target leak check

All 12 `calibration_target` entries were checked for the failure mode this
task named as "the worst thing you could find" - one being read by
production code rather than only by a check:

`HISTORICAL_FARM_POPULATION_SHARE_{LOW,HIGH}` (agriculture.py),
`LAND_TO_SEA_FREIGHT_COST_RATIO_{LOW,HIGH}` and
`HISTORICAL_MAX_ECONOMIC_LAND_HAUL_KM_{LOW,HIGH}` (transport.py),
`CALIBRATION_LEGION_RATION_KG_GRAIN_PER_DAY_{LOW,HIGH}`,
`CALIBRATION_LEGION_MARCH_RATE_KM_PER_DAY_{LOW,HIGH}` and
`CALIBRATION_MAX_SUPPLY_RANGE_DAYS_{LOW,HIGH}` (military_logistics.py), plus
three more found in `sim/world/demand.py` once it appeared mid-audit:
`HOUSEHOLD_FOOD_BUDGET_SHARE_{LOW,HIGH}` and
`SILVER_TO_LEAD_PRICE_RATIO_HISTORICAL`.

Every one of them is read only from two places: the declaring module's own
`if __name__ == "__main__":` printout (a human-readable comparison line,
never called by any production function), and its own test file's assertions
against the module's *computed* figure (`sim/tests/test_demand.py` did not
exist yet at the time `demand.py`'s three were checked, so for those the
check is only "not read anywhere outside `__main__`" - re-verify once that
test file lands). **Clean.** None is read by a function any other code path
calls.

`sim/world/demand.py`'s other seven declarations (a Gini coefficient, three
household discretionary-spending shares, two calorie/energy conversions
already declared elsewhere for standalone-module reasons, and two
`initial_condition` demo-scale figures for its own `__main__` block) were
also read in full. All self-flag as unsourced/tuned or as demo-only figures
no production function reads; none is a `hardcoded_historical_outcome`
candidate. Worth calling out: `BETA_SILVER_SURPLUS_SHARE`'s own `why` text
records that it was "picked ONCE... and never adjusted after computing what
silver:lead ratio it produces" specifically to avoid the trap CLAUDE.md 3.4
warns about (tuning a heuristic until it matches a calibration target) - the
kind of self-discipline this audit was looking for evidence of elsewhere.

### Borderline cases looked at and NOT reclassified

Flagged here rather than fixed, per the task's instruction, and rather than
folded into the main list above because none of them cleared the bar for
`hardcoded_historical_outcome` - each is recorded so a reviewer can overrule
this call:

1. **`MINE_CAPEX_PER_T_YR_COAL` and its five siblings** (`economy.py`,
   `engineering_estimate`). The class comment above them derives capex from
   "a Roman coal hewer working a shallow drift wins on the order of a tonne
   a day... at a miner's wage of 0.09 denarii/hour over 2000 hours/year."
   The wage figure is an assumed, unsourced number embedded in a comment
   (not itself `declare()`d, not read anywhere else), used as one ingredient
   in a genuine physical build-up (throughput × wage × a haulage/timbering
   multiplier) rather than asserted directly as the capex figure itself.
   This is different in kind from `DEBT_BASE_RATE`, which had no derivation
   at all - but a wage is exactly the kind of thing this task flagged as
   suspect, and wages are still exogenous everywhere in this engine until
   the price solver lands. Left as `engineering_estimate`; flagged because
   I was genuinely unsure rather than confident it clears.

2. **`STATE_CAPACITY_DEFAULT_FALLBACK`** (`economy.py`, currently
   `initial_condition`, value 0.5). This is a generic fallback for a
   civilisation file that omits `state_capacity`, not itself a claim about
   any specific society's starting state - the `why` text says as much
   ("not a claim about any specific society"). It reads more like
   `temporary_heuristic` (a defensible default standing in for missing data)
   than `initial_condition` (a fact about the world at 100 AD). Not a §3.1
   concern either way - flagging only as a probable mis-tagging for whoever
   next touches `economy.py`.

3. **`LITERACY_REFERENCE_GENERAL` / `LITERACY_REFERENCE_ELITE`**
   (`sim/engine/labour.py`, in-flight, `initial_condition`, 0.12 / 0.90,
   sourced to `rome_100ad.json`). Worth recording because it has the same
   *shape* as the `DEBT_BASE_RATE` mistake one step earlier: Rome's own
   starting condition is "copied here as the denominator every OTHER
   civilisation's literate-trade capacity is measured against." The
   difference that clears it, on reading `literacy_factor()`: each
   civilisation's OWN `literacy_general`/`literacy_elite` is read from that
   civilisation's own data file every time, and Rome's figure is used only
   as the normalising denominator (1.0 = Rome's level) - Han's 0.95 elite
   literacy is Han's own attested number, not Rome's reused. That is a
   calibration-anchor choice ("everything else in this economy is already
   calibrated relative to Rome"), not a value asserted for every
   civilisation regardless of its own data, which is what made
   `DEBT_BASE_RATE` a violation. Recorded rather than silently cleared,
   because `labour.py` was still being written while I read it and the
   mechanism should be re-checked once it settles.

4. **`share_of_empire_output`-derived declarations** (`deposits.py`,
   `temporary_heuristic`, one per gold/mercury deposit). These stand in for
   `geography.json`'s regional mineral-share breakdown for the two metals it
   has no entry for, and are explicitly a share of `empire_output_100ad` -
   an initial-condition-flavoured geographic fact (ore distribution at
   scenario start), arguably mistagged as `temporary_heuristic` rather than
   `initial_condition`. Not a §3.1 concern; noted for the eventual tag
   sweep, not urgent.

### One thing this audit did NOT have

`declare()` calls not yet written. Six agents are adding them to
`sim/engine/{society,core,labour,projects,cli}.py` and `sim/engine/proto/`
concurrently with this task; `projects.py` and `sim/engine/proto/` carried
no `declare()` calls at the time this was written, and whatever lands in the
files that were mid-edit was read once, as a snapshot, and could still change
before it settles. This complaint is a photograph of one moment, not a
standing guarantee - re-run the audit once the registry stops moving.

---

## PM adjudication, and a variant the audit nearly walked past

The audit flagged `MINE_CAPEX_PER_T_YR_*` as borderline because an unsourced
miner's wage (0.09 den/hr) sits inside the derivation. That is the lesser
problem. Reading the `source` text of those same constants turns up
something sharper, stated openly in the code:

    MINE_CAPEX_PER_T_YR_IRON
      "...cross-checked against iron's own BOOK PRICE (the
       GENERIC_MINE_CAPEX_MULTIPLE comment below notes iron's capex is close
       to 60x its book price, the same multiple the generic fallback for
       every other material now uses)."

    GENERIC_MINE_CAPEX_MULTIPLE = 50.0
      unit:   "denarii capex per denarius/kg of BOOK PRICE"
      source: "Fitted from the seven curated MINE_CAPEX_PER_T_YR figures
               against their own book prices: iron ~60x, copper ~60x, tin
               ~42x, silver ~28x, gold ~46x... 50, the middle of that band,
               is used for any material without a curated figure."

**The capital cost of a mine is computed as a multiple of what the metal
sells for.** Not for one metal - as the general rule for every material
without a hand-written figure.

### Why this is worse than DEBT_BASE_RATE, not merely equal to it

`DEBT_BASE_RATE` copies a historical fact, the Roman legal interest ceiling.
It is at least a real observation about the world.

This copies `data/prices.json`, which CLAUDE.md §4 records as **91.8% the
author's own estimates**, and which `data/production/` exists specifically
to replace. So an author's guess is laundered into an `engineering_estimate`
with a fitted multiple and five decimal places of apparent method.

And it is circular. Capex feeds cost; cost is what should determine price;
the capex was read off the price. CLAUDE.md §4 states the rule for the
production data in as many words - a yield "is NEVER derived from what the
material sells for, nor tuned so a computed price matches `prices.json`" -
and the same rule plainly governs the engine. It was written for
`data/production/` because that is where somebody was about to break it;
nothing in it is specific to that directory.

### Reclassified

Seven constants whose own `source` cites a book price are now
`hardcoded_historical_outcome` rather than `engineering_estimate`:
`GENERIC_MINE_CAPEX_MULTIPLE`, `GENERIC_OUTPUT_PRICE_EXPONENT`,
`MINING_COST_SCALE_CEILING`, and the four `MINE_CAPEX_PER_T_YR_*` entries
that say so outright.

The kind's meaning is "a number that IS the answer to something this
simulation should compute, asserted instead of derived". A book price
qualifies. That the number came from this project's own data file rather
than from a history book makes it easier to miss, not more legitimate.

### What would fix it

`sim/world/deposits.py` already derives extraction cost per deposit from ore
grade, depth and hardness, and `data/production/`'s `capital` field already
carries build materials and build labour in physical quantities. A mine's
capex is a building with a bill of materials, which is exactly the shape
both of those speak. The pieces exist; nothing has been joined up.

### On the miner's wage, the thing actually flagged

Keep it, for now, and keep it visible. A wage is what §3.1 says must fall
out of the model, so 0.09 den/hr cannot stay indefinitely - but it is an
input to a derivation rather than the wage the simulation charges anybody,
and the wage half of Milestone 5 is the piece that will replace it. It is
`temporary_heuristic`-shaped, not `hardcoded_historical_outcome`-shaped.
Revisit when the wage exists.

### Not changed, and why

`STATE_CAPACITY_DEFAULT_FALLBACK` is tagged `initial_condition` and is
really a missing-data fallback - mistagged as the wrong LEGITIMATE kind, not
a §3.1 issue. `share_of_empire_output` in `deposits.py` is arguably
`initial_condition` rather than `temporary_heuristic`. Both are bookkeeping;
neither is a hardcoded outcome. Left alone to keep this complaint about one
thing.
