# An interest group's prohibition reaches almost no technique, and protection lifts it anyway

**Status:** partly - reach: `Sector.reached_by` (sim/agents/group_reach.py) adds a node's own goods category and the commodities of the techniques of its category it refines; protection no longer lifts a prohibition outright, it must exceed the opposition line by the group's pull (`protection_needed`). Measured: techniques reached for iron stay at 3 in rome_100ad and england_1300 (the tree has no refinement of the iron makers in their category); a goods category reaches every technique carrying it (textiles 50, printing 19). Substitutes and the concerns around a good (power, tools) still have no tree relation to follow.

Interest groups (110) can have the state forbid starting the techniques that make the commodity they lost income on. The start gate finds those techniques through `supply.materials_made_by`, the nodes whose `requires_node` gates a production entry for a material of that commodity, and spares any node the state itself values (`state_interest` above zero). In a driven run of a founder selling iron, the prohibition covers a single node in both Rome and England, and it is one the founder has already built, so it stops nothing. The rest of what displaces the producers (the concerns that make the founder's goods, the power and tools around them) is not linked to the commodity at all. Separately, the founder's protection in those runs sits far above the state-opposition line, which lifts the prohibition outright.

What is needed is a link from the loss to the techniques that cause it that does not depend on production-entry gates: a concern's outputs and the substitutes they replace (the same relation a market clearing uses when the founder's sales displace the society's), and a decision on whether protection should lift a prohibition the state made at an organised group's request or only bargain it down as it does a levy.

See also 110, 311 and 312.

Owner decision (2026-10-02): can be a mod; deferred.
