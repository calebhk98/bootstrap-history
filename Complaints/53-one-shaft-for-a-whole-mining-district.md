# Laurion opens for the price of one shaft

An attempt to derive `MINE_CAPEX_PER_T_YR_*` from `sim/world/deposits.py`'s
sinking-cost model - six of the eleven §3.1 hardcoded outcomes - produced
numbers two to three orders of magnitude below the ones it replaced, and was
REJECTED rather than committed. The derivation was structurally right and
missing one term. This records which term, so the next attempt does not
rediscover it.

## The mismatch

    capex per (tonne/year) = sinking_cost_labour_hours(deposit)
                             / deposit.quantity_tonnes_per_year
                             * miner_wage

`sinking_cost_labour_hours` comes from `depth_class` alone, and
`SHAFT_SINKING_HOURS_DEEP_VEIN` is 20,000 labourer-hours documented as the
cost "to sink **a** deep shaft and install **its** drainage-wheel battery
and long ore-hoist" - ONE working.

`quantity_tonnes_per_year` is `share * empire_total_tonnes`
(`deposits.py:964`) - the whole district's attested annual output.

So the formula charges Laurion the cost of one shaft. Laurion was a field of
shafts; the archaeology counts them in the thousands.

## How far off, measured rather than argued

Laurion is 60 t/yr of silver at 70 labour-hours/kg extracted, so its annual
extraction labour is 4.2 million hours - about 2,100 full-time workers. The
derivation gives it a capital cost of 20,000 hours, or ten worker-years.

    silver mine, 60 t/yr      capex        one year's opex   capex/opex
    constants being replaced  540,000 den       132,000 den    4.1 years
    the derivation             1,800 den       378,000 den        0.5%

Nobody opens a silver mine for half a percent of one year's wage bill. Dacia
is worse: 13,800 workers' worth of annual labour against a capex of ten
worker-years, 0.07%.

The agent that produced this diagnosed the cause correctly - it wrote that
the constant "was sized to represent ONE modest working's fixed capital cost,
while the deposit it gets divided by carries a WHOLE ancient mining
district's attested annual output" - and then concluded that capital looking
nearly free "is also a genuine historical claim." It is not. Ancient mining
was labour-intensive, which is true and well attested, but not to the tune of
capital being 0.07% of annual labour. A correct diagnosis followed by a
rationalisation is the specific failure worth recording here.

## What is missing, precisely

One term: **output per working**, or equivalently the number of workings a
district supports. With it the derivation is correct as written:

    capex per (t/yr) = sinking_cost_labour_hours(deposit)
                       / output_tonnes_per_year_per_working(deposit)
                       * miner_wage

and the district's total capex falls out as that times its number of
workings, instead of being independent of its size. A shaft serves a face of
a certain area at a certain rate; that is a physical quantity of the same
kind as the ore grades already in the file, not another tuning knob.

`deposits.py` also mixes the two scales internally, which is the same bug one
level down and should be fixed in the same pass:
`SHAFT_SINKING_HOURS_DEEP_VEIN` is 20,000 hours for one shaft, while
`AQUEDUCT_CONSTRUCTION_HOURS_ALLUVIAL_HYDRAULIC` is 500,000 hours for Las
Medulas's whole aqueduct programme - a district-scale figure sitting in the
same lookup table, keyed by `depth_class`, and consumed by the same function.

## Two findings from the attempt that ARE worth keeping

**`GENERIC_MINE_CAPEX_MULTIPLE`'s justification was circular, and the
circularity is now measured.** It derives a mine's capital cost from what the
metal SELLS FOR, which CLAUDE.md §4 forbids outright, and its defence was
that capex/price sits in a stable 30-60x band across the seven curated
metals. Rebuilt against honestly derived figures, that band is not there -
the ratios scatter across four orders of magnitude. The "band" was an
artefact of the old circular derivation observing itself. Whatever replaces
this constant, it is not a refit of 50.

**A latent crash.** `open_mine()`'s partial-affordability branch computes
`capital / (capex * price_index * scale)`. Every curated capex is currently
positive so it cannot divide by zero today, but the derivation produced a
capex of exactly 0.0 for tin - alluvial tin needs no shaft, which is
physically right - and a founder in debt then hits `0 > negative_capital`
and divides by zero. `mine_quote()` already guards this with an epsilon;
`open_mine()` does not. Worth fixing on its own account, before any capex
ever legitimately reaches zero.

The rejected work is not in the repository. It was preserved outside it, and
this file is the part worth keeping.
