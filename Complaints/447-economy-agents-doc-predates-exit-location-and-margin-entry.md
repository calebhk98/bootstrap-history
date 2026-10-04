# ECONOMY_AGENTS.md describes entry, exit and placement as they were before round four

**Status:** open - `docs/architecture/` is outside the economy package

`docs/architecture/ECONOMY_AGENTS.md` says demand brings makers only where buyers were turned away,
that a producer with no capacity closes, and nothing about where producers sit. Since round four
(`Complaints/reports/agent-economy-review-round-four.md`):
- producers are placed over a market's tiles by labour, cost and site limits (`sim/economy/location.py`,
  `sites.py`), crops only on tiles of their climates;
- a lasting margin over full cost draws newcomers where buyers' demand is elastic over the gap, and a
  market with buyers and no maker draws a trial newcomer (`sim/economy/entry_margin.py`);
- a producer with no variable margin after its loss years exits, repaying its lenders first
  (`producers_close.py`, `producer_exit.py`); plantless capacity follows use;
- the economy has a published surface, `sim/economy/api.py`.

What it would take: rewrite the "Demand brings makers" paragraph and add placement and exit.
