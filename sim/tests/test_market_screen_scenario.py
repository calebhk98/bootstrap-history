"""market_screen scenario (Complaint 640 audit): the `market` command against a whole game. The command registration, the
typed parse and the rendering of a reply are rule tests in test_market_screen."""
from .harness import *  # noqa: F401,F403
from sim.ui.market_report import priceable_materials

# `market`: every priceable material, every trade's wage,
# on one screen, from numbers the game already computes.
_loom_sim, _loom_ids = _mk_loom_sim(2, 60)
_reply = S._agent_dispatch(_loom_sim, NODES, {"cmd": "market"})
check("market answers ok, with no founder-side goods rows", _reply.get("ok") is True and "goods" not in _reply
      and "demand" not in _reply, sorted(_reply))

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
check("each material row says which technique its price is at, and some are priced at one the society lacks",
      set(_bases.values()) <= {"solved", "gated", "imported", None} and "gated" in _bases.values(),
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
_mine_sim.state.holdings.forest_ha = 10.0
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
