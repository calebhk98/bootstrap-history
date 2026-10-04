# A game has one goal id, one reach year and no "what controls this metric" hook

**Status:** open

Three engine limits block the rest of 268 and 69:

- **One reach year.** `goal_year` is set once, the first time the goal node completes (`sim/engine/projects_completion.py`, `core.py`). A second goal set after a win never records its own year, and the end text names the first goal's year.
- **Changing the goal mid-game.** `sim.goal` is a plain attribute; caches keyed on it (`_goal_closure`, read by `fog.py`, `labour_port.py`, `society_hazards.py`) are not invalidated, and `ui_port` offers no safe way to change it. The UI therefore tracks extra goals itself and never changes the formal one.
- **No anatomy hook for measurement goals.** `_win_condition_value` (`core.py`) computes a measurement goal's value privately and nothing returns its contributors. The UI explains the known metrics (literacy, epidemic relief) by reading their public parts; a mod adding a new metric gets only a generic explanation. A public `win_condition_anatomy(condition)` returning `[(label, value, unit)]` per metric would make the view generic.

Related: 69, 268, 220.
