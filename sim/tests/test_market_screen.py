"""market_screen: regression checks, run individually with `--only market_screen`."""
from .harness import *  # noqa: F401,F403
from sim.ui.market_report import priceable_materials
from sim.ui.proto import command_registry as _registry
from sim.ui.proto.render_typed import render_pretty as _render_pretty
from sim.ui.proto.typed import parse_typed as _parse_typed

# `market`: goods saturation, every priceable material, every trade's wage,
# on one screen, from numbers the game already computes.
check("market is a registered command with a help page",
      _registry.resolve("market") is not None
      and _registry.page("market")["usage"], _registry.resolve("market"))

_empty = sim()
_reply_empty = S._agent_dispatch(_empty, NODES, {"cmd": "market"})
check("market answers on a fresh game with no concerns: ok, no saturation rows",
      _reply_empty.get("ok") is True and _reply_empty.get("goods") == [],
      _reply_empty.get("goods"))

_loom_sim, _loom_ids = _mk_loom_sim(2, 60)
_reply = S._agent_dispatch(_loom_sim, NODES, {"cmd": "market"})
_textiles = next((row for row in _reply.get("goods", []) if row["category"] == "textiles"), None)
check("market lists the category the concerns sell into, with the concerns that compete",
      _textiles is not None and sorted(_textiles["concerns"]) == sorted(_loom_ids),
      _reply.get("goods"))
check("...and the share of the quoted figure actually being earned, below 1 when saturated",
      _textiles and 0.0 < _textiles["share_of_quoted_earned"] < 1.0
      and _textiles["earned_per_year"] < _textiles["quoted_per_year"],
      _textiles)
check("...matching goods_market_factor's own numbers",
      _textiles and abs(_textiles["earned_per_year"] - sum(
          NODES[node_id]["rev"] * _loom_sim.venture_ramp(node_id) * _loom_sim.price_index
          * _loom_sim.goods_market_factor(node_id) for node_id in _loom_ids)) < 0.06,
      _textiles)

_materials = _reply.get("materials", {})
_rows = _materials.get("rows", [])
_priceable = priceable_materials(_loom_sim)
check("materials table covers every priceable material, not only tracked ones (paged)",
      _materials.get("total") == len(_priceable) and len(_priceable) > 100
      and 0 < len(_rows) < len(_priceable), (_materials.get("total"), len(_rows)))
check("each material row carries the quote's buy price and an own-supply flag",
      all("buy_per_tonne" in row and isinstance(row["own_supply"], bool) for row in _rows),
      _rows[:2])
_everything = S._agent_dispatch(_loom_sim, NODES, {"cmd": "market", "limit": 1000}).get("materials", {}).get("rows", [])
_bases = {row["material"]: row.get("price_basis") for row in _everything}
check("each material row says which technique its price is at, and the text names one the society lacks",
      set(_bases.values()) <= {"solved", "gated", "mature", None} and "gated" in _bases.values()
      and "priced at a technique you do not have" in _render_pretty(
          "market", {"ok": True, "goods": [], "materials": {"rows": [dict(_everything[0], price_basis="gated")], "total": 1},
                     "wages": []}),
      _bases.get("steel_plate_kg"))
_quote_ref = _loom_sim.material_trade_quote(_rows[0]["material"])
check("...and the price is the one `quote material` uses",
      abs(_rows[0]["buy_per_tonne"] - _quote_ref["buy_per_tonne"]) < 0.01, _rows[0])
_page2 = S._agent_dispatch(_loom_sim, NODES, {"cmd": "market", "offset": len(_rows), "limit": 5})
check("offset and limit page the materials table",
      [row["material"] for row in _page2["materials"]["rows"]]
      == list(_priceable)[len(_rows):len(_rows) + 5],
      _page2["materials"]["rows"])
_mine_sim = sim()
_mine_sim.state.economy.forest_ha = 10.0
_all = S._agent_dispatch(_mine_sim, NODES, {"cmd": "market", "limit": 1000})
_charcoal = next(row for row in _all["materials"]["rows"] if row["material"] == "charcoal_kg")
check("a material you produce is flagged as own supply",
      _charcoal["own_supply"] is True, _charcoal)

_wages = _reply.get("wages", [])
check("wages table has every trade, with the per-year wage `labour <trade>` reports",
      sorted(row["trade"] for row in _wages) == sorted(WAGES)
      and all(abs(row["a_year_of_one"] - S._agent_dispatch(
          _loom_sim, NODES, {"cmd": "labour", "trade": row["trade"]})["trade"]["a_year_of_one"]) < 1.0
          for row in _wages[:5]), _wages[:3])

check("typed 'market offset 10 limit 5' parses",
      _parse_typed("market offset 10 limit 5")[0] == {"cmd": "market", "offset": 10, "limit": 5},
      _parse_typed("market offset 10 limit 5"))
_text = _render_pretty("market", _reply)
check("the rendered screen has the three sections",
      all(word in _text for word in ("GOODS", "MATERIAL", "WAGES")), _text[:400])

# `why` on a concern names its goods category and the saturation there.
_why = S._agent_dispatch(_loom_sim, NODES, {"cmd": "why", "id": _loom_ids[0]})
_why_text = _render_pretty("why", _why)
check("why on a concern names its goods category and current saturation",
      "textiles" in _why_text.lower() and "market" in _why_text.lower()
      and _why.get("goods_market_line"), _why.get("goods_market_line"))
