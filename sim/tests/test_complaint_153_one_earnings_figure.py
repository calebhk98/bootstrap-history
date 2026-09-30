"""Complaint 153: every screen that quotes a concern's earnings or upkeep
uses Sim.venture_real_earnings / venture_real_upkeep, and `ventures` shows
the market-saturation line the `money` screen promises."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto.render_typed import render_pretty
from sim.engine.proto.typed import parse_typed


def _run(sim_state, text):
    parsed, error = parse_typed(text)
    if error:
        return {"ok": False, "error": error}
    return S._agent_dispatch(sim_state, NODES, parsed)


def _close(left, right):
    return left is not None and right is not None and abs(left - right) < 0.06


# A saturated market (three looms), a trade-route bonus running, and a price
# level and output factor that make the tree's raw figure differ from the real one.
crowded, loom_ids = _mk_loom_sim(3, 60)
if "exp_trade_route_extend" in NODES:
    run_it(crowded, "exp_trade_route_extend")
crowded.price_index = 1.7
crowded.output_factor = 0.9
loom = loom_ids[0]
real_earnings = crowded.venture_real_earnings(loom)
real_upkeep = crowded.venture_real_upkeep(loom)
check("set-up: saturation and prices make the real figure differ from the tree's",
      abs(real_earnings - NODES[loom]["rev"]) > 1.0 and abs(real_upkeep - NODES[loom]["up"]) > 1.0,
      (real_earnings, real_upkeep, NODES[loom]["rev"], NODES[loom]["up"]))

ventures_out = _run(crowded, "ventures")
ventures_row = next(row for row in ventures_out["running"] if row["id"] == loom)
money_out = _run(crowded, "money")
why_out = _run(crowded, "why " + loom)
check("ventures earns/costs match venture_real_earnings/upkeep",
      _close(ventures_row["earns_a_year"], real_earnings) and _close(ventures_row["costs_a_year"], real_upkeep),
      (ventures_row, real_earnings, real_upkeep))
check("money's per-concern row matches the same earnings",
      _close(money_out["where_the_money_comes_from"].get(loom), real_earnings),
      (money_out["where_the_money_comes_from"].get(loom), real_earnings))
check("why shows the same earnings for a running concern",
      _close(why_out.get("revenue"), real_earnings), (why_out.get("revenue"), real_earnings))
check("why shows the same upkeep for a running concern",
      _close(why_out.get("upkeep"), real_upkeep), (why_out.get("upkeep"), real_upkeep))

# a concern not yet built: `available` and `why` agree with the same methods
fresh = sim(capital=1_000_000)
fresh.price_index = 1.7
fresh.output_factor = 0.9
listed = _run(fresh, "available sort earns reverse limit 5")["available"]
candidate = next(row for row in listed if NODES[row["id"]]["rev"] > 0)
candidate_id = candidate["id"]
check("available earns/costs match the same methods",
      _close(candidate["earns_per_year"], fresh.venture_real_earnings(candidate_id))
      and _close(candidate["costs_per_year_after"], fresh.venture_real_upkeep(candidate_id)),
      (candidate, fresh.venture_real_earnings(candidate_id)))
candidate_why = _run(fresh, "why " + candidate_id)
check("why agrees with available for a concern not yet built",
      _close(candidate_why.get("revenue"), candidate["earns_per_year"])
      and _close(candidate_why.get("upkeep"), candidate["costs_per_year_after"]),
      (candidate_why.get("revenue"), candidate["earns_per_year"]))
check("available net_per_year is real earnings less real upkeep",
      _close(candidate.get("net_per_year"),
             fresh.venture_real_earnings(candidate_id) - fresh.venture_real_upkeep(candidate_id)),
      (candidate.get("net_per_year"), candidate))

# the saturation line on the ventures screen a player reads
screen = render_pretty("ventures", ventures_out)
check("the ventures screen shows the saturation line under a saturated row",
      "saturation" in screen, screen[:600])
