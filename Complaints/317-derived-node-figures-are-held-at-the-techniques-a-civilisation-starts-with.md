# Derived node figures are held at the techniques a civilisation starts with

**Status:** partly - `node_revenue.for_civilisation(..., held_techs=)` derives and caches on the gate techniques held (`test_node_revenue_held_techs`); still open: the `Sim` calls it once at construction with the starting techniques, so nothing re-derives when research changes the held set

`node_revenue.for_civilisation` derives each output node's revenue and upkeep once per civilisation, at the goods table, graded energy prices and wages of the technologies it holds when the `Sim` is built (`starting_techs`). A game spans centuries: the founder's own research changes what the civilisation can make and at what cost (iron by blast furnace, cheaper heat, a cheaper carrier), and the node's revenue stays at the starting prices. The yearly market ratio (`Sim.node_output_market_factor`) moves it with the price of what it sells and buys, but not with what the civilisation has learned to make.

A good priced at the "mature" fallback (`python3 -c` over `data.goods_provenance` listing materials not `solved`) also enters a node's revenue at a technique nobody in reach holds; the same holds for an energy requirement graded at the mature table (`sim/engine/energy_prices.py` falls back to it when no held technique reaches the temperature).

What it would take: re-derive (cache key already includes the held gate set) when the set of held gate technologies changes, and say which node figures a player sees move. Measure with `python3 sim/node_revenue_report.py` (script since removed; recover with `git show 97473f1:sim/node_revenue_report.py`) at two held sets. See `Complaints/283`, `Complaints/310` (closed), `Complaints/302`.

Related: 140, 295, 318, 329, 335, 336, 337.
