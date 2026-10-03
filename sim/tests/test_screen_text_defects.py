"""Screen text that read wrongly or said too little: Complaints/195 (score change line), 204 (sack chance wording), 280 (option ids)."""
from .harness import *  # noqa: F401,F403
from sim.ui import cli
from sim.ui.proto.render_screens_status import render_risk, render_score


# --- 204: the sack chance line prints the figure with nothing built, not a dash
mexica = sim(civ="mexica_1500", capital=1e6)
mexica_risk = render_risk(S._agent_dispatch(mexica, NODES, {"cmd": "risk"}))
invasion_line = next(line for line in mexica_risk.splitlines() if line.lstrip().startswith("sack chance:"))
check("risk says what a sacking chance is with nothing built, in a figure",
      "(- with nothing built)" not in invasion_line and "90% with nothing built" in invasion_line,
      invasion_line)

# --- 199: a second `score` says what moved since the first
score_sim = sim()
first = S._agent_dispatch(score_sim, NODES, {"cmd": "score"})
check("the first score has no change line to show",
      all("since_last_score" not in component for component in first["components"].values()))
score_sim.reputation = score_sim.reputation + 20
second = S._agent_dispatch(score_sim, NODES, {"cmd": "score"})
standing_change = second["components"]["standing"].get("since_last_score")
check("a second score reports the standing change since the first",
      standing_change is not None and standing_change["normalized_change"] > 0, standing_change)
check("the score screen prints the change line",
      "since your last score" in render_score(second), render_score(second)[-600:])
third = S._agent_dispatch(score_sim, NODES, {"cmd": "score"})
check("an unchanged score reports no movement",
      (third["components"]["standing"].get("since_last_score") or {}).get("normalized_change") == 0)

# --- 280: no option names the tail of a node id under another prefix without the validator saying so
check("the control option of load dispatch names the real telephone node",
      "telephone_exchange" not in {option for group in NODES["el2_load_dispatch_and_scheduling"].get("req_any") or []
                                   for option in group.get("options") or {}})
loose_warning = [warning for warning in cli._validate_nodes(*[
    NODES, set(cli.load()[4]), cli.load()[3]])[1] if "purchasable commodities" in warning]
check("validate says how many commodity-style options are the tail of one node id",
      loose_warning and "also the tail of one node id" in loose_warning[0], loose_warning)
