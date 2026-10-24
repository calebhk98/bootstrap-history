"""Complaints 358 and 356: every employer asks the one labour market. Whoever asks is quoted the same rate for the same
trade at the same moment; hiring records pressure and releasing eases it; and no module outside the labour market
computes a wage. The market is called over a stand-in for the household and the world it reads; the employers reaching it
are in test_one_labour_market_wiring."""
import ast
import os
from types import SimpleNamespace
from unittest import mock

from .harness import *  # noqa: F401,F403

from sim.labour import labour_market_api
from sim.labour.labour_market_api import LabourMarket
from sim.labour.wage_factors import annual_wage
from .source_dirs import engine_side_dirs

QUICK_TOPIC = True
UNDER_TEST = {"hire"}

TRADE = "artisan"
HOURS_PER_YEAR = 2000.0
SUPPLY = 10_000.0          # hours a year of the trade the local market has
BASE, WEIGHTED, PRICE_INDEX, WAGE_INDEX, PAY_SCALE = 100.0, 1.2, 1.5, 1.3, 1.1


def market(pressure_records=None):
    """A labour market over a stand-in: a base wage, cost-of-living factor, price and wage indices and a local supply."""
    employed = {}
    world = SimpleNamespace(
        state=SimpleNamespace(household=SimpleNamespace(labour_pressure_records={} if pressure_records is None else pressure_records),
                              scenario=SimpleNamespace(year=0)),
        HOURS_PER_PERSON_YEAR=HOURS_PER_YEAR, price_index=PRICE_INDEX, wage_index=WAGE_INDEX,
        economy=SimpleNamespace(agent_wage_per_hour=lambda trade: None), real_output_per_head=lambda: PAY_SCALE,
        wages={}, actor_staff_fte=lambda name: 0.0)
    labour = SimpleNamespace(
        _world=world, wage_schedule=lambda: SimpleNamespace(training_years={}),
        market_supply=lambda trade: SUPPLY + HOURS_PER_YEAR * employed.get(trade, 0.0),
        employed=lambda trade: employed.get(trade, 0.0),
        set_employed=lambda trade, people: employed.__setitem__(trade, people),
        base_annual_wage=lambda trade: BASE, wage_cost_factors=lambda trade: {"weighted": WEIGHTED},
        LABOUR_PAY_SHARE_OF_OUTPUT_GAIN=1.0)
    return LabourMarket(labour)


FALLBACK = mock.patch.object(labour_market_api.trade_data, "fallback_trade_of", lambda world, years: "labourer")
FALLBACK.start()

# ---- one rate for every kind of employer
unstressed = market()
stressed = market()
stressed.press(TRADE, SUPPLY * 0.8)
check("the stressed market has a scarcity premium above one", stressed.price_factor(TRADE) > 1.05, stressed.price_factor(TRADE))
rate = stressed.quote(TRADE, 0.0)
expected = annual_wage(BASE, WEIGHTED, PRICE_INDEX, WAGE_INDEX, stressed.price_factor(TRADE), PAY_SCALE) / HOURS_PER_YEAR
check("an hour's quote is the wage arithmetic over the base, the cost of living, the indices and the scarcity premium",
      abs(rate - expected) < 1e-12 * expected, (rate, expected))
check("the quote does not depend on who asks",
      stressed.quote(TRADE, 100.0, employer="a firm") == stressed.quote(TRADE, 100.0, employer=SimpleNamespace()))
check("more hours taken on cost more once the premium has risen", stressed.quote(TRADE, 5 * HOURS_PER_YEAR) > rate)
check("the annual quote is an hour's quote times the hours of a person-year",
      abs(stressed.quote_annual(TRADE) - rate * HOURS_PER_YEAR) < 1e-9 * stressed.quote_annual(TRADE))
check("a trade nobody has leaned on is quoted at the wage table, with no premium",
      unstressed.price_factor(TRADE) == 1.0 and abs(unstressed.quote_annual(TRADE) - unstressed.unscarce_annual(TRADE)) < 1e-12)

# ---- the hire quote is what payroll charges
check("the finder's fee for one hire is the first year's wage at the market as it stood",
      abs(stressed.hire_cost(TRADE, 1) - stressed.quote_annual(TRADE)) < 1e-9 * stressed.quote_annual(TRADE),
      (stressed.hire_cost(TRADE, 1), stressed.quote_annual(TRADE)))
check("each further hire costs more than the one before, as those before thin the pool",
      stressed.hire_cost(TRADE, 5) > 5 * stressed.hire_cost(TRADE, 1) * 0.999, (stressed.hire_cost(TRADE, 5), stressed.hire_cost(TRADE, 1)))
check("no employer reaches a wage through the engine's own methods",
      not any(hasattr(S.Sim, name) for name in ("annual_wage", "market_wage_per_hour", "labour_price_factor",
                                                "labour_pressure", "_add_labour_pressure", "labour_pay_scale")))

# ---- hire and release record and ease the pressure
pressed = []
recorder = SimpleNamespace(quote=lambda trade, hours, employer, premium: 12.5, press=lambda trade, hours: pressed.append((trade, hours)))
paid_rate = LabourMarket.hire(recorder, "a firm", TRADE, 2 * HOURS_PER_YEAR)
check("hiring returns the rate the market quoted", paid_rate == 12.5)
check("hiring records the hours as pressure", pressed == [(TRADE, 2 * HOURS_PER_YEAR)], pressed)
leaned_on = market({TRADE: (2 * HOURS_PER_YEAR, 0)})
leaned_on.release("a firm", TRADE, 2 * HOURS_PER_YEAR)
check("releasing eases the pressure", leaned_on.pressure(TRADE) < 1.0, leaned_on.pressure(TRADE))
FALLBACK.stop()

# ---- no module outside the labour market computes a wage -------------------------------------------
# The names only the labour market (and the schedule it reads) may touch.
WAGE_INTERNALS = {
    "market_wage_per_hour", "hiring_wage_per_hour", "labour_price_factor",
    "labour_price_factor_after_hiring", "_add_labour_pressure", "labour_pressure", "labour_pressure_records",
    "wage_cost_factors", "labour_pay_scale", "press_labour",
}
OWNERS = {"labour_market_api.py", "labour_wages.py", "labour_wage_ledger.py", "state.py", "household.py"}
# Modules that show or record the wage level (screens, the cause book, the labour port, the country profile
# builder) without turning it into a wage: they may read it, never multiply by it.
LEVEL_REPORTERS = ("sim/ui/", "engine/baseline_game.py", "engine/cause_book.py", "engine/labour_port.py",
                   "engine/shock_year.py", "agents/cast.py")


class WageArithmeticVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.violations = []

    def visit_Attribute(self, node):
        if node.attr in WAGE_INTERNALS:
            self.violations.append((self.filename, node.lineno, "uses " + node.attr))
        if node.attr == "wage_index" and isinstance(node.ctx, ast.Load):
            self.violations.append((self.filename, node.lineno, "reads wage_index"))
        self.generic_visit(node)

    def visit_BinOp(self, node):
        for operand in (node.left, node.right):
            if isinstance(operand, ast.Attribute) and operand.attr == "wage_index":
                self.violations.append((self.filename, node.lineno, "multiplies by wage_index"))
        self.generic_visit(node)

    def visit_Call(self, node):
        # a wage level passed by name (getattr(profile, "wage_index"), a helper keyed on it) is a read too
        for argument in list(node.args) + [keyword.value for keyword in node.keywords]:
            if isinstance(argument, ast.Constant) and argument.value == "wage_index":
                self.violations.append((self.filename, node.lineno, "passes the name wage_index to a call"))
        self.generic_visit(node)


def wage_arithmetic_outside_the_market(source_by_name):
    violations = []
    for name, source in source_by_name.items():
        if os.path.basename(name) in OWNERS or os.path.basename(name) == "core.py":
            continue
        visitor = WageArithmeticVisitor(name)
        visitor.visit(ast.parse(source, filename=name))
        reports_only = any(marker in name.replace(os.sep, "/") for marker in LEVEL_REPORTERS)
        violations.extend(entry for entry in visitor.violations
                          if not (reports_only and entry[2].startswith(("reads", "passes"))))
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
      and len(wage_arithmetic_outside_the_market({"synthetic.py": "def f(sim, t):\n    return t * sim.wage_index\n"})) == 2
      and not wage_arithmetic_outside_the_market({"labour_market_api.py": "def f(sim, t):\n    return sim.labour_price_factor(t)\n"}))
check("the scan flags a wage level read or passed by name outside the owners, and lets a screen read it",
      len(wage_arithmetic_outside_the_market({"synthetic.py": "def f(profile):\n    return profile.wage_index\n"})) == 1
      and len(wage_arithmetic_outside_the_market({"synthetic.py": "def f(profile):\n    return getattr(profile, 'wage_index')\n"})) == 1
      and not wage_arithmetic_outside_the_market({"sim/ui/screen.py": "def f(sim):\n    return sim.wage_index\n"})
      and len(wage_arithmetic_outside_the_market({"sim/ui/screen.py": "def f(sim):\n    return 2 * sim.wage_index\n"})) == 1)
