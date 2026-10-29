"""Opening what plainly pays for itself: `auto_open` is off for a player and on for the optimizer (`default_policy`), and the concerns
`auto_open_ventures` considers are the completed, idle, unexcluded ventures that earn more than they cost to keep, best margin for the
money they tie up first (the projects module's `_auto_open_ordinary_candidates`, over plain values). The opening itself is test_affordability_and_credit."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.seat_defaults import default_policy
from sim.tests import projects_host

check("auto_open is off by default for a player", default_policy(manual=True)["auto_open"] is False)
check("...and on for the optimizer", default_policy(manual=False)["auto_open"] is True)

NODES = {
    "big_margin_dear": {"rev": 3300.0, "up": 100.0},      # margin 3200 on 3200 capex
    "small_margin_cheap": {"rev": 460.0, "up": 60.0},     # margin 400 on 60 capex
    "loss_maker": {"rev": 10.0, "up": 50.0},
    "break_even": {"rev": 50.0, "up": 50.0},
    "running": {"rev": 900.0, "up": 100.0},
    "excluded": {"rev": 900.0, "up": 100.0},
    "not_a_venture": {"rev": 900.0, "up": 100.0},
    "not_built": {"rev": 900.0, "up": 100.0},
}
CAPEX = {"big_margin_dear": 3200.0, "small_margin_cheap": 60.0, "running": 10.0, "excluded": 10.0}


operating = {"running"}
game = projects_host.build(
    tree=NODES, projects_record=SimpleNamespace(done=set(NODES) - {"not_built"}, operating=operating), operating=lambda: operating,
    techniques_held=set(NODES) - {"not_built"}, is_venture=lambda node_id: node_id != "not_a_venture",
    venture_capex=lambda node_id: CAPEX.get(node_id, 1.0))
game.exclusion_reason = lambda node_id: "held back" if node_id == "excluded" else None
candidates = game._auto_open_ordinary_candidates()
check("only completed, idle, unexcluded ventures that earn more than they cost to keep are candidates",
      set(candidates) == {"big_margin_dear", "small_margin_cheap"}, candidates)
check("the best margin for the money it ties up comes first, not the best margin outright",
      candidates == ["small_margin_cheap", "big_margin_dear"], candidates)
