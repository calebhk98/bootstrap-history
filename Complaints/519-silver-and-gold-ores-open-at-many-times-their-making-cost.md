# Silver and gold ores open at many times their making cost

**Status:** partly - the common ores (iron, copper, tin, lead) pass in every civilisation; silver and gold ores, and the metals themselves, still open far above cost

**What is wrong now.** Silver metal trades at tens of times its making cost at an opening, and the ore follows it (Rome and
England silver ore; Han gold lode ore). Measure: `sited_traded_ore_ratios(civilisation)` in
`sim/tests/test_sited_ore_price_over_cost_validation.py` (agent price over making cost after one step, suite harness;
`python3 -m sim.tests --only sited_ore_price_over_cost_validation`). The all-ores test
(`test_every_civilisations_sited_ores_open_within_a_bounded_multiple_of_their_cost`) is an expected failure that turns
green when this is fixed; the common-ores test passes and guards the rest.

**Evidence on the cause** (details in `Complaints/reports/519-history.md`):

- Not the mint: cutting `MINT_YEARLY_STRIKE_SHARE` by orders of magnitude leaves Rome's silver price unchanged.
- Silver sits at the coin's mint parity at the opening; the ore sites take the margin.
- Unverified lead: the opening's price level in coin (wage, wheat) against the coin standard; the same drift as 473 and
  526. Check through `reprice_opening_money` and `coin_revaluation.py`.
- Cost side: the model's silver takes far fewer labour hours a kilogram than closed Complaint 349's sources attest;
  reconcile the silver recipe chain with 349.

**What it would take.** Settle the opening's price level (473, 526); reconcile silver and gold recipe labour with the sources
(349); then re-run the test and remove the expected-failure marker. A partner's export budget
(`_partner_spending`, `sim/engine/economy_port_year.py`) is sized by the cost table's price for the coin metal until the
metal's price is near its cost; move it to `GoodsMarket.home_unit_price` then.

**Tried and why it failed.**

- Stocking every producer with a year of inputs at the opening (branch `fix-regression-iron-chain`, `0410114b`) brought
  every sited ore under the bound but was reverted: it turned four checks red that depend on where the unsettled spin-up's
  cycle stands (473). Land it with a settled spin-up.
- Sizing a named district at the size-weighted mean was dropped: it lifts iron districts to a tonnage nobody worked in antiquity.
- Site room was a cause for the common ores (ore grade defaulting to pure metal; yearly room a flat share of endowment); both
  fixed (`resources_district.district_grade`, `mine_deposits.found_deposits`).
