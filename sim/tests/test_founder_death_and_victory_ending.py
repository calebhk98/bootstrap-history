"""SCENARIO (Complaint 640): founder death and the ending in a running game (the losable list is test_losable_nodes.py).

Complaints 220, 251, 252, 253, 255, 260: founder age, the ending after a dispersed corpus, achievements announced once,
the civilisation after the start, and the victory block with a finish-and-score command. The wording of the age line,
the death notice about deputies and the victory screen is presentation and not tested here."""
from .harness import *  # noqa: F401,F403


def _new_sim(civ="rome_100ad", mortal=True, fog=False):
    new_sim = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                    civ=S.load_civ(civ), cfg={"immortal": not mortal})
    new_sim.fog = fog
    new_sim.goal, new_sim.done_year = GOAL, {}
    return new_sim


def _die(mortal_sim):
    mortal_sim.founder_alive, mortal_sim.life_left = True, 1
    mortal_sim._step_founder_mortality()
    return [message for _, message in mortal_sim.log]


# 255: the age is shown
_alive = _new_sim()
_alive_out = S._agent_state(_alive, NODES)
check("a mortal founder's state carries the age as a number",
      _alive_out.get("founder_age") == _alive.cfg["founder_arrival_age"], _alive_out.get("founder_age"))

# 257: a dispersed corpus is named when the run ends
_dispersed = _new_sim()
_die(_dispersed)
run_it(_dispersed, "corpus_dispersed")
_dispersed.state.projects.stalled = _dispersed.DISSOLUTION_YEARS_UNTIL_END - 1
_dispersed._step_founder_mortality()
_end_text = _dispersed.dead_reason or ""
check("the run ends, and the ending names the dispersed corpus that survived",
      bool(_end_text) and "survive" in _end_text, _end_text)
check("a dispersed corpus is not forgotten by the dissolution",
      "corpus_dispersed" in _dispersed.done, None)

# 259: measured goal nodes are never forgotten, so never announced twice
_win_id = next(node_id for node_id, node in sorted(NODES.items()) if node.get("win_condition"))
_forget = _new_sim()
_die(_forget)
_forget.done.add(_win_id)
_forget._done_changed()
_forget.state.projects.stalled = _forget.DISSOLUTION_YEARS_BEFORE_FORGETTING - 1
_forget._step_founder_mortality()
check("dissolution does not forget a measured goal node", _win_id in _forget.done, None)

# 264: the running game names the civilisation by its short name
_pop = S._agent_dispatch(_new_sim(), NODES, {"cmd": "population"})
check("population still names the civilisation", bool(_pop.get("civilisation")), None)

# 224: victory block, and finish-and-score under fog
_win = _new_sim(fog=True, mortal=False)
_win.end_year = _win.cfg["start_year"] + _win.cfg["horizon_years"]
_real_step = _win.step


def _step_and_win():
    _real_step()
    _win.goal_year = _win.year


_win.step = _step_and_win
_win_out = S._agent_dispatch(_win, NODES, {"cmd": "step", "years": 1})
_victory = _win_out.get("victory") or {}
check("reaching the goal returns a victory block with date, years and how to score",
      _victory.get("year") == _win.year and "elapsed_years" in _victory
      and "finish" in (_victory.get("to_see_your_score") or ""), _victory)
_before = S._agent_dispatch(_win, NODES, {"cmd": "score"})
check("under fog the total is withheld before finishing", _before.get("total") is None, _before.get("total"))
_finish = S._agent_dispatch(_win, NODES, {"cmd": "finish"})
check("finish ends the run and reveals the total",
      bool(_finish.get("ok")) and (_finish.get("score") or {}).get("total") is not None
      and bool(S._agent_end_reason(_win)), _finish.get("score"))
check("after finishing, commands that move the game on are refused",
      not S._agent_dispatch(_win, NODES, {"cmd": "step", "years": 1}).get("ok", True), None)
