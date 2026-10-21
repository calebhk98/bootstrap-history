# Most tree nodes charge upkeep as a concern but make nothing: knowledge and plant are one object

**Status:** open - owner direction (2026-10-14): tech nodes are knowledge only; a business is a firm an actor runs (plan: `docs/architecture/FIRMS_OWN_PLANTS_PLAN.md`; with 514)

`python3 -m sim.engine.validate_unlinked_producers` lists the nodes that carry upkeep but gate or operate no
production entry. It is most of the tree, largely staffed engineering nodes. 504 linked the few twins that
had an entry; adding a recipe per node cannot close the rest, because a tree node stands for two things:
a piece of knowledge (which costs nothing to hold once learned) and a concern a player opens (which costs
upkeep and should sell its product).

What it would take: decide which nodes are concerns. Knowledge nodes carry no upkeep and earn nothing
themselves; they unlock recipes, plants and better yields on entries others run. A node that is a concern
names the production entry it operates (`operated_by`) and its plant. `validate` then reports a node with
upkeep and no entry as an error. The nodes that make a good with no production entry yet (brushes, lenses,
sintered ore) get one with a demand side.

## Owner direction (2026-10-14)

A tech node is knowledge and nothing else: holding it costs nothing and it earns nothing itself. A business is a
firm, owned by an actor (founder, firm, state), that runs one or more plants, each plant a production entry's
physical unit with its own crew. "Opening lead" means founding or buying a firm that runs lead-smelting plants;
the number of plants, and so the size of the firm, follows what it can sell. Upkeep belongs to plants and firms,
never to nodes. See 514 for the founder's ventures, which are a second implementation of the same thing.

## Opening check: do plants pay their way (merged from 528)

Owner decision (2026-10-19): a technology never earns anything. Knowing how to do something makes no money; money
comes only from people buying or using what is made with it (a good, a service, the use of a plant), or from the
holder using it to save cost. So a check over tree nodes ("what share of the technologies a society holds pay at its
opening") is the wrong question. The check is over plants and firms that make and sell goods: at an opening, the
plants the society runs (the producers the opening sizes) cover their costs from what they sell, within the spin-up's
settling (473); a concern that sells nothing earns nothing.

Why it was filed: after 507 stage 3 (actors pay the economy's prices) a scan of the default Rome opening found almost
no concern whose takings exceeded its wages and rent, so firms did not enter and the founder had few ways to earn.
Likely causes, to measure: input prices far above making cost (519), the opening's low wages and income (526), and
node takings that still come from node fields rather than the plant's own output at market prices (this complaint
and 514). The scan used node takings, which is the thing this complaint removes; a plant-level check depends on 510
and 514 landing.

Measure: `python3 sim/simulator.py opening-checks --civs rome_100ad --concerns-only` (add `--json` for structured
rows) counts, per civilisation, the held concerns whose takings exceed their running cost and lists the payers and
the biggest losers. It is reported, never a failing check; it reuses the entry test's figures
(`SimWorld.entry_gross`, `business_books.yearly_costs`, `firm_entry.carrying_cost`) in `sim/agents/concern_scan.py`.
Open: `finery_puddling` pays with takings several times what `origin/main` showed for it; the cause is not traced
(`sim/tests/test_firm_entry_default_game.py` uses it).
