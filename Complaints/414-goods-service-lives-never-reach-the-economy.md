# Goods' service lives never reach the agent economy, so tools and ornaments are used up within the year

**Status:** open - needs `sim/engine/economy_port_setup.py` and a data source

`sim.economy.setup.goods_specs` takes `service_lives`, and the economy already treats a good with a
service life as a durable: households hold a stock, buy only to keep it up, and it wears
(`households_orders._durable_ratio`, `households_close`, `inventory.wear_moves`). The port calls
`goods_specs({good: "" for good in goods}, spoilage)` with no service lives
(`sim/engine/economy_port_setup.py`, `build_setup`), so every good is consumed in the year it is
bought: an iron tool, a bronze pot and a gold ring are bought afresh every year like bread.

Why it matters: metal demand is then a large yearly flow instead of the upkeep of a stock, and metal
prices are formed on flows (Complaint 387); gold and silver cannot be held as wealth (413).

What it would take: a service life per good in data (for example beside the spoilage rates in
`data/world/spoilage.json`), and the port passing it. The port also passes an empty category for
every good; categories from data would let checks pick goods by kind instead of by id.
