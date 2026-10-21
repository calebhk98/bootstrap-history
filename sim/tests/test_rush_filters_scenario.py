"""SCENARIO: the `rush` command with filters on a real game: a subject, a cost ceiling and a list of ids start only what fits and
account for the rest, and a preview totals the founder hours. The filter rules are in test_rush_filters."""
from .harness import *  # noqa: F401,F403

_CAPITAL = 20000.0


def _rush(sim_state, **options):
    return S._agent_dispatch(sim_state, NODES, dict({"cmd": "rush"}, **options))


probe = unopened_sim(capital=_CAPITAL)
_startable = [node_id for node_id in probe.order if probe.can_start(node_id)]
_category = next(NODES[node_id]["cat"] for node_id in _startable)

_preview = _rush(unopened_sim(capital=_CAPITAL), category=_category, preview=True, limit=200)
check("rush category filter keeps only that subject",
      _preview["count_would_start"] > 0
      and all(NODES[row["id"]]["cat"] == _category for row in _preview["would_start"]), _preview)

_ceiling = 500.0
_by_cost = unopened_sim(capital=_CAPITAL)
_costs = {node_id: _by_cost.project_cost(node_id) for node_id in _startable}
_result = _rush(_by_cost, max_cost=_ceiling, limit=200)
check("rush max_cost starts something and nothing dearer than the ceiling",
      _result["count_started"] > 0 and all(_costs[row["id"]] <= _ceiling + 1e-6 for row in _result["started"]), _result["started"][:3])

_preview = _rush(unopened_sim(capital=_CAPITAL), preview=True, limit=5)
_expect = sum(NODES[row["id"]]["ph"] for row in _preview["would_start"])
check("rush preview totals the founder hours",
      abs(_preview.get("total_founder_hours", -1) - _expect) < 1e-6, _preview.get("total_founder_hours"))

_ids_sim = unopened_sim(capital=_CAPITAL)
_pick = [node_id for node_id in _ids_sim.order if _ids_sim.can_start(node_id)][:2]
_result = _rush(_ids_sim, ids=",".join(_pick), limit=10)
# what is affordable shifts with data and credit rules, so the invariant is: nothing outside the named list starts,
# and every named one is accounted for (started or refused with a reason)
_started_ids = {row["id"] for row in _result["started"]}
_refused_ids = {row["id"] for row in _result["not_started"]}
check("rush ids starts only the named projects and accounts for each",
      _started_ids and _started_ids <= set(_pick) and _started_ids | _refused_ids == set(_pick)
      and not _started_ids & _refused_ids, (_result["started"], _result["not_started"]))
