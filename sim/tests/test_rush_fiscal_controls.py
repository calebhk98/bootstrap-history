"""rush_fiscal_controls: regression checks, run with `--only rush_fiscal_controls`."""
from .harness import *  # noqa: F401,F403
from sim.engine.purchase_rule import purchase_budget as _purchase_budget
from sim.engine.state import serialize_state

_START_CAPITAL = 20000.0


def _rush(sim_state, **options):
    return S._agent_dispatch(sim_state, NODES, dict({"cmd": "rush"}, **options))


def _annual_draw(sim_state, node_id):
    return sim_state.project_cost(node_id) / max(1.0, NODES[node_id]["yrs"])


def _snapshot(sim_state):
    return (sorted(sim_state.active), sim_state.capital, len(sim_state.log))


# --- a total cost cap is never exceeded
capped = sim(capital=_START_CAPITAL)
_cap_costs = {node_id: capped.project_cost(node_id) for node_id in capped.order
              if capped.can_start(node_id)}
_total_cap = 1000.0
_result = _rush(capped, limit=50, max_total_cost=_total_cap)
_spent = sum(_cap_costs[row["id"]] for row in _result["started"])
check("rush max_total_cost starts something", _result["count_started"] > 0, _result)
check("rush max_total_cost never commits more than the cap",
      _spent <= _total_cap + 1e-6, (_spent, _total_cap))
check("rush max_total_cost explains what the cap skipped",
      any("max_total_cost" in row.get("why", "") for row in _result["not_started"]),
      _result["not_started"][:3])

# --- an annual draw cap is never exceeded
drawn = sim(capital=_START_CAPITAL)
_draw_cap = 300.0
_result = _rush(drawn, limit=50, max_annual_draw=_draw_cap)
_draw = sum(_annual_draw(drawn, row["id"]) for row in _result["started"])
check("rush max_annual_draw starts something", _result["count_started"] > 0, _result)
check("rush max_annual_draw never commits a bigger yearly draw than the cap",
      _draw <= _draw_cap + 1e-6, (_draw, _draw_cap))

# --- a cash reserve is left uncommitted
reserved = sim(capital=_START_CAPITAL)
_reserve = _purchase_budget(reserved) - 800.0
_result = _rush(reserved, limit=50, reserve_cash=_reserve)
_spent = sum(row["cost"] for row in _result["started"])
check("rush reserve_cash keeps the reserve out of the purchase budget",
      _spent <= 800.0 + 1e-6, _spent)

# --- preview changes no state and matches the real run
previewed = sim(capital=_START_CAPITAL)
_before = _snapshot(previewed)
_preview = _rush(previewed, limit=50, max_total_cost=1000.0, preview=True)
check("rush preview changes no state", _snapshot(previewed) == _before,
      (_before, _snapshot(previewed)))
check("rush preview says nothing was changed",
      _preview.get("preview") is True and _preview.get("nothing_changed") is True, _preview)
check("rush preview reports totals",
      _preview.get("total_cost") is not None and _preview.get("total_annual_draw") is not None
      and _preview["count_would_start"] == len(_preview["would_start"]), _preview)
_real = _rush(sim(capital=_START_CAPITAL), limit=50, max_total_cost=1000.0)
check("rush preview lists exactly what the real run starts",
      [row["id"] for row in _preview["would_start"]] == [row["id"] for row in _real["started"]],
      (_preview["would_start"][:3], _real["started"][:3]))

# --- bad option values are refused, not ignored
for _option in ("max_total_cost", "max_annual_draw", "reserve_cash"):
    refused = sim(capital=_START_CAPITAL)
    _result = _rush(refused, limit=3, **{_option: "lots"})
    check("rush refuses a non-numeric %s and starts nothing" % _option,
          _result.get("ok") is False and not refused.active, _result)
_result = _rush(sim(capital=_START_CAPITAL), limit=3, max_total_cost=-5)
check("rush refuses a negative cap", _result.get("ok") is False, _result)

# --- with no options, behaviour is unchanged
plain = sim(capital=_START_CAPITAL)
_result = _rush(plain, limit=5)
check("plain rush limit still starts exactly that many",
      _result["count_started"] == 5 and "preview" not in _result, _result)
check("plain rush is deterministic",
      [row["id"] for row in _rush(sim(capital=_START_CAPITAL), limit=5)["started"]]
      == [row["id"] for row in _result["started"]])
_unbounded = _rush(sim(capital=_START_CAPITAL))
check("unbounded rush with no options still only previews",
      _unbounded.get("preview") is True and _unbounded.get("nothing_changed") is True)

# --- typed spellings
_parsed, _error = _PT("rush limit:5 max_total_cost:20000 max_annual_draw:5,000 reserve_cash:10000 preview")
check("typed rush parses every fiscal option",
      _error is None and _parsed.get("max_total_cost") == 20000
      and _parsed.get("max_annual_draw") == 5000 and _parsed.get("reserve_cash") == 10000
      and _parsed.get("preview") is True and _parsed.get("limit") == 5, (_parsed, _error))
_parsed, _error = _PT("rush max_total_cost:abc")
check("typed rush refuses an unparseable cap", _parsed is None and _error, (_parsed, _error))
_parsed, _error = _PT("start all max_total_cost:500")
check("'start all' is the rush alias and keeps its options",
      _error is None and _parsed.get("cmd") == "rush" and _parsed.get("max_total_cost") == 500,
      (_parsed, _error))
_parsed, _error = _PT("start scientific_method")
check("'start <id>' is unchanged", (_parsed or {}).get("cmd") == "start", (_parsed, _error))

# --- preview and a real run agree near the credit margin
for _margin_capital in (150.0, 400.0, 900.0, 2500.0):
    _preview_ids = [row["id"] for row in
                    _rush(sim(capital=_margin_capital), limit=50, preview=True)["would_start"]]
    _real_ids = [row["id"] for row in _rush(sim(capital=_margin_capital), limit=50)["started"]]
    check("rush preview matches the real run at capital %d" % _margin_capital,
          _preview_ids == _real_ids and len(_real_ids) > 0, (_preview_ids, _real_ids))
_margin_sim = sim(capital=400.0)
check("start_refusal is None for a startable, affordable project and changes nothing",
      _margin_sim.start_refusal("units_standards") is None and not _margin_sim.active)
check("start_refusal counts extra_owed against the credit ceiling",
      "you already owe" in (_margin_sim.start_refusal("units_standards", extra_owed=1e9) or ""))

# --- preview rolls back everything, including the priority order and the saved state
_roll = sim(capital=400.0)
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
