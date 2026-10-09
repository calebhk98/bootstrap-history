# Gold is worth no more than silver per kilogram to households, and nobody holds it as wealth

**Status:** closed - the store splits by expected carrying return including the service a held good gives; opening stocks come from deposit output; states hold a reserve in the same stores by the same rule; every gold and silver deposit states its working or that it is unknown; equal ornament effectiveness per kilogram is argued physically right and the ratio is carried by the store demand; the whole-game re-measure is a slow topic (`whole_game_gold_silver_ratio`) for the orchestrator to run.

Measured on the agent economy (scratch driver replaying the deleted `sim/economy_validate.py`,
30 years, seeds 1-3; no command prints it yet, Complaint 445): the median gold-to-silver price ratio
is about 6 in England, far below one in Rome, and in the thousands to tens of thousands in Han,
Mexica and Norse, where gold barely trades; the attested ratio is around 10-15 (see
`Complaints/reports/economy-research-extraction-and-money-metals.md`, weak sources). Gold's price
swings by more than its own value year to year.

Why:
- the only household use of gold is the `ornament` need, whose effectiveness is "equal across the
  bright metals" per kg. Buyers then take gold only when it costs no more per kg than silver: gold
  either sells at or below silver's price (Rome, where the hydraulic route is cheap) or not at all;
- there is no demand to hold precious metal as wealth (plate, hoards, temple treasure). Households save
  only in coin and loans (`households_orders.savings_target`), so a metal's price is set by a year's
  flow against a thin ornament demand, not by willingness to hold the stock, which was dozens of years
  of output;
- goods are not durable in the economy at all (Complaint 443), so an ornament bought is used up.

What it would take:
- data: an ornament effectiveness that is not equal per kg, or better, none needed: a store-of-value
  demand in which prestige follows scarcity, so the ratio emerges;
- economy: households keep part of their savings in durable, non-spoiling goods of high value per kg,
  chosen by those physical properties and the price, not by id; selling from that stock when its price
  is high is what makes the stock, not the flow, set the price.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 325 (`closed/325-gold-prices-below-silver-so-ornament-demand-buys-gold.md`): gold priced below silver so ornament demand buys gold; satiation done, supply-limited gold price and held-stock ornament remain.
- 334 (`closed/334-gold-has-one-hand-sluicing-route-and-no-deposit-model.md`): gold has hydraulic and lode routes; only the ornament limit and hand placers remain.
- 387 (`closed/387-metal-prices-swing-more-than-grain-in-rome-and-norse.md`): metal prices swing more than grain; partly fixed, gold remains and needs a validation command (445).

Research second pass (2026-10-09): `Complaints/reports/gold-silver-value-second-pass.md` (read alongside the first report, `gold-silver-value-research.md`). Finding: households already hold durable high-value goods as wealth (`sim/economy/households_store.py`), so "nobody holds it as wealth" may be stale; re-measure first. What remains is that the store splits its budget between metals by carrying cost alone, which comes out near even, and opening metal stocks start empty. Recommended: split by expected carrying return, seed opening stocks from past deposit output less loss, and let regional ratios differ through carriage cost per unit of value.

## Progress (2026-10-09)

Code, all on pure functions and small fixtures (no game built):

- `sim/economy/store_return.py`: a good's carrying return is its expected price change (toward the slow average of its price, `MarketMemory.usual_prices`, read through `YearView.usual_price`) less spoilage, wear and storage; `households_store.store_candidates` splits the store by that return. Every coefficient is a declared temporary heuristic. The old inverse-carrying-cost split made the price ratio of two metals equal the stock ratio, which is the hidden outcome the second report named; now the ratio rises with the stock gap by less than the gap.
- `sim/geography/resources_mined.py` (`mined_before`, in the geography contract): output of a country's deposits before a year, each deposit worked at a stated share of its endowment a year from `first_worked` until worked out. A deposit with no working date or size is listed as unworked, never guessed; a country with no deposit of a metal says so.
- `sim/engine/economy_port_stores.py` and `sim/economy/opening_stores.py`: the port passes workings to the setup; the economy keeps what yearly loss leaves and gives it to households by income, for goods that qualify as stores at the opening prices. Resources that yield several goods, or count in tonnes, are reported as gaps.
- Tests: `test_economy_store_ratio`, `test_economy_store_usual_price`, `test_economy_opening_stores`, `test_geography_mined_output`, `test_port_opening_stores`.

Findings to act on next:

- For Rome the derived silver stock is not far above the gold stock, because `hispania_silver`, `rio_tinto_jarosite` and the Italian and British placeholders have no `first_worked` or no `endowment` in the deposit data, so they are left out. Print the list with `opening_store_values` in `sim/engine/economy_port_stores.py`. Adding sourced working dates and sizes is data work (do not tune them to a ratio).
- Han, Mexica and Norse have no gold or silver deposit in the data, so their opening stores are empty by that statement; the missing West African, Japanese, Central European and Indian districts are the same gap.
- The working share (`resources_working_share_per_year`) and the loss rate (`METAL_GOODS_LOSS_PER_YEAR`) are unsourced heuristics.
- To measure the ratio, run the 442 scratch driver on the new build in a slow topic; it was not run here.

## Closed (2026-10-09)

The five remaining items, each with where it lives:

1. **Whole-game re-measure.** `sim/tests/test_whole_game_gold_silver_ratio.py`, a slow topic: it steps a game per civilisation and prints the gold-to-silver price ratio at the capital by year, what the state and the households hold of each metal, and what each opening store leaves out. Its one hard check is physical (where both metals trade, gold costs more per kilogram than silver). Run: `python3 -m sim.tests --slow --only whole_game_gold_silver_ratio`. It was not run where this was written (a whole game takes too long there); the size of the ratio is measured, not asserted.
2. **Ornament need.** Kept equal per kilogram, on this reasoning. What makes an ornament metal prized is that it does not tarnish, its colour, and that it works thin. Gold is denser, so a kilogram of it covers less surface than a kilogram of silver, which favours silver per kilogram; gold keeps its face without cleaning, which favours gold. The two effects run in opposite directions and are each of order a small multiple, while the attested price gap is an order of magnitude and follows scarcity (`gold-silver-value-second-pass.md`). So an equal effect per kilogram is within the physical uncertainty for ornament use, and no per-good weight is added. What ornament demand does under equal effect is take whichever metal is cheaper per kilogram, so it cannot hold gold's price up; the ratio comes from the store demand, which splits by carrying return and so rises with the stock gap by less than the gap (`test_economy_store_ratio`). The data note on the ornament need (`data/world/needs.json`, owned by Complaint 434 work in parallel) was not edited; its `effectiveness_basis` still reads as a cultural quantity.
3. **Deposit workings.** No report gives a working date or a total size for `hispania_silver`, `rio_tinto_jarosite`, `italia_silver_generic` or `britannia_silver_generic`. Each now carries a `working_unknown` note (confidence letter, what was read, the primary to obtain) and no invented date or size; `test_deposit_workings_stated` fails any gold or silver deposit that has neither a date and size nor that note. Sourced facts that do not give a total are recorded in the note (Polybius via Strabo on the scale at Carthago Nova, the inferred yearly output of Kay 2014, the Rio Tinto slag mass as a ceiling). One real gap was filled: `dacia_vein_gold` gets `first_worked` from the Roman conquest, confidence D. Unknown workings do not block closing: the derivation lists them as left out and the slow topic prints them. The consequence is stated: Rome's opening silver store counts Laurion only, so it is a lower bound until Domergue 1990 or Anguilano et al. are read. Han, Mexica and Norse have no gold or silver deposit in the data and open empty, as stated.
4. **A held good's service.** `store_return.service_values_per_year`: a durable good that meets a need is worth, a year, its effect per unit over its service life at what a unit of that need costs the household anew; `carrying_return` adds it as a share of the price. No field was added to `GoodSpec`: the effect is already in the basket and the life in the spec, so a second copy would drift. The service is counted without a satiation limit, declared `STORE_SERVICE_UNLIMITED`. Test: `test_economy_store_service`.
5. **State reserve.** `sim/economy/state_store.py`: the cash the state leaves unplanned beyond its reserve is bid into the same store goods, split by the same rule (`households_store`), and the excess over its target, or enough to meet a deficit, is offered back. The lines do not use up the store (`state_budget.goods_bids`, `close_year`). The state carries an expected inflation of its own, updated like a household's. Test: `test_economy_state_store`.

Not run where this was written: `test_economy_state_budget` and `test_economy_agent_state` (each builds a game). `test_economy_service_lives` already failed two checks before this work; with a state that now keeps cash out of circulation in its small fixture, one of them fails on a different assertion (the fixture's income no longer keeps growing).
