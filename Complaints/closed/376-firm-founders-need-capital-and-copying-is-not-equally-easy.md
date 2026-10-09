# Firm founders do not need personal capital, and copying a technique is not equally hard for every technique

**Status:** closed - a firm's founder is a household of a stratum with its own wealth, bounded by savings and a lender's equity rule, and what an onlooker can copy is declared in data for every node (its own entry or its category's, each with a reason) and drives what shows of it

Raised by the owner (2026-10-02). Earlier Rome runs reached hundreds to thousands of firms. Firms enter from a pool of society's capital (`ENTREPRENEURIAL_CAPITAL_SHARE` of output, `sim/agents/registry.py` `consider_entry`) plus borrowing, not from particular people who have the money. A labourer cannot found a balloon works; a founder needs savings or a lender willing to back them, and only a few households in an ancient economy had that.

Copying is also not equally easy. A visible, simple device (a wheelbarrow, a hot-air balloon) can be copied by looking at it; a process whose essence is hidden (black powder's proportions and corning, steel's heat treatment, glass recipes) cannot be reverse-engineered from the product. Today copy difficulty comes from the count of trades and materials a node needs (`copy_difficulty`, `sim/engine/society_disclosure.py`).

What it would take: firm founders drawn from households that hold capital (the society's income and wealth distribution in data), each with its own savings and a lender's limit, so entry is bounded by who can actually fund it; and per-technique copy difficulty declared in data (how much of the know-how is visible in the product versus tacit or secret), with a stated basis, replacing the count of trades and materials. Related: 103, 330, 331, 345, 308.

## Closed

- Founders are households: a stratum's savings are spread over its households as a power law (`WEALTH_TAIL_INDEX`, a
  labelled heuristic that replaces the old multiple of average savings); the richest free household puts up a stake,
  keeps it committed while the firm runs, and has it free again when the firm closes. `sim/agents/household_wealth.py`;
  topics `household_wealth`, `firm_entry_capital`.
- Copy visibility is declared for every node: a node's own `copy_visibility` and reason in `data/branches` stands,
  and a node that declares none takes its category's entry from `data/world/copy_visibility.json`, each with a reason
  naming what shows and what does not (`sim/engine/copy_visibility_defaults.py`, checked by `simulator.py validate`;
  a mod can overlay its own). The count of trades and materials remains only for a mod's node in a category nobody
  declared, and `validate` lists those. Topic `copy_visibility`.
- Visibility, not a flat factor, sets what can be copied: a concern run in public shows what its product gives away
  (the reciprocal of its copy difficulty), a kept secret only what leaks; an actor copies only what shows enough from
  its place, and what it already knows decides which steps remain (`sim/engine/visibility.py`, `imitation.in_sight`).
  Topics `seat_sight`, `actor_fog`.
- Remaining nodes are filled by category, not one by one. The 100-odd technique-level declarations override their
  category; refining a category default for a technique that differs is an ordinary data edit, not an open item.
