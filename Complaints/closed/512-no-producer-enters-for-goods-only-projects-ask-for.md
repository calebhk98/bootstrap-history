# No producer enters for goods only projects ask for

**Status:** closed. The founder's year of draws on materials (bought at the market edge or taken by running works) now reaches firm entry as fixed-quantity bids (`YearInputs.standing_bids`, `sim/economy/standing_demand.py`, built in `sim/engine/economy_port_actors.py`), so a good only a project asks for draws a maker as any other bid does; nothing clears against them. Test: `python3 -m sim.tests --slow --only economy_entry_for_standing_bids`.

The related finding of Complaint 629 (merchants' pack saddles, river barges and merchant ships got no maker) had a different cause: their cordage needs the rope walk, which Rome did not hold, so `makeable_prices` dropped all three carriers' prices, they had no market and the merchants' replacement bids were skipped. Rome now starts holding `tex_rope_walk` (with `cap_measure_len` and `units_standards`, its prerequisites), and all three are priced and made. Firm entry's reading of fixed-quantity bids was not at fault (the same test shows it).

A good a held technique makes and the price table prices (alum, salt, chalk, bone, beeswax in a fresh Rome) can
have no deposit on the tiles held and no producer plant, so the market half of the supply throttle is zero for
it and every project or standing installation that draws it runs at the throttle floor for the whole game.
`material_supply_route` now names this case ("makeable") and the shortage says so, but nothing changes it:
the agent economy opens producers for what households ask for, and a project's or an installation's draw is
not a bid that attracts one.

Measure: `python3 -m sim.tests --slow --only material_reach_whole_game`; to list the goods,
call `material_supply_route` on every material key the tree names in a fresh `sim(civ="rome_100ad")` and count
the `makeable` ones. Eight years of play do not change the answer for the goods checked.

What it would take: project and standing draws entering the economy as demand (`note_actor_purchase` exists)
so that firm entry in `sim/agents/firm*.py` can answer them, or the tree naming an operating concern for each
such recipe (`operated_by`, see 504). Both are in files other work owns, so this is filed rather than done.
Related: 504.

## Stage 3 of Complaint 507 (the purchase reads the economy's price) did not close this

A project's bill now reads the economy's price on the founder's tile, and the economy has a market (and a price) for
alum, salt, chalk and beeswax: the price is the opening's seed, since no producer has made any of them since.
The draw is still not a bid. A founder's purchase pays the market edge and receives stock at once
(`GoodsMarket.settle_purchase`); the economy sees it only as a count of tonnes for the year, which it does not
turn into orders, so the book it clears has no buyer for the good and entry has no unmet demand to answer. Making the
draw a bid means the economy delivers the goods (the purchase clears in its book and is limited by what its sellers
offer), which is Stage 4 of `docs/architecture/ONE_PRICE_OWNER_PLAN.md` (`market_available_tonnes_per_year` becomes the
offered quantity at the tile). Close this there, with the test that a producer enters for a good only a project asks for.
Measure now: `python3 -m sim.tests --slow --only material_reach_whole_game`.
