"""player_command_fixes: sort words, quote for every buy target, rush preview, buy school."""
from .harness import *
from sim.engine.proto import buy_targets
from sim.engine.proto.dispatch_money import _BUY_HANDLERS
from sim.engine.proto.render_typed import render_pretty
from sim.engine.proto.typed import parse_typed


def _run(sim_state, text):
    parsed, error = parse_typed(text)
    if error:
        return {"ok": False, "error": error}
    return S._agent_dispatch(sim_state, NODES, parsed)


def _ids(rows):
    return [row["id"] for row in rows]


# --- 146: `available sort earns` sorts, and an unknown sort key is refused
rich = sim(capital=1_000_000)
spaced = _run(rich, "available sort earns limit 200")
coloned = _run(rich, "available sort:earns limit 200")
check("sort with a space sorts by earnings like the colon form",
      spaced.get("sorted_by") == "earns" and _ids(spaced["available"]) == _ids(coloned["available"]),
      spaced.get("sorted_by"))
check("sort earns reverse puts the biggest earner first",
      _run(rich, "available sort earns reverse limit 5")["available"][0]["earns_per_year"]
      >= _run(rich, "available sort earns limit 5")["available"][0]["earns_per_year"])
refused = _run(rich, "available sort bogus limit 5")
check("an unknown sort key is refused, naming the valid ones",
      not refused["ok"] and "earns" in refused["error"], refused)

# --- 147: quote covers every buy target
for target in buy_targets.target_names():
    check("buy handler exists for target %s" % target, target in _BUY_HANDLERS)
quotable = {"forest": "quote forest 10", "nitre": "quote nitre 100", "farm": "quote farm 20",
            "housing": "quote housing 5", "school": "quote school smith 2",
            "material": "quote material iron 10", "mine": "quote mine coal 100",
            "slaves": "quote slaves 2", "manumit": "quote manumit 1"}
check("the quote test names every buy target", set(quotable) == set(buy_targets.target_names()))
for target, text in quotable.items():
    reply = _run(sim(capital=1_000_000), text)
    check("quote works for buy target %s" % target, reply.get("ok"), (text, reply))
farm_reply = _run(rich, "quote farm 20")
check("quote farm prices what buy farm charges",
      abs(farm_reply["to_buy_it"] - 20 * rich.FARM_COST_PER_HA * rich.price_index) < 0.1, farm_reply)
material_reply = _run(rich, "quote material iron 10")
check("quote material gives the current market price per tonne",
      material_reply["per_tonne"] > 0, material_reply)
capital_before = rich.capital
_run(rich, "quote farm 20")
check("quote changes nothing", rich.capital == capital_before)

# --- 155: rush preview lists what rush would start
preview = _run(sim(capital=20000.0), "rush preview limit:3")
real = _run(sim(capital=20000.0), "rush limit:3")
check("rush preview lists exactly the ids rush limit starts",
      _ids(preview["would_start"]) == _ids(real["started"]) and len(real["started"]) == 3,
      (preview, real))
bare_sim = sim(capital=20000.0)
bare = _run(bare_sim, "rush preview")
check("bare rush preview lists what it would start and starts nothing",
      bare.get("preview") and bare.get("count_would_start", 0) > 0
      and "total_cost" in bare and not bare_sim.active, bare)
check("bare rush preview renders as a preview, not as '0 started'",
      "RUSH PREVIEW" in render_pretty("rush", bare), render_pretty("rush", bare)[:80])
plain = _run(sim(capital=20000.0), "rush")
check("unbounded rush still only previews and renders as one",
      plain.get("preview") and "RUSH PREVIEW" in render_pretty("rush", plain))

# --- 156: buy school <trade> <n> works, as do `trade school` and `trade_school`
school_sim = sim(capital=1_000_000)
school_sim.trades_created.add("chemist")
school_sim._add_labour_pressure("chemist", 100)
for text in ("buy school chemist 1", "buy trade school chemist 1", "buy trade_school chemist 1"):
    reply = _run(school_sim, text)
    check("%r founds a school" % text, reply.get("ok") and reply["trade"] == "chemist", reply)
check("the help example for schools is the form that works",
      "buy school smith 2" in json.dumps(_run(sim(), "help economy")))
