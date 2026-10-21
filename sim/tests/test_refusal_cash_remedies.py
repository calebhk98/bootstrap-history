"""An unaffordable purchase's refusal lists the commands that raise cash, with the amounts those commands themselves
charge or pay. `cash_remedies`, `remedies_text` and `refusal_text` run on a stand-in actor holding stock, concerns,
mines and staff (no game). The refusal reached through `start` is test_refusal_cash_remedies_scenario."""
from types import SimpleNamespace

from .harness import check

from sim.engine import cash_remedies, purchase_rule
from sim.engine.living_stock_yearly import stock_rates
from sim.refusal import facts_of

QUICK_TOPIC = True

BREEDING = sorted(stock_rates())[0]


def _actor(stock=None, upkeep=None, mines=None, employees=None, wages=None, budget=100.0, cash=-6000.0):
    stock = {} if stock is None else stock
    upkeep = {} if upkeep is None else upkeep
    mines = {} if mines is None else mines
    wages = {} if wages is None else wages
    projects = SimpleNamespace(operating=set(upkeep), done=set(upkeep), granted=set())
    return SimpleNamespace(
        SPENDING_DRAW_SHARE_ORDINARY=0.5, capital=cash, civ={"id": "stub"},
        _stock_key=lambda material: material, _material_stock=lambda: stock,
        material_stock_t=lambda material: stock[material],
        goods_market=SimpleNamespace(quote_sell=lambda material, tonnes: (material, tonnes, 30.0 * tonnes)),
        state=SimpleNamespace(projects=projects, household=SimpleNamespace(employees=employees or {})),
        venture_real_upkeep=lambda node_id: upkeep[node_id],
        mine_capacity=mines, _workings_of=lambda material: mines[material],
        mine_operating_cost_for=lambda working: working,
        labour=SimpleNamespace(market=SimpleNamespace(quote_annual=lambda trade: wages[trade])),
        spending_power=lambda kind: budget, credit_limit=lambda: 5000.0)


# --- each remedy quotes the amount its own command uses
stocked = _actor(stock={"iron": 40.0})
lines = cash_remedies.cash_remedies(stocked)
check("selling stock is offered at what the market quote pays for all of it (40 tonnes at 30 is 1,200)",
      len(lines) == 1 and lines[0].startswith("sell iron 40.0") and "1,200" in lines[0], lines)
check("breeding stock is not offered for sale",
      cash_remedies.cash_remedies(_actor(stock={BREEDING: 5000.0, "iron": 40.0})) == lines)
check("stock that brings nothing is not offered", cash_remedies.cash_remedies(_actor(stock={"iron": 0.0})) == [])

mothball = cash_remedies.cash_remedies(_actor(upkeep={"loom": 700.0}))
check("a running concern is offered for mothballing at the upkeep it stops",
      len(mothball) == 1 and mothball[0].startswith("mothball loom") and "700" in mothball[0], mothball)
check("a concern whose upkeep is half a coin or less is not offered",
      cash_remedies.cash_remedies(_actor(upkeep={"loom": 0.4})) == [])
granted = _actor(upkeep={"loom": 700.0})
granted.state.projects.granted.add("loom")
check("a concern the society already had is not offered", cash_remedies.cash_remedies(granted) == [])

closing = cash_remedies.cash_remedies(_actor(mines={"copper": [300.0, 150.0]}))
check("a mine is offered for closing at the sum of its workings' costs",
      len(closing) == 1 and closing[0].startswith("close copper") and "450" in closing[0], closing)

firing = cash_remedies.cash_remedies(_actor(employees={"smith": 2}, wages={"smith": 90.0}))
check("a trade with staff is offered for firing at the wage it stops",
      len(firing) == 1 and firing[0].startswith("fire smith") and "90" in firing[0], firing)
check("a trade with nobody hired is not offered",
      cash_remedies.cash_remedies(_actor(employees={"smith": 0}, wages={"smith": 90.0})) == [])

# --- order and limit
many = _actor(upkeep={"concern_%d" % index: 100.0 + index for index in range(10)}, stock={"iron": 40.0})
ordered = cash_remedies.cash_remedies(many)
check("at most six remedies are listed, the largest amount first",
      len(ordered) == cash_remedies.REMEDY_LIMIT == 6 and ordered[0].startswith("sell iron")
      and ordered[1].startswith("mothball concern_9"), ordered)

# --- the text a refusal carries
check("no remedy line when nothing is on offer", purchase_rule.remedies_text(_actor()) == "")
# presentation: the sentence joining the remedies names each command
check("remedies join into one sentence naming each command",
      "sell iron" in purchase_rule.remedies_text(stocked) and "To raise cash" in purchase_rule.remedies_text(stocked))
refusal = purchase_rule.refusal_text(stocked, "a loom", 900.0)
check("the refusal states its cost, the budget and the shortfall as values",
      refusal.cause == "cash_short" and facts_of(refusal)["cost"] == 900.0 and facts_of(refusal)["budget"] == 100.0
      and facts_of(refusal)["short"] == 800.0, facts_of(refusal))
# presentation: the refusal lists the remedy in its text
check("...and carries the remedy line", "sell iron" in str(refusal), str(refusal))
