"""Complaints 358 and 356: every employer asks the one labour market. The founder's household, a
firm, the state and an interest group are quoted the same rate for the same trade at the same moment;
the hire quote is what payroll then charges; and no module outside the labour market computes a wage."""
import ast
import os

from .harness import *  # noqa: F401,F403

from sim.engine.agents_port import SimWorld
from sim.ui.proto.quote_spending import _quote_hire
from .source_dirs import engine_side_dirs

TRADE = "artisan"


def stressed_game():
    """A game with a non-unit price level, a non-unit demographic wage index and a scarcity premium."""
    game = sim()
    game.price_index = 1.5
    game._wage_index_base = 1.3
    game.labour.market.press(TRADE, game.labour.market_supply(TRADE) * 0.8)
    game.labour.market.press("labourer", game.labour.market_supply("labourer") * 0.8)
    game.labour.market.press("scribe", game.labour.market_supply("scribe") * 0.8)
    return game


# ---- one rate for every kind of employer -----------------------------------------------------------
game = stressed_game()
market = game.labour.market
hours_per_year = game.HOURS_PER_PERSON_YEAR
check("the stressed market has a scarcity premium above one", market.price_factor(TRADE) > 1.05, market.price_factor(TRADE))
check("the stressed market has a price level above one", game.price_index > 1.4 and game.wage_index > 1.2)
game.state.household.employees = {TRADE: 1.0}
rate = market.quote(TRADE, 0.0)
founder_rate = game.labour.wage_bill() / hours_per_year
check("the founder's household is quoted the market rate", abs(founder_rate - rate) < 1e-9 * rate, (founder_rate, rate))

world = SimWorld(game)
check("an actor reaches the market through the world's one accessor", world.labour_market is market)
check("the state's budget pays the market rate",
      abs(world.pay_per_person_year(TRADE) - rate * hours_per_year) < 1e-9 * rate * hours_per_year,
      (world.pay_per_person_year(TRADE), rate * hours_per_year))

node_id = next(node_id for node_id in game.nodes if game.is_venture(node_id) and "artisan" in world.concern_staff(node_id))
expected_bill = world.span_factor(1.0) * sum(people * hours_per_year * market.quote(staffed_trade)
                                             for staffed_trade, people in world.concern_staff(node_id).items())
check("a firm's wage bill is staff times the market rate", abs(world.concern_wage_bill(node_id) - expected_bill) < 1e-6 * expected_bill,
      (world.concern_wage_bill(node_id), expected_bill))

labourer_year = market.quote("labourer") * hours_per_year
check("an interest group measures hands at the market rate",
      abs(world._annual_labourer_wage() - labourer_year) < 1e-9 * labourer_year, (world._annual_labourer_wage(), labourer_year))

check("the quote does not depend on who asks",
      market.quote(TRADE, 100.0, employer="a firm") == market.quote(TRADE, 100.0, employer=game.state.household))
check("more hours taken on cost more once the premium has risen", market.quote(TRADE, 5 * hours_per_year) > rate)

# ---- the hire quote is what payroll charges --------------------------------------------------------
hiring = stressed_game()
hiring.state.household.employees = {}
fee_quoted = hiring.labour.market.quote_annual(TRADE)
quote = _quote_hire(hiring, hiring.nodes, {"trade": TRADE, "n": 1})
check("the hire quote answers", quote.get("ok"), quote)
ok, _message = hiring.labour.hire(TRADE, 1)
payroll_per_year = hiring.labour.wage_bill() / hiring.state.household.employees[TRADE]
check("the quote's wage from next year is what payroll charges once hired",
      abs(quote["from_next_year_per_year"] - payroll_per_year) < 0.1,
      (quote["from_next_year_per_year"], payroll_per_year))
check("the finder's fee is the first year's wage at the market as it stood",
      abs(quote["paid_now"] - fee_quoted) < 0.1, (quote["paid_now"], fee_quoted))
check("no employer reaches a wage through the engine's own methods",
      not any(hasattr(S.Sim, name) for name in ("annual_wage", "market_wage_per_hour", "labour_price_factor",
                                                "labour_pressure", "_add_labour_pressure", "labour_pay_scale")))

# ---- hire and release record and ease the pressure -------------------------------------------------
fresh = sim()
pressure_before = fresh.labour.market.pressure(TRADE)
paid_rate = fresh.labour.market.hire("a firm", TRADE, 2 * hours_per_year)
check("hiring returns the rate it paid, the one quoted before it", paid_rate == sim().labour.market.quote(TRADE, 0.0) and paid_rate > 0)
check("hiring records the pressure", fresh.labour.market.pressure(TRADE) > pressure_before + 1.9 * hours_per_year)
fresh.labour.market.release("a firm", TRADE, 2 * hours_per_year)
check("releasing eases the pressure", fresh.labour.market.pressure(TRADE) < 1.0, fresh.labour.market.pressure(TRADE))

# ---- no module outside the labour market computes a wage -------------------------------------------
# The names only the labour market (and the schedule it reads) may touch.
WAGE_INTERNALS = {
    "market_wage_per_hour", "hiring_wage_per_hour", "labour_price_factor",
    "labour_price_factor_after_hiring", "_add_labour_pressure", "labour_pressure", "labour_pressure_records",
    "wage_cost_factors", "labour_pay_scale", "press_labour",
}
OWNERS = {"labour_market_api.py", "labour_wages.py", "labour_wage_ledger.py", "state.py", "household.py"}


class WageArithmeticVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.violations = []

    def visit_Attribute(self, node):
        if node.attr in WAGE_INTERNALS:
            self.violations.append((self.filename, node.lineno, "uses " + node.attr))
        self.generic_visit(node)

    def visit_BinOp(self, node):
        for operand in (node.left, node.right):
            if isinstance(operand, ast.Attribute) and operand.attr == "wage_index":
                self.violations.append((self.filename, node.lineno, "multiplies by wage_index"))
        self.generic_visit(node)


def wage_arithmetic_outside_the_market(source_by_name):
    violations = []
    for name, source in source_by_name.items():
        if os.path.basename(name) in OWNERS or os.path.basename(name) == "core.py":
            continue
        visitor = WageArithmeticVisitor(name)
        visitor.visit(ast.parse(source, filename=name))
        violations.extend(visitor.violations)
    return violations


def engine_sources():
    sources = {}
    for folder, _dirs, files in (entry for directory in engine_side_dirs() for entry in os.walk(directory)):
        for file_name in files:
            if file_name.endswith(".py"):
                path = os.path.join(folder, file_name)
                with open(path, encoding="utf-8") as handle:
                    sources[os.path.relpath(path, ROOT)] = handle.read()
    return sources


found = wage_arithmetic_outside_the_market(engine_sources())
check("no module outside the labour market computes a wage",
      not found, "\n".join("%s:%d %s" % entry for entry in found[:15]))
check("the structural scan catches a synthetic offender",
      len(wage_arithmetic_outside_the_market({"synthetic.py": "def f(sim, t):\n    return sim.labour_price_factor(t) * 2\n"})) == 1
      and len(wage_arithmetic_outside_the_market({"synthetic.py": "def f(sim, t):\n    return t * sim.wage_index\n"})) == 1
      and not wage_arithmetic_outside_the_market({"labour_market_api.py": "def f(sim, t):\n    return sim.labour_price_factor(t)\n"}))
