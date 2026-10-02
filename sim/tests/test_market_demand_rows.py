"""market_demand_rows: regression checks, run with `--only market_demand_rows`."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto.render_typed import render_pretty as _render_pretty

_empty = sim()
_reply = S._agent_dispatch(_empty, NODES, {"cmd": "market"})
_rows = _reply.get("demand", [])
check("market lists every goods category before anything is built",
      sorted(row["category"] for row in _rows) == sorted(_empty.GOODS_CATEGORIES), _rows[:2])
check("...each with the share a first concern would earn, matching the engine",
      all(abs(row["new_concern_earns_share"]
              - _empty.goods_category_factor_with_entrants(row["category"], 1)) < 1e-3
          for row in _rows), _rows[:2])
check("...and no price move while nothing of yours sells there",
      all(row["concerns_of_yours"] == 0 and row["sale_price_vs_opening"] is None for row in _rows), _rows[:2])

_loom_sim, _loom_ids = _mk_loom_sim(2, 60)
_after = S._agent_dispatch(_loom_sim, NODES, {"cmd": "market"})
_textiles = next(row for row in _after["demand"] if row["category"] == "textiles")
_ratios = _loom_sim._goods_category_ratios("textiles")
check("once you sell there the row counts your concerns and shows the sale price against opening day",
      _textiles["concerns_of_yours"] == len(_loom_ids)
      and abs(_textiles["sale_price_vs_opening"] - _ratios[0]) < 1e-3
      and abs(_textiles["quantity_vs_opening"] - _ratios[1]) < 1e-3, _textiles)
check("a further concern would earn less than the first did",
      _textiles["new_concern_earns_share"] < 1.0, _textiles)
check("the text screen prints the demand section",
      "DEMAND" in _render_pretty("market", _after) and "textiles" in _render_pretty("market", _after))
