"""SCENARIO: the `rush` command's fiscal caps and preview on a real game: a total cap holds, a preview changes nothing, lists
what the real run starts (also near the credit margin) and rolls the order and the saved state back. The caps' rules are in
test_rush_fiscal_controls."""
from .harness import *  # noqa: F401,F403
from sim.engine.state import serialize_state

_START_CAPITAL = 20000.0


def _rush(sim_state, **options):
    return S._agent_dispatch(sim_state, NODES, dict({"cmd": "rush"}, **options))


def _snapshot(sim_state):
    return (sorted(sim_state.active), sim_state.capital, len(sim_state.log))


# --- a total cost cap is never exceeded
capped = unopened_sim(capital=_START_CAPITAL)
_cap_costs = {node_id: capped.project_cost(node_id) for node_id in capped.order
              if capped.can_start(node_id)}
_total_cap = 1000.0
_result = _rush(capped, limit=50, max_total_cost=_total_cap)
_rush_capped = _result
_spent = sum(_cap_costs[row["id"]] for row in _result["started"])
check("rush max_total_cost starts something", _result["count_started"] > 0, _result)
check("rush max_total_cost never commits more than the cap",
      _spent <= _total_cap + 1e-6, (_spent, _total_cap))
check("rush max_total_cost explains what the cap skipped",
      any("max_total_cost" in row.get("why", "") for row in _result["not_started"]),
      _result["not_started"][:3])

# --- preview changes no state and matches the real run
previewed = unopened_sim(capital=_START_CAPITAL)
_before = _snapshot(previewed)
_preview = _rush(previewed, limit=50, max_total_cost=1000.0, preview=True)
check("rush preview changes no state", _snapshot(previewed) == _before,
      (_before, _snapshot(previewed)))
check("rush preview says nothing was changed",
      _preview.get("preview") is True and _preview.get("nothing_changed") is True, _preview)
check("rush preview reports totals",
      _preview.get("total_cost") is not None and _preview.get("total_annual_draw") is not None
      and _preview["count_would_start"] == len(_preview["would_start"]), _preview)
_capped_run = _rush_capped
check("rush preview lists exactly what the real run starts",
      [row["id"] for row in _preview["would_start"]] == [row["id"] for row in _capped_run["started"]],
      (_preview["would_start"][:3], _capped_run["started"][:3]))

# --- with no options, behaviour is unchanged
plain = unopened_sim(capital=_START_CAPITAL)
_result = _rush(plain, limit=5)
check("plain rush limit still starts exactly that many",
      _result["count_started"] == 5 and "preview" not in _result, _result)
_unbounded = _rush(previewed)
check("unbounded rush with no options still only previews",
      _unbounded.get("preview") is True and _unbounded.get("nothing_changed") is True)

# --- preview and a real run agree near the credit margin
for _margin_capital in (150.0, 400.0, 900.0, 2500.0):
    _margin_sim = unopened_sim(capital=_margin_capital)
    _preview_ids = [row["id"] for row in _rush(_margin_sim, limit=50, preview=True)["would_start"]]
    _real_ids = [row["id"] for row in _rush(_margin_sim, limit=50)["started"]]
    check("rush preview matches the real run at capital %d" % _margin_capital,
          _preview_ids == _real_ids and len(_real_ids) > 0, (_preview_ids, _real_ids))

# --- preview rolls back everything, including the priority order and the saved state
_roll = previewed
_order_before = list(_roll.order)


def _sections(sim_state):
    """The serialised game sections, without the metadata a save stamps on."""
    blob = serialize_state(sim_state.state)
    return json.dumps({key: value for key, value in blob.items() if not key.startswith("_")},
                      sort_keys=True, default=str)


_blob_before = _sections(_roll)
_rush(_roll, limit=50, preview=True)
check("rush preview leaves the priority order untouched", _roll.order == _order_before)
check("rush preview leaves the serialised game state identical",
      _sections(_roll) == _blob_before)
