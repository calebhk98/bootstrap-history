# The founder's goods concerns displace no incumbent producers, so cloth and print make no groups

**Status:** open

Interest groups (114) form around income the founder's doing takes from others. For materials that income is measured: the market clearing says how many tonnes the society's producers sell less because the founder sells (`society_sales_displaced_by_founder`). For the goods categories (textiles, processing, printing, ...) the engine has no such figure. `goods_market_factor` is a price ratio over the founder's own takings and there is no revenue for the society's existing weavers, printers or brewers to lose, so a founder who dominates a goods category displaces nobody on screen and no group forms, however the real handloom-weaver case ran.

What is needed is a society-side producer in each goods category (capacity, revenue, the people it keeps) that the category's price depression and the founder's and firms' share take from, the way the materials book already does for tonnes. With it the displaced-producers source in `GroupView.displaced_producers` extends to goods without any engine special case.

A related gap: displaced-producer groups for materials form only when the player sells. Only the player's `sell` command sells material stock (`sell_material_stock`), so an automatic run never displaces a producer. The founder's own concerns' output does not reach the market's flows, so what he makes and uses or keeps displaces no one either; routing concern output through the same sold flows would let his production, not only his stock sales, organise producers.

See also 110 and 311.
