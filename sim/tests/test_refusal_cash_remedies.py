"""An unaffordable purchase's refusal lists the commands that raise cash, with the amounts those commands themselves
charge or pay. The finance module's `cash_remedies` runs over the views of its owners written out as plain figures (stock, concerns,
mines and staff); `purchase_remedies_text` and `purchase_refusal` run over the lines it gives. What a sale pays is
`GoodsMarket.sell` in test_quote_equals_charge_stock."""
from types import SimpleNamespace

from .harness import check

from sim.finance import remedy_rules
from sim.living_stock.api import stock_rates
from sim.refusal import facts_of
from sim.tests import finance_host

QUICK_TOPIC = True

BREEDING = sorted(stock_rates())[0]
MONEY_TEXT = lambda amount, grouped=False, short=False: "{:,.0f}".format(amount)


def module(stock=None, upkeep=None, mines=None, employees=None, wages=None, granted=(), cash=-6000.0):
    """The finance module over a stand-in game that holds stock, concerns, mines and staff."""
    stock = {} if stock is None else stock
    upkeep = {} if upkeep is None else upkeep
    mines = {} if mines is None else mines
    wages = {} if wages is None else wages
    held = set(upkeep)
    built = finance_host.build(
        acting_balance=cash, money_text=MONEY_TEXT, operating=set(upkeep), techniques_held=lambda: held,
        techniques_granted=lambda: set(granted), held_goods=lambda: list(stock), goods_stock=stock,
        sale_quote=lambda material, tonnes: (material, tonnes, 30.0 * tonnes if tonnes > 0 else 0.0),
        venture_real_upkeep=lambda node_id: upkeep[node_id], mine_capacity=lambda: dict(mines),
        mine_workings=lambda: [{"material": material, "cost": cost} for material, costs in mines.items() for cost in costs],
        mine_working_cost=lambda working: working["cost"], staff=lambda: {"employees": employees or {}},
        labour_market=SimpleNamespace(quote_annual=lambda trade: wages[trade]))
    built.spending_power = lambda kind: 100.0
    built.credit_limit = lambda revenue=None, upkeep=None, capital=None: 5000.0
    return built


# --- each remedy quotes the amount its own command uses
stocked = module(stock={"iron": 40.0})
lines = stocked.cash_remedies()
check("selling stock is offered at what the market quote pays for all of it (40 tonnes at 30 is 1,200)",
      len(lines) == 1 and lines[0].startswith("sell iron 40.0") and "1,200" in lines[0], lines)
check("breeding stock is not offered for sale", module(stock={BREEDING: 5000.0, "iron": 40.0}).cash_remedies() == lines)
check("stock that brings nothing is not offered", module(stock={"iron": 0.0}).cash_remedies() == [])

mothball = module(upkeep={"loom": 700.0}).cash_remedies()
check("a running concern is offered for mothballing at the upkeep it stops",
      len(mothball) == 1 and mothball[0].startswith("mothball loom") and "700" in mothball[0], mothball)
check("a concern whose upkeep is half a coin or less is not offered", module(upkeep={"loom": 0.4}).cash_remedies() == [])
check("a concern the society already had is not offered", module(upkeep={"loom": 700.0}, granted=("loom",)).cash_remedies() == [])

closing = module(mines={"copper": [300.0, 150.0]}).cash_remedies()
check("a mine is offered for closing at the sum of its workings' costs",
      len(closing) == 1 and closing[0].startswith("close copper") and "450" in closing[0], closing)

firing = module(employees={"smith": 2}, wages={"smith": 90.0}).cash_remedies()
check("a trade with staff is offered for firing at the wage it stops",
      len(firing) == 1 and firing[0].startswith("fire smith") and "90" in firing[0], firing)
check("a trade with nobody hired is not offered", module(employees={"smith": 0}, wages={"smith": 90.0}).cash_remedies() == [])

# --- order and limit
ordered = module(upkeep={"concern_%d" % index: 100.0 + index for index in range(10)}, stock={"iron": 40.0}).cash_remedies()
check("at most six remedies are listed, the largest amount first",
      len(ordered) == remedy_rules.REMEDY_LIMIT == 6 and ordered[0].startswith("sell iron")
      and ordered[1].startswith("mothball concern_9"), ordered)
check("equal amounts keep the order they were found in",
      remedy_rules.top_remedies([(5.0, "a"), (9.0, "b"), (5.0, "c")], 2) == ["b", "a"])

# --- the text a refusal carries
check("no remedy line when nothing is on offer", module().purchase_remedies_text() == "")
# presentation: the sentence joining the remedies names each command
check("remedies join into one sentence naming each command",
      "sell iron" in stocked.purchase_remedies_text() and "To raise cash" in stocked.purchase_remedies_text())
refusal = stocked.purchase_refusal("a loom", 900.0)
check("the refusal states its cost, the budget and the shortfall as values",
      refusal.cause == "cash_short" and facts_of(refusal)["cost"] == 900.0 and facts_of(refusal)["budget"] == 100.0
      and facts_of(refusal)["short"] == 800.0, facts_of(refusal))
# presentation: the refusal lists the remedy in its text
check("...and carries the remedy line", "sell iron" in str(refusal), str(refusal))

# --- each rule on written-out figures
check("a sale that brings nothing gives no remedy", remedy_rules.sale_remedy("iron", 3.0, 0.0, MONEY_TEXT) is None)
check("a sale gives its amount and a line", remedy_rules.sale_remedy("iron", 3.0, 90.0, MONEY_TEXT)[0] == 90.0)
check("a saving at the floor gives no remedy", remedy_rules.mothball_remedy("loom", remedy_rules.SMALLEST_SAVING, MONEY_TEXT) is None)
check("a mine's saving above the floor gives its amount", remedy_rules.mine_closing_remedy("copper", 450.0, MONEY_TEXT)[0] == 450.0)
check("nobody hired gives no firing", remedy_rules.firing_remedy("smith", 0, 90.0, MONEY_TEXT) is None)
