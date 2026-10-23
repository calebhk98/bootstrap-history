"""Complaints 429, 443, 444: trade facts, fatality risks and goods' service lives are read from data. Stub registries use
invented trade ids; the shipped trades and service-life files are read as data. That the port hands the economy the risk and
the lives is test_game_port_and_portfolio_smoke."""
QUICK_TOPIC = True

import json
import os

from .harness import *  # noqa: F401,F403

from sim.economy import labour
from sim.engine.catalog import Trade, _trade_fields, _trade_from
from sim.labour import trade_data

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "world")
trades_file = json.load(open(os.path.join(DATA, "trades.json")))["trades"]

# 429: the registry keeps every field, and labour reads them.
trade = _trade_from("wright", {"family": "craft", "literate": True, "tool_basket": ["timber"]}, "test")
check("the trade record keeps a field it does not name", trade.extra == {"literate": True, "tool_basket": ["timber"]}, trade.extra)
check("an override sees the extra fields flat", _trade_fields(trade)["literate"] is True and "extra" not in _trade_fields(trade))
registry = {"wright": {"literate": True, "taught_from": "weaver", "tool_basket": ["timber", "iron"], "staff_resource": "crew"},
            "plain": {}}
check("a mod's trade can say it is literate", trade_data.literate_trades(registry, ["wright", "plain", "absent"]) == {"wright"})
check("a mod's trade names its teacher", trade_data.taught_from(registry, "wright") == "weaver")
check("a trade naming none is taught from the default", trade_data.taught_from(registry, "plain") == trade_data.taught_from({}, "x"))
check("a mod's trade names its tools", trade_data.tool_basket(registry, "wright") == ("timber", "iron")
      and trade_data.tool_basket(registry, "plain") == ())
check("a staffing resource is filled by the trade that names it, else by the same name",
      trade_data.staff_resource_trade(registry, "crew") == "wright" and trade_data.staff_resource_trade(registry, "ghosts") == "ghosts")

check("the shipped data states which trades are literate", trade_data.literate_trades(trades_file, trades_file) >= {"scholar", "scribe"})
check("the shipped data states the scholars' staffing resource", trade_data.staff_resource_trade(trades_file, "scholars") == "scholar")

# 444: fatality risks are stated with a source and confidence.
for name, spec in sorted(trades_file.items()):
    risk = spec.get("fatality_risk_per_year")
    check("%s states a fatality risk in [0, 1) with its source and confidence" % name,
          isinstance(risk, (int, float)) and 0.0 <= risk < 1.0 and spec.get("fatality_source") and spec.get("fatality_confidence"), spec)
check("mining, seafaring and soldiering carry a risk",
      all(trades_file[name]["fatality_risk_per_year"] > 0.0 for name in ("miner", "sailor", "soldier")))
dangerous_ask = labour.reservation_wage(100.0, 2000.0, trades_file["miner"]["fatality_risk_per_year"], 20.0)
safe_ask = labour.reservation_wage(100.0, 2000.0, 0.0, 20.0)
check("a dangerous trade's offered wage exceeds a safe one with equal subsistence", dangerous_ask > safe_ask, (dangerous_ask, safe_ask))

# 443: service lives are in data.
lives = json.load(open(os.path.join(DATA, "service_lives.json")))["years"]
check("every service life has a positive span, source and confidence",
      all(entry["years"] > 0 and entry["source"] and entry["confidence"] for entry in lives.values()))
