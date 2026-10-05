# Multiple parallel models exist for related concepts; define which is authoritative

**Status:** open

**Source:** playtest findings document, ARCH-001. **Type:** Architecture
recommendation, largely already answered by an existing document; this
complaint's job is to say so precisely, per CLAUDE.md's own request, rather
than duplicate the answer.

## The player's reasoning

The repository contains rich standalone modules (`sim/world/demand.py`,
`sim/labour/labour_market.py`, `sim/world/deposits.py`) while the live engine
has separate labour, demand/revenue and mining paths of its own. Standalone
modules are useful for development, but duplicate concepts drift. Their
recommendation: for each domain, document the authoritative live model, the
experimental/reference model, the intended migration path and the
invariants shared between them; then either wire the standalone model in,
deliberately keep it as a research module, or retire it.

## What already exists, checked directly

This exact question is already answered, per-module, in `docs/architecture/
STATE_OF_THE_PROJECT.md` (its milestone table and "What is not built or not linked"
section, as first written), and the answer is current as of the same day this review was
done:

    agriculture.py         imported by sim/engine/core.py
    demography.py          imported by sim/engine/core.py
    land.py                 imported by sim/engine/core.py
    transport.py            imported by sim/engine/economy.py (as freight_physics)
    military_logistics.py   imported by sim/engine/society.py
    deposits.py             imported ONLY by sim/engine/solve_prices.py (a standalone tool);
                             reaches the engine only when use_solved_prices=True,
                             which is False everywhere by default
    demand.py               imported by NOTHING under sim/engine/ or sim/engine/solve_prices.py
    labour_market.py        imported by NOTHING under sim/engine/

So: five of the eight `sim/world/` domain modules are already authoritative
and wired directly into the engine (agriculture, demography, land, transport,
military_logistics). One (`deposits.py`) is reachable through a tool the
engine can call but does not by default - the live engine still prices ore
through its own `sim/engine/economy_mining.py` path, and `deposits.py`'s
Ricardian-rent mechanism only takes over when `use_solved_prices` is flipped
on, which it is not. Two (`demand.py`, `labour_market.py`) are wired into
nothing at all - the live engine has its own separate revenue path
(`sim/engine/economy_production.py`) and its own separate labour-pricing
path (`sim/labour/labour.py`, the static `TRADE_DENSITY` classification the
`labour_market.py` docstring itself names as what it is meant to replace),
and neither reads the standalone module.

`docs/architecture/STATE_OF_THE_PROJECT.md` ("What to do next") also already states the
intended migration path for the two fully-unwired modules, in priority
order: wire `labour_market.py` into the engine first (named the single
most-referenced missing piece across the open complaints), then wire
`demand.py` into `sim/engine/solve_prices.py` in place of the current mass-split
joint-byproduct allocation. Neither module is a dead research artifact
awaiting a retire decision; both are complete, tested, and simply not called
from production code yet, per that same document's own framing ("a wiring
job, not a design job").

## How this sits against CLAUDE.md

§4 states plainly that "nothing reads this data yet" for `data/production/`
is a different, earlier-stage problem than what is described here; the
`sim/world/` situation is one level further along; the mechanism exists in
working, tested code, only the wiring is missing. That distinction (data
exists vs. code exists vs. code is called) is worth being precise about
whenever this area comes up again, because conflating "unwired" with
"unbuilt" is exactly the mistake this finding's own framing risks if read
too quickly.

## Size

The documentation this finding asks for already exists; the remaining work
is the wiring itself, which is `Complaints/102`'s scope, not a new
documentation task. This complaint's only remaining contribution is noting,
for the record, that `deposits.py`'s status ("reachable through a tool the
engine can call but does not by default") is subtly different from
`demand.py` and `labour_market.py`'s status ("wired into nothing"), a
distinction the player's original finding does not draw but which matters
for prioritising the wiring work.

## Cross-references

`docs/architecture/STATE_OF_THE_PROJECT.md` (milestones, not-built and next-steps sections) answer this finding
directly; read that document rather than re-deriving the answer.
`Complaints/102` (ECON-004) is where the actual wiring work is tracked.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 405 (`closed/405-trader-actors-overlap-the-other-trade-models.md`): three merchant models (engine foreign_traders, economy merchants, trader actors) trade the same gap; trader sales never move the partner's market.
- 403 (`closed/403-strata-income-has-no-source-agreeing-with-the-economy.md`): strata income has no source agreeing with the economy; strata are another household-budget model.

## Merchants (405): decision, one owner per flow

Measured on a Rome start with the agent economy on (a short run, printing per year the tonnes each path carried;
there is no command for it, the checks in `sim/tests/test_foreign_actor_trade.py` are the repeatable part):

- The engine's aggregate `foreign_traders` flow is dormant in an agent-economy game: `_step_market` returns after the
  agent year, so `foreign_trade_year_end` never books a flow. It runs only when the agent economy is off.
- The economy's `_external_orders` and the trader actors both carried the same goods across the same gap. Felt was
  imported by both in the same years; stone blocks were imported by the stand-in orders while the traders exported
  them. The traders carried the same cargo every year, since a sale abroad never moved the partner's price.

Decision: inter-country trade is owned by the trader actors (any actor can be one, so any country can play it).
The stand-ins give way where an actor is already carrying:

- A cargo sold to or bought from a partner is tallied (`sim/engine/foreign_actor_trade.py`) and the partner's market
  book closes on it at the year's end, so the partner's price, capacity and stock follow the cargo (405 item 1).
  `Sim.partner_price_per_unit` is the one price of a partner's good (solved cost, coin price level, the book's ratio),
  read by the trader view and by the external orders. A partner's depth for a trader is capped at its book's demand,
  the scale that price moves on.
- `_external_orders` offers no import of a good actors carried home this year and bids for no export of one they carried
  out. The engine's aggregate flow skips a commodity actors carry with a partner. Both stay as the owner of the goods
  no actor carries (intermediates, ores, goods before a trader is founded) until the traders are general enough
  to take them.

Left to do, in order:

1. Done: a trader sizes a cargo against the price it makes (`paying_tonnes` in `sim/agents/trader_routes.py`): carry
   as far as the destination's price after the cargo lands, less carriage, risk and interest, still beats the source's
   price after it is taken. The partner book answers (`price_after_cargo`, `partner_price_response`); the cargo no longer
   flips year to year, and the partner's price settles at the break-even freight, risk and interest set
   (`test_foreign_actor_trade.py`). Still open: the home society's market does not answer `price_after_cargo` (the
   economy has no quote of the price after a sale), so cargo bound for home is still limited by `TRADER_DEPTH_SHARE`
   and a home price that rises or falls with trader cargo is not seen by the trader. Also a cargo is sized against
   its own route only: two routes into one market within a year each see the tally of the cargo already shipped,
   not of the cargo planned by the other.
2. A trader's money is booked through "edge:market sale" and "edge:market purchase", not through the foreign coin
   ledger, so a trader's exports do not draw coin from the partner or raise the home coin stock (price-specie flow
   exists only for the external edge). The cargo does not use the carrier lift either (`_record_lift`).
3. Trader purchases and sales at home enter the agent economy over the legacy edge, not as external orders; the
   economy cannot yet tell them from domestic trade. Moving them to the external edge needs the partner per order
   (the same gap as the even split in `_settle_foreign_coin`).
4. The economy's merchants (`sim/economy/merchants.py`) were not touched: they move goods between tiles only, with no
   partner. The aggregate flow can go once the agent economy is the only economy, with the external orders; until
   then it is the opt-out game's merchant.
5. No domestic routes for trader actors (an economy-port member exposing area prices).

## Remaining after the shared-helper pass: state revenue bases

`sim/agents/revenue_bases.py` and `sim/economy/taxes_bases.py` share base names (`harvest`, `adult_labour_years`,
`imports_value`, `exports_value`, `coin_stock`) and a `Base` dataclass, but they are not one implementation twice:

- The agents bases take the engine's `SimWorld` and read aggregates (`harvest_tonnes`, `national_people`, `trade_value`,
  `coin_stock_value`), so each yields one body-wide figure. The economy bases take `YearFacts` and measure per payer
  from the economy's own ledger records, skipping edge accounts. The inputs have no common shape, so no single
  function can serve both without first deciding which side is authoritative.
- The two `Base` records differ (payers and material against quantity, good and tile), and each package may import
  the other only through its `api`; a shared base would have to live in a top-level module both packages import.
- Only the vocabulary is common: the basis names (and the harvest material). Sharing a table of names would not
  remove drift, because the measurement is what differs. The real fix is the one recorded above: the agents
  `Government` reads the economy's assessed total through an economy-port member and its aggregate bases go.
- Also still open, noted while auditing: `labour/trade_data.fallback_trade` is a thin adapter over
  `labour/market/trades.fallback_trade` (different signature), `deep_merge` in `engine/mods_base.py` and
  `geography/map_source.py` differ on purpose (control keys and nested-only deletion against delete-on-null), and
  `economy/labour.training_premium` and `reservation_wage` against the labour package's are different maths (item 2
  of the audit), not copies.

## Unified: price level, credit room, small constants

- **Price level.** The word named three different things. Each now says which: `Sim.home_price_level()` (engine,
  `foreign_payments.py`) is the one level the engine reads for wages, caches and clearing, from the coin stock against the
  opening stock (`balance_of_payments.money_stock_price_level`); `basket_price_level` is the agent economy's fixed-basket
  index of its own cleared prices, read only by its households' and state's expectations; `partner_price_level` is a
  trading partner's. The unused `EconomyPort.price_level` is gone. The engine does not read the basket index, on purpose:
  measured over a dozen default-game years (Rome) the basket index is noisy and sits well below one after the rebase,
  where the coin-stock level moves smoothly, so wiring wages to it would move them by a different order than the
  disagreement being fixed. Whether wages should follow the basket index is a design change, not a dedupe (Complaints
  273, 140).
- **Credit.** `market_rate()` and `market_credit_room()` both ask the agent economy's credit market when it is on
  (`economy.api.credit_room`: what lenders put out of the savings on offer at the last lending, less what other borrowers
  took). The engine's loanable-funds record answers only when the agent economy is off. Founder credit with the agent economy on
  now follows the agent market's room (it used to read a record the agent economy never updates); the quick fingerprint
  scenarios are byte-identical before and after, so the founder's ceiling is not bound by it there.
- **Constants.** `tile_costs.py` no longer holds its own distance or carrier-size copies (geography owns them). The
  bare 365-day year in `foreign_traders.py`, `food_pasture.py` and `layers_ocean.py` is `unit_conversions.CIVIL_DAYS_PER_YEAR`;
  the 365.25 averages declared in `sim/world/` and `climate_temperatures.py` stay separate (standalone models).

## Strata (403): decision, the cohorts own household income

With the agent economy on, a home stratum's income is read from the economy's household cohorts, not from members times
work share times pay. The cohorts of the whole home country form an income curve over the people (poorest per head
first, `economy.cohort_incomes`); the home strata are ranked by what their own trade or property would earn per head
and laid end to end along the curve, each taking the income of the cohorts its members occupy
(`sim/agents/strata_observed.py`, fed through `observed_stratum` in `sim/engine/agents_port_cast.py`). No stratum is
named; the rule reads only a plan's trade and property share. The bonded earn nothing themselves and their slice is the
product credited to the keeper (the hours their cohort supplied, paid by employers). Another country's strata and any game
with the agent economy off keep the wage bridge. Membership still follows the population model.
Measured on a Rome start (agent economy on), the bridge against the mapped cohort income per stratum is printed by
`python3 -m sim.tests --jobs 1 --only strata_income_from_cohorts`: the bridge overstates by a few times for wage strata
and by orders of magnitude for the propertied; the test also checks the mapped incomes add up to the cohorts' and that
strata money moves only by what crossed the edge and the state's relief.

## Still two owners

- Labour (428): the labour package's market and the agent economy's labour market each clear wages.
- Merchants (405): one owner per flow now for goods actors carry (decision above); the stand-ins still own the rest.
- Demand baskets: `sim/world/demand.py`, the economy's household baskets and the agents' strata baskets.
- The engine's `market_loans`, `update_capital_market` and its rate still run (and set the rate) when the agent economy is off;
  only the reading side is unified.
