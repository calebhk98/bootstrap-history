# Research behind the multiplayer actors

Four surveys were run for this design, covering strategy games, scientific economic simulations,
software engineering, and fiction about knowledgeable outsiders. None of them could open its sources
live. The pointers below are from the researchers' own knowledge and need checking before anyone
quotes them. Nothing here is a measured fact about this simulator.

## Adopted

- **People as aggregates, not individuals.** Use one stratum per (country, body of people) with
  headcount, purse, literacy and unmet needs. This follows Victoria 2 and 3 pops, Anno tiers, and
  the "super-individuals" of agent-based ecology. Cost then grows with countries times strata, not
  with population.
- **Standard of living as a welfare ratio:** income over the cost of a subsistence basket at the
  simulator's own prices (Allen's welfare ratios). Growth responds to it with a lag. Deaths rise
  steeply below subsistence and births rise gently above it (Malthusian and Lee feedback). Shortfall
  falls on whoever cannot pay, which is the Sugarscape metabolism rule, so nobody is chosen to
  starve.
- **Needs in tiers:** food, then housing, then other goods (Anno, Victoria 2). Each tier is bought
  only from what is left after the one below.
- **Mobility as a function of state, never a fixed matrix.** Rising depends on surplus over
  subsistence and literacy, and falling depends on deficit. A fixed transition table is the usual
  way a hardcoded outcome sneaks in. Bondage has its own entry and exit, not the generic ladder.
- **Free entry with a bound.** A competitor enters while the expected margin pays the stake and the
  market's rate. The number of operators already sharing the market lowers the expected margin, and
  exit follows sustained losses (Hopenhayn, the CATS model, Capitalism Lab). This is how
  `consider_entry` already works. Trader entry follows the same rule.
- **Traders size to a share of the gap.** A trader carries a good where the destination price
  exceeds the origin price plus freight, a year's interest on the cargo, and risk. It is limited by
  its capital and sized to a share of the gap, so traders do not overshoot together (Patrician, the
  law of one price). Freight comes from the geography package, never from a table per pair.
- **Diffusion needs a carrier.** A foreign country learns an invention as it is exposed to it, and
  exposure falls with distance (Comin and Hobijn). The registry's exposure question already scales
  with distance.
- **Simple NPC decisions.** NPCs use a ranked option list within budget (`ValuePolicy`), which is
  what the EU4, Patrician and Offworld AIs amount to. They do no planning.
- **Engineering:**
  - Commands are plain records with a journal.
  - Randomness is per actor, from a hash of (seed, actor, year), through `world.rng_for`, so adding
    an actor does not shift another's draws.
  - Kinds and spawners go in registries.
  - Unit tests run against a small fake world (`sim/tests/agents_fake_world.py`).
  - A conservation check runs over every year.

## Noted for later, not built

- **Simultaneous turns (WEGO).** Every player's orders would be validated against the start-of-year
  state and resolved by an explicit rule. Today actors act in id order, which favours the lowest id.
- **Seeded shuffle of the order actors act in.**
- **Lighter yearly turns for distant or minor actors.**
- **Tombstoning exited actors** to keep saves small.
- **A per-actor cost budget test under `--slow`.**
- **From fiction (1632, Lest Darkness Fall, Connecticut Yankee, Bookworm):**
  - Copying is fast for what can be copied by inspection and slow for what needs tooling and skills.
  - States answer a visible, profitable outsider with patronage, a tax or monopoly, confiscation or
    war, depending on fiscal need and the outsider's standing.
  - Incumbents resist in proportion to the income they lose (interest groups already do this).
  - A project that depends on one founder's protection is fragile.
  - NPCs must pursue their own ends (copy, undercut, defect) rather than cooperate by default.

## Pointers (unverified)

- Victoria 3 wiki: <https://vic3.paradoxwikis.com/Pops>
- EU4 trade: <https://eu4.paradoxwikis.com/Trade>
- Lengnick, agent-based macro baseline: <https://www.sciencedirect.com/science/article/pii/S0167268113000759>
- Dosi, Fagiolo and Roventini, K+S: <https://www.sciencedirect.com/science/article/pii/S0165188909000980>
- Godley and Lavoie, stock-flow consistency: <https://link.springer.com/book/10.1057/9780230626546>
- Anderson and van Wincoop, gravity: <https://www.aeaweb.org/articles?id=10.1257/000282803321455214>
- Comin and Hobijn, diffusion: <https://www.aeaweb.org/articles?id=10.1257/aer.100.5.2031>
- ORBIS (Roman routes, validation only): <https://orbis.stanford.edu>
- Game Programming Patterns, Command: <https://gameprogrammingpatterns.com/command.html>
- Age of Empires lockstep: <https://www.gamedeveloper.com/programming/1500-archers-on-a-28-8-network-programming-in-age-of-empires-and-beyond>
- 1632 series: <https://en.wikipedia.org/wiki/1632_series>
