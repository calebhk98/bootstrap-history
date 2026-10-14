# Most tree nodes charge upkeep as a concern but make nothing: knowledge and plant are one object

**Status:** open - owner direction (2026-10-14): tech nodes are knowledge only; a business is a firm an actor runs

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
