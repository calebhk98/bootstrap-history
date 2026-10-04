# The founder's goods concerns displace no incumbent producers, so cloth and print make no groups

**Status:** partly - goods categories now have incumbents: `GroupView.goods_categories` (sim/engine/agents_port_groups.py) gives each category's price depression (goods_category_price_ratio) and each trade's share of work in it; `Sector.of_goods` (sim/agents/group_goods.py) turns the strata whose trades make it into a displaced_producers sector (loss = depression x their income in the category). Measured with three textiles-category concerns marked operating on rome_100ad (scratchpad c_goods.py): before no sector; after `displaced_producers:textiles`, about 11M lost, about 105k people. The trade-to-category share is a labelled heuristic (hours in the tree). Not done: founder concern output reaching market flows, and separating the founder's from the firms' share of the depression.

Interest groups (110) form around income the founder's doing takes from others. For materials that income is measured: the market clearing says how many tonnes the society's producers sell less because the founder sells (`society_sales_displaced_by_founder`). For the goods categories (textiles, processing, printing, ...) the engine has no such figure. `goods_market_factor` is a price ratio over the founder's own takings and there is no revenue for the society's existing weavers, printers or brewers to lose, so a founder who dominates a goods category displaces nobody on screen and no group forms, however the real handloom-weaver case ran.

What is needed is a society-side producer in each goods category (capacity, revenue, the people it keeps) that the category's price depression and the founder's and firms' share take from, the way the materials book already does for tonnes. With it the displaced-producers source in `GroupView.displaced_producers` extends to goods without any engine special case.

A related gap: displaced-producer groups for materials form only when the player sells. Only the player's `sell` command sells material stock (`sell_material_stock`), so an automatic run never displaces a producer. The founder's own concerns' output does not reach the market's flows, so what he makes and uses or keeps displaces no one either; routing concern output through the same sold flows would let his production, not only his stock sales, organise producers.

See also 110 and 311.

Related: 313.

Owner decision (2026-10-02): can be a mod; deferred.
