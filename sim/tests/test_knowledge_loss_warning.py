"""knowledge_loss_warning: the escalated warning for a sacking window that is close or running (Complaint 640:
the rule is called on a stub game built here; the `state` and `path` replies on a whole game are in
test_knowledge_loss_warning_scenario)."""
QUICK_TOPIC = True

import types

from .harness import *  # noqa: F401,F403
from sim.engine.knowledge_warning import WARNING_HORIZON_YEARS, knowledge_loss_warning, warning_lines
from sim.tests.ui_stand_in import Game

WINDOW = (200, 204)


def _nodes():
    return {"base": {"name": "Base", "pre": []}, "step": {"name": "Step", "pre": ["base"]},
            "weak_hedge": {"name": "Weak", "pre": ["step"]}, "strong_hedge": {"name": "Strong", "pre": ["weak_hedge"]},
            "cheap_hedge": {"name": "Cheap", "pre": []}}


def _game(year, at_risk=10.0, hedges=(("strong_hedge", 0.05, 0.1), ("weak_hedge", 0.1, 0.5)), held=(), done=(),
          sacks_a_site=True, fog=False):
    nodes = _nodes()
    risk = {"technologies_at_risk": at_risk, "expected_technologies_lost_per_sacking": at_risk * 0.9,
            "known_hazards_ahead": [{"name": "A sack", "years": list(range(WINDOW[0], WINDOW[1] + 1)),
                                     "sacks_a_site": sacks_a_site}]}
    return Game(
        year=year, nodes=nodes, fog=fog, done=set(done), knowledge_risk=lambda advice=True, chronology=True: risk,
        corpus_hedge_tiers=lambda: list(hedges), has=lambda node_id: node_id in held,
        is_visible=lambda node_id: True, project_cost=lambda node_id: 100.0)


check("no escalated warning while the sacking window is farther than the horizon",
      knowledge_loss_warning(_game(WINDOW[0] - WARNING_HORIZON_YEARS - 1)) is None)

_near = knowledge_loss_warning(_game(WINDOW[0] - 25))
check("within the horizon of a sacking window the warning exists and names the window and the years until it",
      _near is not None and _near["years"][0] == WINDOW[0] and _near["years_until"] == 25 and not _near["in_progress"], _near)
check("it quotes the risk's own expected loss per sacking and technologies at risk",
      _near["expected_technologies_lost_per_sacking"] == 9.0 and _near["technologies_at_risk"] == 10.0, _near)
check("it names the cheapest hedge with its steps away (the unbuilt nodes in its closure) and cost",
      _near["cheapest_hedge"]["id"] == "weak_hedge" and _near["cheapest_hedge"]["steps_away"] == 3
      and _near["cheapest_hedge"]["cost"] == 300.0, _near["cheapest_hedge"])
check("the hedge says what is expected to be lost once it is built",
      _near["cheapest_hedge"]["expected_technologies_lost_per_sacking_once_built"] == 5.0, _near["cheapest_hedge"])

_closer = knowledge_loss_warning(_game(WINDOW[0] - 25, done=("base", "step")))
check("nodes already built are not steps away and not paid for",
      _closer["cheapest_hedge"]["steps_away"] == 1 and _closer["cheapest_hedge"]["cost"] == 100.0, _closer["cheapest_hedge"])

_running = knowledge_loss_warning(_game(WINDOW[0] + 2))
check("a window running now is flagged as in progress", _running and _running["in_progress"] and _running["years_until"] == 0, _running)

check("fully hedged: no stronger hedge to name, no warning",
      knowledge_loss_warning(_game(WINDOW[0] - 25, held=("strong_hedge",))) is None)
_one_stronger = knowledge_loss_warning(_game(WINDOW[0] - 25, held=("weak_hedge",)))
check("a hedge already held is not offered, only a stronger one", _one_stronger["cheapest_hedge"]["id"] == "strong_hedge", _one_stronger)
check("nothing built by you means nothing to lose, so no warning", knowledge_loss_warning(_game(WINDOW[0] - 25, at_risk=0.0)) is None)
check("a window that sacks no site gives no warning", knowledge_loss_warning(_game(WINDOW[0] - 25, sacks_a_site=False)) is None)

# presentation: the warning line is text a player reads
_lines = warning_lines(_near, "denarii")
check("the warning line names the window, the hedge and the money unit",
      len(_lines) == 1 and "WARNING" in _lines[0] and "200" in _lines[0] and "weak_hedge" in _lines[0] and "denarii" in _lines[0], _lines)
check("no warning, no line", warning_lines(None) == [])
