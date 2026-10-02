# Goods prices follow a solved long-run cost of the techniques in use, not each producer's cost and supply

**Status:** open - the owner's principle: a market price comes from the supply of producers who actually produce, at the cost of the technique each actually runs, against demand; a technology that is invented but unused changes no price, and the market does not know the tech tree. Today's code gets half of this.

Done (Complaints 369, 370): the price solver is asked about the techniques some producer runs, not about everything held (`sim/engine/techniques_in_use.py`: the starting techniques, the founder's operating nodes, every firm's concerns). Readers moved: `Sim._material_prices`, `Sim.material_price_basis`, the `_done_memo` stamp (`sim/engine/economy_materials.py`), the concern ratios (`sim/engine/concern_volume.py`).

Still pricing from a technique that need not be run by whoever sells:
- `sim/engine/economy_materials.py:_material_prices`: one solved cost per material for the whole society, from the cheapest entry among the techniques in use. The solver (`sim/engine/prices.py:solved_prices`) picks the cheapest entry in reach for every material, so as soon as one producer runs a cheaper entry every producer of the good is priced at it, whether or not it has adopted it.
- `sim/engine/techniques_in_use.py`: a technique counts for every producer the moment one runs it (labelled temporary).
- `sim/engine/goods_market_offers.py:_worked_out_offers` and `sim/engine/market_demand.py`: household prices are the solved cost, with the spot ratio on top; supply (`sim/engine/actors/supply.py:concern_output_tonnes`) is the declared yearly output, not what staff and entries make for nodes that declare none.
- `sim/engine/node_revenue.py:for_civilisation` and `sim/engine/data.py:load`: revenue and upkeep derived once at the starting techniques.
- The founder's project costs and quotes (`project_cost`, `material_price_factor`) read `_material_prices`.

What would replace it: each producer's cost from the entry it runs and its own wages and inputs; supply from the producers' volumes (`concern_volume`); price from clearing that supply against household demand, with the solver kept only as the cost of the marginal producer and as a baseline for goods nobody yet makes.

Related: 369, 370, 354.
