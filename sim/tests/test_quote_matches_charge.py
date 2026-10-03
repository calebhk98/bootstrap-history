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
from sim.ui.proto.buy_targets import BUY_TARGETS as _BUY_TARGETS  # noqa: E402
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


# ---- the same comparison through the cash ledger: open, research, project bills, the hire wage ------
def _ledger_outflow(game, *causes):
    """Money the ledger shows paid out under these causes, the open period and the closed ones."""
    household = game.state.household
    totals = [household.cash_flow] + [period["causes"] for period in household.cash_periods]
    return -sum(totals_by_cause.get(cause, 0.0) for totals_by_cause in totals for cause in causes)


def _ledger_game():
    game = _fresh()
    game.end_year = game.cfg["start_year"] + game.cfg["horizon_years"]
    game.LIVING_COST_STATUS_PER_CAPITAL = 0.0   # status spending follows cash, which a charge changes
    return game


def _first_node(test):
    probe = _ledger_game()
    for node_id in ORDER:
        if node_id not in probe.done and probe.can_start(node_id) and test(NODES[node_id]):
            return node_id
    return None


def _openable_game(node_id):
    game = _ledger_game()
    game.state.projects.done.add(node_id)
    game._done_changed()
    return game


def _first_openable():
    for node_id in ORDER:
        probe = _ledger_game()
        if node_id in probe.done or not probe.is_venture(node_id):
            continue
        reply = S._agent_dispatch(_openable_game(node_id), NODES,
                                  {"cmd": "quote", "what": "open", "id": node_id})
        if reply.get("ok") and not reply.get("staff_short"):
            return node_id
    return None


def _run_project(node_id):
    game = _ledger_game()
    quoted = S._agent_dispatch(game, NODES, {"cmd": "why", "id": node_id})["cost"]["total"]
    reply = S._agent_dispatch(game, NODES, {"cmd": "start", "id": node_id})
    for _year in range(8):
        if node_id in game.done:
            break
        S._agent_dispatch(game, NODES, {"cmd": "step", "years": 1})
    return game, quoted, reply


_open_id = _first_openable()
check("a venture exists to open in the table", _open_id is not None)
if _open_id:
    _open_quote = S._agent_dispatch(_openable_game(_open_id), NODES,
                                    {"cmd": "quote", "what": "open", "id": _open_id})
    _opener = _openable_game(_open_id)
    _open_reply = S._agent_dispatch(_opener, NODES, {"cmd": "open", "id": _open_id})
    check("open: the action succeeds", _open_reply.get("ok"), _open_reply)
    check("open: the ledger shows exactly what was quoted",
          abs(_ledger_outflow(_opener, "opening a venture") - _open_quote["paid_now"]) <= 0.051,
          (_ledger_outflow(_opener, "opening a venture"), _open_quote["paid_now"]))

for _label, _test in (
        ("research", lambda node: not node["rev"] and not node["mat"]),
        ("project", lambda node: node["rev"] > 0 and node["mat"])):
    _node_id = _first_node(_test)
    check("%s: a node exists to start in the table" % _label, _node_id is not None)
    if not _node_id:
        continue
    _game, _quoted, _started = _run_project(_node_id)
    check("%s: the project starts and finishes" % _label,
          _started.get("ok") and _node_id in _game.done, _started)
    _paid = _ledger_outflow(_game, "project payments", "materials bought for projects")
    check("%s: the ledger shows exactly the bill that `why` quoted" % _label,
          abs(_paid - _quoted) <= 0.11, (_paid, _quoted))

# The hire's yearly wage: the fee plus what the first year's payroll adds beyond it is the quoted wage.
_hired, _twin = _ledger_game(), _ledger_game()
_hire_quote = S._agent_dispatch(_ledger_game(), NODES, {"cmd": "quote", "what": "hire", "trade": "smith", "n": 1})
S._agent_dispatch(_hired, NODES, {"cmd": "hire", "trade": "smith", "n": 1})
for _game in (_hired, _twin):
    S._agent_dispatch(_game, NODES, {"cmd": "step", "years": 1})
_hire_charged = (_ledger_outflow(_hired, "hiring fee and first year's wages")
                 + _ledger_outflow(_hired, "living costs") - _ledger_outflow(_twin, "living costs"))
check("hire wage: the first year's charge through the ledger is the quoted yearly wage",
      abs(_hire_charged - _hire_quote["from_next_year_per_year"]) <= 0.11,
      (_hire_charged, _hire_quote["from_next_year_per_year"]))

# Living stock: the ledger "stock bought abroad" outflow is exactly the quoted cost.
_stock_args = {"what": "living_stock", "material": "ramie_stock_kg", "n": 100}
_stock_quote = S._agent_dispatch(_ledger_game(), NODES, dict(_stock_args, cmd="quote"))
_stocked = _ledger_game()
_stock_reply = S._agent_dispatch(_stocked, NODES, dict(_stock_args, cmd="buy"))
check("living stock: the ledger shows exactly what was quoted",
      _stock_reply.get("ok") and abs(_ledger_outflow(_stocked, "stock bought abroad")
                                     - _stock_quote["to_buy_it"]) <= 0.051,
      (_ledger_outflow(_stocked, "stock bought abroad"), _stock_quote.get("to_buy_it")))
