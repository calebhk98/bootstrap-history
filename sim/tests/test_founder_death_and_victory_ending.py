"""Complaints 224, 255, 256, 257, 259, 264: founder age and death text, deputies,
the ending after a dispersed corpus, achievements announced once, the civilisation
label after the start, and the victory screen with a finish-and-score command."""
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


# 255: the age is shown, with a range, and "ageing" is dropped after death
_alive = _new_sim()
_alive_out = S._agent_state(_alive, NODES)
_alive_text = _RSTATE(_alive_out)
check("a mortal founder's state carries the age as a number",
      _alive_out.get("founder_age") == _alive.cfg["founder_arrival_age"], _alive_out.get("founder_age"))
check("a mortal founder's state line shows the age",
      "aged about %d" % _alive.cfg["founder_arrival_age"] in _alive_text, _alive_text[:300])
_dead = _new_sim()
_die(_dead)
_dead_text = _RSTATE(S._agent_state(_dead, NODES))
check("after death the status line does not say ageing", "ageing" not in _dead_text, _dead_text[:300])
check("an immortal founder's state has no age line",
      "aged about" not in _RSTATE(S._agent_state(_new_sim(mortal=False), NODES)), None)

# 256: one rule for a deputy, and the notice names the hours
_fraction = _new_sim()
_fraction.directors_extra = 0.15
_fraction_log = " ".join(_die(_fraction))
check("the death notice does not deny deputies who carry hours",
      "no deputy" not in _fraction_log and "nobody to" not in _fraction_log, _fraction_log)
check("the death notice says how many hours the deputies carry",
      "%d hours" % round(0.15 * _fraction.cfg["director_hours_per_year"]) in _fraction_log, _fraction_log)
_none_log = " ".join(_die(_new_sim()))
check("with no deputies at all the notice says so", "no deputy" in _none_log, _none_log)
check("state names the deputies in words",
      "deputies" in _RSTATE(S._agent_state(_fraction, NODES)), None)

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
_sack = _new_sim()
_sack.done.add(_win_id)
_sack._done_changed()
check("the losable list excludes measured goal nodes", _win_id not in _sack.losable_node_ids(), None)

# 264: the running game names the civilisation by its short name
_pop = S._agent_dispatch(_new_sim(), NODES, {"cmd": "population"})
check("population does not say 'under Trajan'", "Trajan" not in _pop.get("civilisation", ""), _pop.get("civilisation"))
check("population still names the civilisation", bool(_pop.get("civilisation")), None)

# 224: victory screen, and finish-and-score under fog
_win = _new_sim(fog=True, mortal=False)
_real_step = _win.step


def _step_and_win():
    _real_step()
    _win.goal_year = _win.year


_win.step = _step_and_win
_win_out = S._agent_dispatch(_win, NODES, {"cmd": "step", "n": 1})
_victory = _win_out.get("victory") or {}
check("reaching the goal returns a victory block with date, years and how to score",
      _victory.get("year") == _win.year and "elapsed_years" in _victory
      and "finish" in (_victory.get("to_see_your_score") or ""), _victory)
check("the victory screen renders", "VICTORY" in _RSTATE(_win_out), None)
_before = S._agent_dispatch(_win, NODES, {"cmd": "score"})
check("under fog the total is withheld before finishing", _before.get("total") is None, _before.get("total"))
_finish = S._agent_dispatch(_win, NODES, {"cmd": "finish"})
check("finish ends the run and reveals the total",
      bool(_finish.get("ok")) and (_finish.get("score") or {}).get("total") is not None
      and bool(S._agent_end_reason(_win)), _finish.get("score"))
check("after finishing, commands that move the game on are refused",
      not S._agent_dispatch(_win, NODES, {"cmd": "step", "n": 1}).get("ok", True), None)
