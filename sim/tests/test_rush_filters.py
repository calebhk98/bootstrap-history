"""rush_filters: regression checks, run with `--only rush_filters`."""
from .harness import *  # noqa: F401,F403

_CAPITAL = 20000.0


def _rush(sim_state, **options):
    return S._agent_dispatch(sim_state, NODES, dict({"cmd": "rush"}, **options))


probe = sim(capital=_CAPITAL)
_startable = [node_id for node_id in probe.order if probe.can_start(node_id)]
_category = next(NODES[node_id]["cat"] for node_id in _startable)

# subject filter: only that category is previewed and started
_preview = _rush(sim(capital=_CAPITAL), category=_category, preview=True, limit=200)
check("rush category filter keeps only that subject",
      _preview["count_would_start"] > 0
      and all(NODES[row["id"]]["cat"] == _category for row in _preview["would_start"]), _preview)
check("rush category filter names what it filtered by",
      _preview.get("filters", {}).get("category") == _category, _preview.get("filters"))

# per-project cost ceiling
_ceiling = 500.0
_by_cost = sim(capital=_CAPITAL)
_costs = {node_id: _by_cost.project_cost(node_id) for node_id in _startable}
_result = _rush(_by_cost, max_cost=_ceiling, limit=200)
check("rush max_cost starts something", _result["count_started"] > 0, _result)
check("rush max_cost starts nothing dearer than the ceiling",
      all(_costs[row["id"]] <= _ceiling + 1e-6 for row in _result["started"]), _result["started"][:3])

# founder-hours ceiling
_by_hours = sim(capital=_CAPITAL)
_result = _rush(_by_hours, max_hours=0, limit=200)
check("rush max_hours:0 starts only projects needing no founder hours",
      all(NODES[row["id"]]["ph"] <= 0 for row in _result["started"]), _result["started"][:3])

# preview reports founder hours
_preview = _rush(sim(capital=_CAPITAL), preview=True, limit=5)
_expect = sum(NODES[row["id"]]["ph"] for row in _preview["would_start"])
check("rush preview totals the founder hours",
      abs(_preview.get("total_founder_hours", -1) - _expect) < 1e-6, _preview.get("total_founder_hours"))

# bad value
check("rush rejects a non-numeric max_cost", _rush(sim(capital=_CAPITAL), max_cost="lots")["ok"] is False)

# explicit id list
_ids_sim = sim(capital=_CAPITAL)
_pick = [node_id for node_id in _ids_sim.order if _ids_sim.can_start(node_id)][:2]
_result = _rush(_ids_sim, ids=",".join(_pick), limit=10)
# what is affordable shifts with data and credit rules, so the invariant is: nothing
# outside the named list starts, and every named one is accounted for (started or refused with a reason)
_started_ids = {row["id"] for row in _result["started"]}
_refused_ids = {row["id"] for row in _result["not_started"]}
check("rush ids starts only the named projects and accounts for each",
      _started_ids and _started_ids <= set(_pick) and _started_ids | _refused_ids == set(_pick)
      and not _started_ids & _refused_ids, (_result["started"], _result["not_started"]))
_unknown = _rush(sim(capital=_CAPITAL), ids="no_such_node", preview=True)
check("rush ids rejects an unknown id", _unknown["ok"] is False and "no_such_node" in _unknown["error"], _unknown)

# preview shows bottlenecks and risk
_preview = _rush(sim(capital=_CAPITAL), preview=True, limit=30)
check("rush preview carries risk exposure",
      "risk_exposure" in _preview and "expected_failures" in _preview["risk_exposure"], _preview.get("risk_exposure"))
_expected = sum(NODES[row["id"]]["risk"] for row in _preview["would_start"])
check("...as the sum of the started projects' own risk",
      abs(_preview["risk_exposure"]["expected_failures"] - _expected) < 0.01, _preview["risk_exposure"])
check("rush preview lists trade bottlenecks as a list of trades with demand and supply",
      isinstance(_preview.get("trade_bottlenecks"), list)
      and all({"trade", "demand_hours_this_year", "supply_hours_this_year"} <= set(row)
              for row in _preview["trade_bottlenecks"]), _preview.get("trade_bottlenecks"))
