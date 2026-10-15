# No producer enters for goods only projects ask for

**Status:** open

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
