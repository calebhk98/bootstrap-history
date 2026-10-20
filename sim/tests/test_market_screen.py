"""market_screen: the `market` command's registration, typed parse and rendering (Complaint 640: a reply built here, no game;
the command against a whole game is test_market_screen_scenario)."""
from .harness import check
from sim.ui.proto import command_registry as _registry
from sim.ui.proto.render_typed import render_pretty as _render_pretty
from sim.ui.proto.typed import parse_typed as _parse_typed

QUICK_TOPIC = True

check("market is a registered command with a help page",
      _registry.resolve("market") is not None
      and _registry.page("market")["usage"], _registry.resolve("market"))
check("typed 'market offset 10 limit 5' parses",
      _parse_typed("market offset 10 limit 5")[0] == {"cmd": "market", "offset": 10, "limit": 5},
      _parse_typed("market offset 10 limit 5"))

_row = {"material": "steel_plate_kg", "buy_per_tonne": 100.0, "sell_per_tonne": 80.0, "market_available_tonnes_per_year": 5.0,
        "own_supply": False, "price_basis": "solved"}
_reply = {"ok": True, "materials": {"rows": [_row], "total": 1}, "wages": [{"trade": "smith", "a_year_of_one": 500.0, "available_here": True, "you_employ": 0}]}
_text = _render_pretty("market", _reply)
# presentation: the screen's section headings
check("the rendered screen has its two sections", all(word in _text for word in ("MATERIAL", "WAGES")), _text[:400])
# presentation: the note on a gated price
check("a price at a technique the society lacks says so",
      "priced at a technique you do not have" in _render_pretty(
          "market", {"ok": True, "materials": {"rows": [dict(_row, price_basis="gated")], "total": 1}, "wages": []}),
      None)
check("a price at a technique the society holds carries no such note",
      "priced at a technique you do not have" not in _text, None)
