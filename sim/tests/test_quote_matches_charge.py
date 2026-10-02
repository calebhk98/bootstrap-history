"""quote_matches_charge: every command with a quote is charged what it quoted.

One parametrised table: each row is a quote command, the command that spends,
and the reply key holding the quoted price. Both run on identical games.
"""
from .harness import *  # noqa: F401,F403

_CAPITAL = 400000.0


def _fresh():
    return sim(capital=_CAPITAL)


def _bounty_node():
    probe = _fresh()
    for node_id in sorted(NODES):
        if node_id not in probe.done and probe.bounty_eligible(node_id):
            return node_id
    return None


_ROWS = [
    ("forest", {"what": "forest", "n": 20}, "buy", {"what": "forest", "n": 20}, "to_buy_it"),
    ("nitre", {"what": "nitre", "n": 3000}, "buy", {"what": "nitre", "n": 3000}, "to_lay_it"),
    ("farm", {"what": "farm", "n": 3}, "buy", {"what": "farm", "n": 3}, "to_buy_it"),
    ("housing", {"what": "housing", "n": 2}, "buy", {"what": "housing", "n": 2}, "to_buy_it"),
    ("school", {"what": "school", "trade": "smith", "n": 2},
     "buy", {"what": "school", "trade": "smith", "n": 2}, "to_buy_it"),
    ("material", {"what": "material", "material": "iron", "n": 0.5},
     "buy", {"what": "material", "material": "iron", "n": 0.5}, "to_buy_it"),
    ("mine", {"what": "mine", "material": "coal", "n": 50},
     "buy", {"what": "mine", "material": "coal", "n": 50}, "to_sink_it"),
    ("living stock", {"what": "living_stock", "material": "ramie_stock_kg", "n": 100},
     "buy", {"what": "living_stock", "material": "ramie_stock_kg", "n": 100}, "to_buy_it"),
    ("slaves", {"what": "slaves", "n": 3}, "buy", {"what": "slaves", "n": 3}, "to_buy_them"),
    ("hire", {"what": "hire", "trade": "smith", "n": 1},
     "hire", {"trade": "smith", "n": 1}, "paid_now"),
    ("commission", {"what": "commission", "trade": "smith", "hours": 100},
     "commission", {"trade": "smith", "hours": 100}, "paid_now"),
    ("train", {"what": "train", "trade": "smith", "n": 1},
     "train", {"trade": "smith", "n": 1}, "paid_now"),
]
_bounty_id = _bounty_node()
if _bounty_id:
    _ROWS.append(("bounty", {"what": "bounty", "id": _bounty_id},
                  "bounty", {"id": _bounty_id}, "paid_now"))

for _name, _quote_args, _action, _action_args, _key in _ROWS:
    _quote = S._agent_dispatch(_fresh(), NODES, dict(_quote_args, cmd="quote"))
    _game = _fresh()
    _before = _game.capital
    _reply = S._agent_dispatch(_game, NODES, dict(_action_args, cmd=_action))
    _charged = _before - _game.capital
    check("%s: the quote answers with a price" % _name,
          _quote.get("ok") and _key in _quote, _quote)
    check("%s: the action succeeds" % _name, _reply.get("ok"), _reply)
    check("%s: charged exactly what was quoted" % _name,
          abs(_charged - _quote.get(_key, -1.0)) <= 0.051,
          (_charged, _quote.get(_key)))

# Every buy target is in the table (manumit costs nothing and is quoted as free).
from sim.engine.proto.buy_targets import BUY_TARGETS as _BUY_TARGETS  # noqa: E402
_covered = {row[3].get("what") for row in _ROWS if row[2] == "buy"}
_uncovered = [target for target in _BUY_TARGETS if target not in _covered | {"manumit"}]
check("every buy target has a row in the quote-equals-charge table",
      not _uncovered, _uncovered)

# Farm and school take their price from one engine function, quote and action alike.
_priced = _fresh()
_farm_quote = S._agent_dispatch(_priced, NODES, {"cmd": "quote", "what": "farm", "n": 1})
_school_quote = S._agent_dispatch(
    _priced, NODES, {"cmd": "quote", "what": "school", "trade": "smith"})
check("farm price per hectare is one engine function the quote reads",
      hasattr(_priced, "farm_price_per_hectare")
      and abs(_farm_quote["per_unit"] - _priced.farm_price_per_hectare()) < 0.006)
check("trade-school price per seat is one engine function the quote reads",
      hasattr(_priced, "trade_school_price_per_seat")
      and abs(_school_quote["per_unit"] - _priced.trade_school_price_per_seat()) < 0.006)
