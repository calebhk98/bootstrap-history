# Most tree nodes charge upkeep as a concern but make nothing: knowledge and plant are one object

**Status:** open - follows 504; a modelling question, not a recipe backlog

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
