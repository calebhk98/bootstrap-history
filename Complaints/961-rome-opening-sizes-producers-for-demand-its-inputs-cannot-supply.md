# Rome's opening sizes producers for demand its inputs cannot supply, and a market with no seller shows no demand

**Status:** open - found tracing Rome's year-one fall on branch claude/labor-market-economy-stability-ueffy1; not fixed

**What is wrong.**

- The opening plans producers to `record.opening_demand`, demand "wanted, supplied or not" (`sim/economy/opening.py`
  `_final_demand`). On Rome about half of year zero's planned runs are not realised because an input is short in the
  producer's area (heat for bakers, millet for millers, lead for silver makers). The year then sells the opening's
  stock, and expected sales fall to what was realised; hiring follows down.
- `_final_demand` also counts households' bids for wealth stores (durables held as savings), a stock-building flow seeded
  from deposit history far below the households' target (`opening_stores.py`), so the producers of store goods
  (precious metals, platinum) are sized to a flow that does not last. Removing store bids altogether barely moved Rome's
  hired hours, so this is a sizing error rather than the cause of the fall.
- `expected_sales.demand_seen` adds unmet demand only in proportion to a producer's own sales, so a market where nobody
  sold shows its would-be sellers no demand; on Rome over a thousand producers sat in such markets in year one.

**Evidence.** Probes on a saved opened Rome economy (`ROME_SPIN_UP_YEARS=3,2`); no committed command prints realised
against planned runs. Measure Rome's trajectory with `python3 sim/simulator.py spin-up-trace --civ rome_100ad`.

**What it would take.** An opening that sizes each producer to what its inputs in reach can supply (the same rule the year
uses to plan within input reach); store demand sized at the replacement of what stores lose, not the gap to a target;
unmet demand in a market without sellers visible to entry and to producers that could serve it.

**A year-rule candidate, parked** (`Complaints/reports/961-plan-within-input-reach.patch.txt`): producers plan runs only as
far as their hard inputs reach (nothing on offer gives zero runs; a short fill last year caps the runs; a full fill caps
nothing). On saved Rome it raises realised over planned runs from year one but lowers hours hired and output a few per
cent, leaves unemployment unchanged, and plans fall faster than realised runs (the cap sometimes sits below what the
inputs deliver). Re-measure once inputs move between areas (lead to silver makers, heat to bakers).

**Inputs between areas (traced on saved Rome).** Lead for silver makers is mostly a real limit: the silver makers' bids
for lead stop at `producers.input_ceiling` (the price times one plus the run margin over variable cost), far below what
a producer that cannot run at all without the input would pay, and carriage from the few lead-smelting areas costs more
than that ceiling allows to all but a couple of the bidding areas. Heat (`thermal_mj`) is immobile by design, so a heat
shortfall is a local fuel problem. Parked: `Complaints/reports/961-merchants-learn-unfilled-demand.patch.txt` (merchants
learn the best unfilled bid and the quantity wanted in a market with bids and no seller); on saved Rome it sent
merchants' cash to other goods first and carried no lead, so it is not merged. Also seen: merchants bid to carry
`gaming_table_hour`, a service, which should not be carried.
