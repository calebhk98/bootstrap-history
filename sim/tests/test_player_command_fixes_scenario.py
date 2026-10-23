"""Scenario: player command fixes on a running game. Quoting changes nothing and `quote manumit` answers (the other targets'
quotes against their charges are test_quote_matches_charge_scenario), the rush preview starts nothing and lists exactly the ids
the real rush then starts, and a school is founded by every spelling. The parser, sort and dispatch-table rules are in
test_player_command_fixes."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.render_typed import render_pretty
from sim.ui.proto.typed import parse_typed


def _run(sim_state, text):
    parsed, error = parse_typed(text)
    if error:
        return {"ok": False, "error": error}
    return S._agent_dispatch(sim_state, NODES, parsed)


def _ids(rows):
    return [row["id"] for row in rows]


# --- 147: quote works for the target the charge table leaves out, and changes nothing
rich = unopened_sim(capital=1_000_000)
reply = _run(rich, "quote manumit 1")
check("quote works for buy target manumit", reply.get("ok"), reply)
capital_before = rich.capital
_run(rich, "quote farm 20")
check("quote changes nothing", rich.capital == capital_before)

# --- 155: rush preview lists what rush would start
rush_game = unopened_sim(capital=20000.0)
preview = _run(rush_game, "rush preview limit:3")
check("rush preview limit starts nothing", not rush_game.active, rush_game.active)
bare = _run(rush_game, "rush preview")
check("bare rush preview lists what it would start and starts nothing",
      bare.get("preview") and bare.get("count_would_start", 0) > 0
      and "total_cost" in bare and not rush_game.active, bare)
plain = _run(rush_game, "rush")
check("unbounded rush still only previews and renders as one",
      plain.get("preview") and "RUSH PREVIEW" in render_pretty("rush", plain))  # presentation: the preview heading
real = _run(rush_game, "rush limit:3")
check("rush preview lists exactly the ids rush limit starts",
      _ids(preview["would_start"]) == _ids(real["started"]) and len(real["started"]) == 3,
      (preview, real))

# --- 156: buy school <trade> <n> works, as do `trade school` and `trade_school`
school_sim = rich
school_sim.trades_created.add("chemist")
school_sim.labour.market.press("chemist", 100)
for text in ("buy school chemist 1", "buy trade school chemist 1", "buy trade_school chemist 1"):
    reply = _run(school_sim, text)
    check("%r founds a school" % text, reply.get("ok") and reply["trade"] == "chemist", reply)
check("the help example for schools is the form that works",  # presentation: the help text carries the working example
      "buy school smith 2" in json.dumps(_run(rich, "help economy")))
