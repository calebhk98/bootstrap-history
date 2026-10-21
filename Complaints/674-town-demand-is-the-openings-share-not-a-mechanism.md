# The share of people in town is bounded by the food a town can draw, but what asks for town people is the opening's typed share

**Status:** open

Left over from 603. A region's urban people are never more than its farms' surplus plus what it can carry in
(`sim/world/urban_share.py`), but below that ceiling the share is the civilisation's typed `urban_fraction`, read once at the opening
and kept as each region's share of its people (`state.population.urban_share_of_people`). The ceiling is far above the
typed share (`python3 -m sim.tests.urban_share_opening` prints both), so food rarely binds in a baseline and the share does not rise
or fall with the things that build towns.

**What it would take.** A demand side from lower-level state: the state's taxes and the landowners' rents spent in a
town (the harvest share the state takes, `sim/agents/tax_burden.py` `harvest_share_taken`, is nothing for Han China, England and the Mexica, which hold their claims in other forms), the trade a port carries, and an urban band that rural workers move into when real income there beats
the countryside (`sim/labour/market/migration.py` `move_shares`), with the urban mortality premium (town providers) returning the
graveyard effect. Then the typed figure is only a validation. Depends on 536 and 634 (a tile's town), 590 (foreign countries).

**Heuristic to retire.** A region's opening share of its people in town is held for the whole game.
