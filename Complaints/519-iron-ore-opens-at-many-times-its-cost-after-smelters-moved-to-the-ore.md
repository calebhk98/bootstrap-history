# Sited ores open at many times their making cost

**Status:** narrowed to precious ores (silver, gold); the common ores pass

After merge 968974d4 (Complaint 473: weight-losing processors sit at their fixed-site inputs), a Rome opening's
iron ore trades far above its long-run cost (`economy.agent_prices()["iron_ore_kg"]` against
`market_price_ratio("iron_ore_kg")` after the opening; it was a small multiple before). Iron bar fell at the same
time. A blast furnace, which needs thousands of tonnes of ore to build, now costs more to open than a default
founder holds. Found fixing `closure_reasons` (the fixture now picks the cheapest concern to open).

Iron ore is common, so a scarcity price of that size is not plausible. The siting change keeps capacity that the
local ore supply cannot feed ("the shortage shows as the input's price") and concentrates smelters on a few ore
tiles whose site limits are small, so their bids for ore run far above its cost of raising.

What it would take: check the iron ore site limits against the deposits' data (they may be far too small, like the
ore mass balance fixed in 511), and size a processor's capacity at the opening to the input supply its tiles can
reach rather than keeping the excess as a price. Test: a common ore's opening price stays within a bounded multiple
of its making cost in every civilisation (a relationship, CLAUDE.md 4.2). Overlaps 507 Stage 2 (the opening);
check after it merges.

Checked in 520: sizing the unsized districts (and drawing deposits down by their rate) leaves Rome's iron sites
as they were (all six already sized); Rome's iron ore price over its making cost falls somewhat but stays far above
1, so it is not a deposit-size problem on the Roman rows. For the other civilisations the new sites move some ore
ratios up and some down (measure with `economy.agent_prices()` against `_material_prices()` after a first step).

## Widened (2026-10-15)

The pattern is general: in 520, Han's copper, tin, lead and gold ores sat near their making cost while they had no
site and rose to several times to tens of times it once their districts named sites; Mexica copper and gold rose
the same way. So a site's yearly room (a share of the deposit's endowment per year) may be far tighter than what a
district can actually raise, and the scarcity shows as price. Check the site-room rule (`resources_working_share_per_year`,
how a site's room per year is derived from its endowment) against the historical output rates the deposit data
gives (`sim/engine/deposit_history.py`), for every civilisation, before changing the opening.

## Measured (fix-519-sited-ore-prices)

Measure: `economy.agent_prices()` over `_material_prices()` after one step, per ore
(`sim.tests.test_sited_ore_price_over_cost.sited_traded_ore_ratios`; the table is the same for a full-length
opening, the suite's harness shortens the spin-up and moves which ores spike).

- Room was a cause, in two ways, both fixed. (1) A deposit with no stated ore grade (every unsized district: Han,
  Mexica, Norse, Timna, Rammelsberg) counted its ore as pure metal, one tonne of ore per tonne of metal, so a
  copper site allowed a hundredth of the ore its metal needs (the 511 mass-balance error again). It now takes the
  type's expected grade (`resources_district.district_grade`). (2) A deposit's yearly room was a flat share of its
  endowment even where the data give the rate it was worked at (the rate `mined_before` already draws it down
  by); the larger of the two now stands (`mine_deposits.found_deposits`).
- Not the cause now: Rome's iron sites hold several times the ore its smelters ran, yet the ore stays dear. The
  producers sit on large unsold opening stocks and the price falls only by the unsold markdown a year, so a price
  that overshot in the opening's spin-up (the opening prices ore far above its cost, then the sited supply was
  short for some years) decays slowly. Room cannot fix that; it is the opening's remembered prices and stocks
  (507 Stage 2, `economy_port_*`, `opening_stores`) and the seller markdown (`sim/economy/producers.py`).
- Smelting capacity at the opening is several times the sited ore room for Rome's iron (check with the balance of
  the sites' room against the smelters' capacity in ore), which is the other half of 507 Stage 2.
- Sizing a named district at the size-weighted mean (a worked deposit is a draw weighted by its size) was tried and
  dropped: it lifts iron districts to the banded-formation tonnage nobody worked in antiquity.

What it would take now: the opening's ore stocks and prices agree with the sited supply (507 Stage 2), and
sellers' markdown reaches the cost within a few years. The test marked expected-failure turns green then.

## Update (stage 2 of 507)

The opening now holds processors to the supply of a good only deposits make (`opening_runs.fit_to_supply`) and sizes producers
from one final demand. Measured on full-length openings (`real` measurement: build the game as `play` does, read the
economy's price over the opening cost of each sited good): every civilisation's sited ores are within an order of magnitude of
cost after the spin-up. The suite's short spin-up (523) still shows a few above the bound (the English and Norse ores),
so `test_sited_ore_price_over_cost` keeps its marker.

Also red because of it: `economy_tin_dearer_than_copper` (Complaint 511). The bisect over this round's merges puts the
break at the 473 merge that sited weight-losing processors beside their supply (the 511 merge added the check and failed
on the combined main from its first commit). In the opening year copper ore shows far above its embodied labour while tin's
gravel does not, so tin shows at a small fraction of copper's price against a labour ratio several times larger
(`python3 -m sim.tests --slow --only economy_tin_dearer_than_copper` prints both). The check says not to weaken it;
it turns green with the opening-price work above.

## Note (2026-10-15, 507 Stage 3)

Until this is fixed, a partner's export budget (`_partner_spending` in `sim/engine/economy_port_year.py`) is sized
by the cost table's price for the coin metal, not the economy's: at the economy's price the metal's opening premium
swamped the port market and left it with no bids. Every other coin-metal use reads the economy's price
(`GoodsMarket.home_unit_price`). Move this one onto it when the metal's price is near its cost.


## Re-measured (fix-519-sited-ores, on economy-accounting-and-speed)

Measure: `sited_traded_ore_ratios(civilisation)` in `sim/tests/test_sited_ore_price_over_cost.py` (agent price over
making cost after one step, suite harness; `python3 -m sim.tests --only sited_ore_price_over_cost`).

- Rome: iron ore 3.0, copper ore 1.1, cassiterite 1.0, galena 4.6, gold gravel 0.4, silver ore 28.8.
- Han: cassiterite 2.4, gold lode ore 12.0. Mexica: no traded sited ore at the first step.
- Norse: iron ore 3.0, copper ore 2.5. England: iron ore 7.6, copper ore 2.6, galena 10.2, silver ore 50.2.

The common ores (iron, copper, tin, lead) are within a small multiple, so the complaint's iron-ore case is gone
(producers limited by cash, entry from unfilled bids and cost-priced aggregate producers fixed it). Test
`test_every_civilisations_common_ores_open_within_a_bounded_multiple_of_their_cost` now passes (bound 15, the
order of magnitude with headroom for England's galena at just over 10).

Still open: silver ore (Rome, England) and Han's gold lode ore. Silver metal itself trades at tens of times its
making cost (England 666 against 28, Rome 370 against 21 per kg), and the ore follows it, so this is the precious
metals' price rather than site room. The all-ores test keeps its expected-failure marker for them.

## Traced (no change made)

Suite harness, one step, agent price over making cost: silver metal about twenty times cost in Rome and England and
about thirty in Han; silver ore follows the metal in Rome and England. Han's gold lode ore is near two times, not the
twelve above.

- **Not the mint.** Cutting `MINT_YEARLY_STRIKE_SHARE` by orders of magnitude leaves Rome's silver price unchanged and
  England's far above cost.
- **Silver sits at the coin's mint parity**, already at the opening; the ore sites take the margin (smelter capacity
  is about twice the ore sites').
- **Unverified lead: the price level.** In coin, Rome's opening wage and wheat price look several times below the
  level the coin standard implies (from a remembered wheat price, not from data in the repo). If so, silver is not
  dear; everything else is cheap, and this is the same drift as 473 and 526. Check: wage and wheat in coin at the
  opening and after the spin-up against the coin standard, through `reprice_opening_money` and
  `coin_revaluation.py`.
- **Cost side.** The model's silver takes a few hundred labour-hours a kilogram against the thousands attested in
  closed Complaint 349's sources; that explains part of the ratio. Reconcile the silver recipe chain with 349.
