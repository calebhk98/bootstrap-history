# Built concerns make nothing, because the recipe names a twin node

**Status:** partly - lead_metallurgy, mt2_zinc_by_retort and pwr_coking now operate the lead, zinc and coke entries; the rest below needs recipes

Almost every concern that costs money to run earns nothing. Count them with:

    python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine import data; nodes=data.load()[0]['nodes']; cost=[n for n in nodes if (n.get('up_hours') or 0)>0]; print(len(cost), sum(1 for n in cost if (n.get('rev') or 0)>0))"

(nodes with a running cost, then how many of them earn). Revenue comes only from nodes that gate a
production entry (`sim/engine/node_output.py` `entries_gated_by`). Many nodes that plainly make something
gate nothing, because the recipe names a different node for the same technique:

- `lead_metallurgy` ("Lead sheet, pipe, litharge ...") gates nothing. `lead_kg` is gated by `mat_lead`.
  Opening it costs a large upkeep and sells no lead.
- `mt2_zinc_by_retort` gates nothing. `zinc_kg` is gated by `zinc_metal`, a separate node that earns
  well but costs orders of magnitude more to start.
- `gp_carbon_brushes`, `lens_grinding`, `pwr_coking` and `mt2_sintering_process` make goods with a
  market, but gate no entry, so opened they earn nothing and only cost upkeep.

In a Rome playtest (`play --civ rome_100ad --kit merchant --seed real25`), `available sort net reverse`
showed nothing startable with a positive net, and the only income past the founder's practice was the
workshop's wage markup (`workshop_output`). That is a single heuristic standing in for the whole
productive economy.

Why it matters (CLAUDE.md 4.1, 4.3): a lead works that sells no lead and a coking plant that sells no coke
are not realistic. The player can't earn the way a real entrepreneur would, by making something and
selling it, so the opening runs on one lever.

What it would take: a `validate` check listing nodes that carry upkeep, gate no production entry and
belong to a category that makes goods. Then either link each to its entry (`operated_by` already allows
several operators per entry) or merge the twin nodes. Add a test that the twins above earn when opened.

## Update

Measure with `python3 -m sim.engine.validate_unlinked_producers` (also printed by `simulator.py validate`):
it counts nodes with upkeep that gate or operate no production entry, by category and kind. Most of the
tree is in that list; the large majority are staffed engineering nodes, and many make no good at all.

Linked (an existing entry already made exactly their good; they were added to its `operated_by`):
`lead_metallurgy` on `lead_kg`, `mt2_zinc_by_retort` on `zinc_kg`, `pwr_coking` on `carbon_kg` (the coke
entry). Regression test: `sim/tests/test_twin_nodes_earn.py`.

Double counting: `node_output` bounds each node by its own staff hours and its own plant, so two operators
of one entry are two separate concerns, each with its own crew and furnace; one set of staff never earns
twice. Both still sell into the same market, which the market factor on `concern_revenue` limits.

Remaining: `gp_carbon_brushes`, `lens_grinding` and `mt2_sintering_process` have no production entry for a
good they make (no brush, lens or sintered-ore good exists), so they cannot be linked. They, and the other
product-making nodes in the measurement, need a recipe for their good and a demand side. That is the
remaining work; the measurement lists the nodes.
