# Built concerns make nothing, because the recipe names a twin node

**Status:** open

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
