"""A screen's question about the material throttle does not change the game, and the reading a step takes is the one the
question gave: `throttle_quote` answers from the books without banking, noting or counting anything; `apply_throttle` banks
what the year leaves, notes the market's draw, counts the shortage once and replays the reading while nothing has changed.
Called on the materials module over plain views; the same question asked of a running game is in
test_peek_resource_throttle_scenario."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.ledger.api import BankStock, rules as ledger_rules
from sim.markets.api import NoteDraw, ResetDraws
from sim.materials.api import ApplyThrottle
from sim.tests import materials_stand_in, module_harness

FURNACE = {"mat": {"iron_ore_kg": 10000.0}, "build_yrs": 1, "up": 0, "pre": []}


def furnace_module():
    """A furnace under construction wants 10 tonnes a year of iron; the seat holds 5 and the market offers 2."""
    stock = ledger_rules.StockLedger({"iron": 5.0})

    def bank(command):
        for commodity, tonnes in command.tonnes:
            stock[commodity] = tonnes
        stock.writes += 1

    module = materials_stand_in.build(
        tree_nodes={"furnace": FURNACE}, projects_record=materials_stand_in.projects(active={"furnace": {}}),
        active_projects_version=1, techniques_version=1, held_goods=stock, goods_stock_opening={"iron": 5.0},
        answers={BankStock: bank})
    module.market_tonnes = lambda commodity: 2.0
    return module, stock


module, stock = furnace_module()
pace, binding = module.throttle_quote()
check("the quote answers what the pace is and which pool binds it", (pace, binding) == (0.7, "iron"), (pace, binding))
check("...and the same for the project that draws the pool", module.throttle_quote("furnace") == (0.7, "iron"))
check("it sent nothing", module_harness.sent(module) == [], module_harness.sent(module))
check("the stock is as it was", dict(stock) == {"iron": 5.0} and stock.writes == 0, dict(stock))
check("the pace, the binding and the shortage count are as they were",
      (module.seat.throttle, module.seat.binding, dict(module.seat.shortages)) == (1.0, None, {}))

taken = module.apply_throttle(ApplyThrottle())
check("the reading a step takes is the one the question gave", taken == pace, taken)
sent = module_harness.sent(module)
check("it banks what the year leaves, resets the draws and notes the market's",
      [type(command) for command in sent] == [BankStock, ResetDraws, NoteDraw]
      and sent[0].tonnes == (("iron", 0.0),) and (sent[2].commodity, sent[2].tonnes) == ("iron", 2.0), sent)
check("it counts the shortage once and keeps the pace and the binding",
      (module.seat.throttle, module.seat.binding, dict(module.seat.shortages)) == (0.7, "iron", {"iron": 1}))
module.apply_throttle(ApplyThrottle())
check("a repeat with nothing changed replays the reading: nothing more is sent or counted",
      len(module_harness.sent(module)) == 3 and dict(module.seat.shortages) == {"iron": 1})
check("the question after the step gets the same answer", module.throttle_quote() == (0.7, "iron"))
stock.writes += 1       # a trade changed the books
module.apply_throttle(ApplyThrottle())
check("a change to the books is read again", dict(module.seat.shortages) == {"iron": 2}, dict(module.seat.shortages))
check("a project's pace is the reading's when it draws the pool that binds",
      module.apply_throttle(ApplyThrottle("furnace")) == 0.7)
