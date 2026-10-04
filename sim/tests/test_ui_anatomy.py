"""ui_anatomy: the `anatomy` command (Complaint 69), run with `--only ui_anatomy`."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto import command_registry
from sim.ui.proto.render_typed import render_pretty as _render_pretty
from sim.ui.proto.typed import parse_typed as _parse_typed

# renderer on hand-written replies (no game)
_literacy_reply = {
    "ok": True, "metric": "literacy_general", "description": "literacy reaches 20%",
    "current": 0.05, "target": {"op": ">=", "value": 0.2, "gap": 0.15, "met": False},
    "rows": [{"label": "ceiling", "value": 0.4, "unit": "fraction", "note": "most it can reach"},
             {"label": "schools running", "value": 0, "unit": "schools", "note": ""}],
    "generic": False}
_text = _render_pretty("anatomy", _literacy_reply)
check("the screen shows target, current value and the gap",
      "5.00%" in _text and "20.00%" in _text and "15.00 points to go" in _text, _text)
check("the screen lists each row", "ceiling" in _text and "40.00%" in _text and "schools running" in _text, _text)
_generic = {"ok": True, "metric": "mod_metric", "description": None, "current": None,
            "target": {"op": ">=", "value": 0.5, "gap": None, "met": None}, "rows": [],
            "generic": True, "note": "no breakdown is available for this metric yet"}
_text = _render_pretty("anatomy", _generic)
check("a generic reply renders with its no-breakdown sentence and an unknown value",
      "no breakdown" in _text and "unknown" in _text, _text)
check("a research-goal reply renders its pointer",
      "leverage" in _render_pretty("anatomy", {"ok": True, "research_goal": True, "note": "see path and leverage"}))

# command registry: no alias clashes, typed parser keeps the metric
_entry = command_registry.COMMANDS["anatomy"]
_clash = [word for word in ("anatomy",) + tuple(_entry["aliases"])
          if sum(1 for name, other in command_registry.COMMANDS.items()
                 if word == name or word in other["aliases"]) != 1]
check("anatomy and its aliases clash with no other command", not _clash, _clash)
check("the typed line carries the named metric",
      _parse_typed("anatomy literacy_general")[0] == {"cmd": "anatomy", "what": "literacy_general"})

# handler on one real game
game = sim()
_measured = sorted(node_id for node_id, node in NODES.items()
                   if (node.get("win_condition") or {}).get("metric") == "literacy_general")
_other_metric = sorted(node_id for node_id, node in NODES.items()
                       if (node.get("win_condition") or {}).get("metric") == "epidemic_relief")


def _ask(**fields):
    return S._agent_dispatch(game, NODES, dict(cmd="anatomy", **fields))


game.goal = _measured[0]
reply = _ask()
check("a literacy goal gives an anatomy with a target, current value and gap",
      reply.get("ok") and reply["metric"] == "literacy_general" and reply["target"]["gap"] is not None
      and reply["current"] is not None and not reply["generic"], reply)
_labels = [row["label"] for row in reply["rows"]]
check("the literacy rows cover ceiling, schooling flow and farm share",
      "ceiling" in _labels and "schooling flow" in _labels and "farm share of working hours" in _labels, _labels)
check("the literacy rows are the education screen's numbers",
      reply["current"] == S._agent_dispatch(game, NODES, {"cmd": "education"})["literacy"]["general"], reply["current"])
check("the named form for elite literacy answers with its own rows",
      _ask(what="literacy_elite")["metric"] == "literacy_elite")
if _other_metric:
    relief = _ask(what="epidemic_relief")
    check("epidemic relief lists its total", relief.get("ok") and relief["rows"][-1]["label"] == "total relief", relief)
check("an unknown metric is refused with a pointer to the list",
      _ask(what="no_such_metric")["ok"] is False)
game.nodes["mod_probe_goal"] = {"name": "Probe", "win_condition": {"metric": "mod_probe", "op": ">=", "value": 0.5}}
_generic_reply = _ask(what="mod_probe")
check("a metric with no entry reports target and the missing breakdown",
      _generic_reply.get("generic") is True and _generic_reply["target"]["value"] == 0.5
      and "no breakdown" in _generic_reply["note"], _generic_reply)
check("the listing names the metrics", "literacy_general" in _ask(what="list")["metrics"])

game.goal = GOAL
check("a research goal is pointed to path and leverage",
      "leverage" in _ask().get("note", ""), _ask())

game.goal = _measured[0]
game.fog = True
_fogged = _ask()
check("under fog, a goal that is not in view is refused politely",
      _fogged.get("ok") is False and "not yet in view" in _fogged["error"], _fogged)
check("under fog, a named metric is still answered", _ask(what="literacy_elite").get("ok") is True)
game.fog = False
