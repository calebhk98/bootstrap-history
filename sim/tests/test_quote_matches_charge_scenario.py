"""SMOKE: every command with a quote is charged what it quoted (the stock bought from a partner is test_quote_equals_charge_stock).

The subject is the agreement of two paths through the dispatcher (a quote handler and the action's handler), so it is
read on running games, not on one function. Two scenarios: a parametrised table (each row is a quote command, the command
that spends, and the reply key holding the quoted price; the rows share one game and run in turn), and the same comparison
through the cash ledger (open, research and project bills, the hire wage). The price
rules each quote reads are in the tests of the module that prices it (test_purchase_reads_economy_price, test_physical_money_constants).
"""
from .harness import *  # noqa: F401,F403

_CAPITAL = 4000000.0


def _fresh():
    return unopened_sim(capital=_CAPITAL)


_TABLE_GAME = _fresh()


def _bounty_node():
    probe = _TABLE_GAME
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
    _game = _TABLE_GAME
    _quote = S._agent_dispatch(_game, NODES, dict(_quote_args, cmd="quote"))
    _before = _game.capital
    _reply = S._agent_dispatch(_game, NODES, dict(_action_args, cmd=_action))
    _charged = _before - _game.capital
    check("%s: the quote answers with a price" % _name,
          _quote.get("ok") and _key in _quote, _quote)
    check("%s: the action succeeds" % _name, _reply.get("ok"), _reply)
    check("%s: charged exactly what was quoted" % _name,
          abs(_charged - _quote.get(_key, -1.0)) <= 0.051,
          (_charged, _quote.get(_key)))

# Every buy target is in the table (manumit costs nothing and is quoted as free; the stock bought from a partner is in test_quote_equals_charge_stock).
from sim.ui.proto.buy_targets import BUY_TARGETS as _BUY_TARGETS  # noqa: E402
_covered = {row[3].get("what") for row in _ROWS if row[2] == "buy"}
_uncovered = [target for target in _BUY_TARGETS if target not in _covered | {"manumit", "living_stock", "smuggled_stock"}]
check("every buy target has a row in the quote-equals-charge table",
      not _uncovered, _uncovered)

# Farm and school take their price from one engine function, quote and action alike.
_priced = _TABLE_GAME
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
    game = unopened_sim(capital=_CAPITAL, surveyed=())
    game.end_year = game.cfg["start_year"] + game.cfg["horizon_years"]
    game.LIVING_COST_STATUS_PER_CAPITAL = 0.0   # status spending follows cash, which a charge changes
    game.HOUSEHOLD_DEPENDANT_PEOPLE = 0.0   # a hire's takings carry some dependants, which would offset part of its wage
    return game


_PROBE = _ledger_game()


def _first_node(test):
    probe = _PROBE
    for node_id in ORDER:
        if node_id not in probe.done and probe.can_start(node_id) and test(NODES[node_id]):
            return node_id
    return None


def _first_openable():
    """A venture whose opening quote needs no extra staff, found on one probe game."""
    probe = _PROBE
    for node_id in ORDER:
        if node_id in probe.done or not probe.is_venture(node_id):
            continue
        probe.state.projects.done.add(node_id)
        probe._done_changed()
        reply = S._agent_dispatch(probe, NODES, {"cmd": "quote", "what": "open", "id": node_id})
        probe.state.projects.done.discard(node_id)
        probe._done_changed()
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
        # the year's project payments and materials (its seat phases, in order); the ledger bill is all this reads
        game._run_seat_prelude()
        game.assembly.phase_handler("start_projects")(game.state.acting_seat)
        game.assembly.phase_handler("materials")(game.state.acting_seat)
        game._step_material_shortage_notes()
        game._run_seat_work()
    return game, quoted, reply


_open_id = _first_openable()
_PROJECT_TESTS = (
    ("research", lambda node: not node["rev"] and not node["mat"]),
    ("project", lambda node: node["rev"] > 0 and node["mat"]))
_PROJECT_NODES = [_first_node(_test) for _label, _test in _PROJECT_TESTS]
check("a venture exists to open in the table", _open_id is not None)
if _open_id:
    _opener = _PROBE
    _opener.state.projects.done.add(_open_id)
    _opener._done_changed()
    _open_quote = S._agent_dispatch(_opener, NODES, {"cmd": "quote", "what": "open", "id": _open_id})
    _open_reply = S._agent_dispatch(_opener, NODES, {"cmd": "open", "id": _open_id})
    check("open: the action succeeds", _open_reply.get("ok"), _open_reply)
    check("open: the ledger shows exactly what was quoted",
          abs(_ledger_outflow(_opener, "opening a venture") - _open_quote["paid_now"]) <= 0.051,
          (_ledger_outflow(_opener, "opening a venture"), _open_quote["paid_now"]))

for (_label, _test), _node_id in zip(_PROJECT_TESTS, _PROJECT_NODES):
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
_hire_quote = S._agent_dispatch(_hired, NODES, {"cmd": "quote", "what": "hire", "trade": "smith", "n": 1})
S._agent_dispatch(_hired, NODES, {"cmd": "hire", "trade": "smith", "n": 1})
for _game in (_hired, _twin):
    _game._step_money_seat()   # the year's wages and living costs, which is where the hire's charge lands
_hire_charged = (_ledger_outflow(_hired, "hiring fee and first year's wages")
                 + _ledger_outflow(_hired, "living costs") - _ledger_outflow(_twin, "living costs"))
check("hire wage: the first year's charge through the ledger is the quoted yearly wage",
      abs(_hire_charged - _hire_quote["from_next_year_per_year"]) <= 0.11,
      (_hire_charged, _hire_quote["from_next_year_per_year"]))
