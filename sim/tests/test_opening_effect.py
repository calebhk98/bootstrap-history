"""opening_effect: regression checks, run with `--only opening_effect`."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto.render_typed import render_pretty as _render_pretty

_loom_sim, _loom_ids = _mk_loom_sim(2, 60)
_candidate = next(node_id for node_id, node in sorted(NODES.items())
                  if node.get("cat") == "textiles" and node.get("rev") and node_id not in _loom_ids)
_running = [node_id for node_id in _loom_ids if node_id in _loom_sim.state.projects.operating]
_why = S._agent_dispatch(_loom_sim, NODES, {"cmd": "why", "id": _candidate})
_effect = _why.get("opening_effect")
check("why on an unopened goods concern gives an opening effect", _effect is not None, list(_why)[:40])
_factor_now = _loom_sim.goods_category_factor("textiles")
_factor_new = _loom_sim.goods_category_factor_with_entrants("textiles", 1)
_expected_existing = sum(NODES[node_id]["rev"] * _loom_sim.venture_ramp(node_id) * _loom_sim.price_index
                         * (_factor_new - _factor_now) for node_id in _running)
check("existing concerns' change is their quoted figure times the move in the category factor",
      _effect and abs(_effect["existing_concerns_change_per_year"] - _expected_existing) < 0.06,
      (_effect, _expected_existing))
check("the new concern's own earnings and the net change are stated",
      _effect and abs(_effect["net_change_per_year"] - (
          _effect["new_concern_earns_per_year"] + _effect["existing_concerns_change_per_year"])) < 0.06
      and _effect["new_concern_earns_per_year"] > 0, _effect)
check("existing concerns lose revenue, and the screen says so",
      _effect and _effect["existing_concerns_change_per_year"] < 0
      and "existing" in _render_pretty("why", _why).lower(), _effect)
_none = S._agent_dispatch(sim(), NODES, {"cmd": "why", "id": _candidate}).get("opening_effect")
check("with nothing of yours in the category, existing concerns lose nothing",
      _none is not None and _none["existing_concerns_change_per_year"] == 0, _none)

_full = S._agent_dispatch(_loom_sim, NODES, {"cmd": "economy", "full": True})
_plain = S._agent_dispatch(_loom_sim, NODES, {"cmd": "economy"})
check("economy full carries the goods demand table that plain economy does not",
      "goods_demand" in _full and "goods_demand" not in _plain, list(_full))
