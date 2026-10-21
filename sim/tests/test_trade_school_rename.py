"""Test that 'school' has been renamed to 'trade_school'. Complaint 640: the spellings are looked up in the buy table, the
command is called on a stand-in game that records the school it is asked for, and the founding rule is called on a
stand-in labour world; no game is built."""
QUICK_TOPIC = True

import types

from .harness import *  # noqa: F401,F403
from sim.labour.labour_population import PopulationMixin
from sim.ui.proto.buy_targets import canonical_target
from sim.ui.proto.dispatch_money import _BUY_HANDLERS, _buy_school, _cmd_buy
from sim.ui.proto.typed import parse_typed

check("buy trade_school parses correctly",
      parse_typed("buy trade_school smith 2")[0]
      == {"cmd": "buy", "what": "trade_school", "material": "smith", "n": 2})

check("help text mentions trade school",  # presentation: the help wording
      "trade school" in str(parse_typed("help economy")).lower()
      or parse_typed("help buy") is not None)

check("every spelling of the target reaches the one school handler",
      {canonical_target(word) for word in ("school", "trade_school", "trade school", "Trade_School")} == {"school"}
      and _BUY_HANDLERS["school"] is _buy_school)


class SchoolLabour:
    """Records the school the command founds."""

    def __init__(self):
        self.founded = []

    def found_trade_school(self, trade, seats):
        self.founded.append((trade, seats))
        return True, None

    def market_supply(self, trade):
        return 1234.5


school_game = types.SimpleNamespace(labour=SchoolLabour(), trade_schools={"chemist": 1.0}, capital=500.0, civ={})
for word in ("trade_school", "school"):
    school_game.labour.founded.clear()
    reply = _cmd_buy(school_game, {}, {"cmd": "buy", "what": word, "trade": "chemist", "n": 1}, None)
    check("buy %s founds a school for the trade named" % word,
          reply["ok"] and school_game.labour.founded == [("chemist", 1.0)] and reply["trade_school_seats"] == 1.0
          and reply["trade"] == "chemist", reply)

# ---- founding a school: the trade must exist, and the seats must be paid for ------------------------------
SEAT_PRICE = 40.0


def labour_world(capital, trade_known=True, schools=None):
    household = types.SimpleNamespace(capital=capital, trade_schools=schools, trades_created=set())
    paid = []
    world = types.SimpleNamespace(
        wages={"chemist": 1.0} if trade_known else {}, trades_absent=set(), state=types.SimpleNamespace(household=household),
        trade_school_price_per_seat=lambda: SEAT_PRICE, EDGE_WORKERS="edge:workers",
        pay_edge=lambda edge, cost, purpose: paid.append((edge, cost, purpose)))
    return types.SimpleNamespace(_world=world, trade_available=lambda trade: PopulationMixin.trade_available(
        types.SimpleNamespace(_world=world), trade)), household, paid


labour, household, paid = labour_world(1000.0)
founded, why = PopulationMixin.found_trade_school(labour, "chemist", 2)
check("a school founded for a known trade adds its seats and pays for them",
      founded and why is None and household.trade_schools == {"chemist": 2.0} and paid == [("edge:workers", 2 * SEAT_PRICE, "trade schools")],
      (household.trade_schools, paid))
PopulationMixin.found_trade_school(labour, "chemist", 1)
check("further seats add to the school", household.trade_schools == {"chemist": 3.0}, household.trade_schools)
check("the trade then counts as one the household has", "chemist" in household.trades_created)
labour, household, paid = labour_world(10.0)
founded, why = PopulationMixin.found_trade_school(labour, "chemist", 2)
check("seats the household cannot pay for are refused and change nothing", not founded and not paid and not household.trade_schools, (why, paid))
labour, household, paid = labour_world(1000.0, trade_known=False)
founded, why = PopulationMixin.found_trade_school(labour, "chemist", 2)
check("a trade that does not exist cannot be taught by a school", not founded and not paid, why)
