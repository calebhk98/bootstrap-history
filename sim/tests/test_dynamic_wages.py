"""Endogenous wage foundations: food, housing, tools, skill, and scarcity. The wage arithmetic (sim/labour/wage_factors.py)
is called with prices built here, so a failure names the line of arithmetic; three named scenarios read a game."""
from .harness import *

sim = unopened_sim   # legacy: pins the engine's wage table and loanable-funds rate; the agent economy sets both in sim/economy

from sim.engine.data import ANNUAL_WAGE
from sim.labour.labour_wages import WagesMixin
from sim.labour.wage_factors import annual_wage, housing_factor, tools_factor, weighted_factor

SHARES = (WagesMixin.WAGE_SHARE_FOOD, WagesMixin.WAGE_SHARE_HOUSING, WagesMixin.WAGE_SHARE_TOOLS,
          WagesMixin.WAGE_SHARE_SKILL_AND_DIFFICULTY)
HOUSING = (WagesMixin.HOUSING_PRESSURE_START_OCCUPANCY, WagesMixin.HOUSING_PRESSURE_BAND,
           WagesMixin.HOUSING_PRESSURE_MAX_MARKUP)


def weighted(food=1.0, housing=1.0, tools=1.0):
    return weighted_factor(*SHARES, food, housing, tools)


check("at neutral prices the cost-of-living shares sum to a factor of one", abs(weighted() - 1.0) < 1e-12, SHARES)
check("cheaper staple food lowers the wage required to live",
      weighted(food=0.60) < weighted() * 0.85, (weighted(food=0.60), weighted()))

# --- housing: a town with room charges nothing extra, a full one marks the wage up, and more housing relieves it
check("a town with room to spare adds no housing markup", housing_factor(40.0, 100.0, *HOUSING) == 1.0)
crowded = housing_factor(95.0, 100.0, *HOUSING)
check("a crowded town marks the wage up", 1.0 < crowded <= 1.0 + HOUSING[2], crowded)
check("expanding housing capacity relieves wage pressure", housing_factor(95.0, 200.0, *HOUSING) < crowded)
check("the markup stops at its maximum however crowded the town",
      abs(housing_factor(1000.0, 100.0, *HOUSING) - (1.0 + HOUSING[2])) < 1e-12)

# --- tools: scarce materials raise the wage of the trade that maintains them
basket = ["iron", "charcoal"]
neutral_tools = tools_factor(basket, lambda material: 1.0, lambda material: 1.0)
scarce_tools = tools_factor(basket, lambda material: 2.0 if material == "iron" else 1.0, lambda material: 1.0)
check("scarce job tools raise the wage of a trade that must maintain them",
      neutral_tools == 1.0 and scarce_tools == 1.5 and weighted(tools=scarce_tools) > weighted())
check("a trade with no tools is not affected by tool prices", tools_factor([], lambda m: 9.0, lambda m: 9.0) == 1.0)
check("the market ratio of a tool scales its factor",
      tools_factor(["iron"], lambda m: 1.0, lambda m: 0.5) == 0.5)

# --- the annual figure is the base through every factor
check("the annual wage is the base times every factor on it",
      abs(annual_wage(1000.0, 1.1, 1.2, 1.3, 1.4, 1.5) - 1000.0 * 1.1 * 1.2 * 1.3 * 1.4 * 1.5) < 1e-9)
check("skill and job difficulty still distinguish trades at neutral prices (the calibrated table)",
      ANNUAL_WAGE["chemist"] > ANNUAL_WAGE["labourer"] * 2, (ANNUAL_WAGE["chemist"], ANNUAL_WAGE["labourer"]))

# --- SCENARIOS: the market's quote in a game
s = sim()
# THE TOLERANCE IS RELATIVE, AND IT IS NOT ZERO, FOR A REAL REASON: a smith's tool basket is iron and charcoal, and Rome
# at year zero already holds inherited technologies that burn charcoal, so charcoal opens the game a hair above neutral
# (wage_cost_factors says so); 1e-4 relative still catches any drift a thousand times smaller than the moves the rule
# tests above look for.
_expected = ANNUAL_WAGE["smith"] * s.price_index * s.wage_index
check("scenario: neutral starting conditions preserve the calibrated wage table",
      abs(s.labour.market.quote_annual("smith") - _expected) / _expected < 1e-4,
      (s.labour.market.quote_annual("smith"), _expected))

s.employees["smith"] = 1
check("scenario: the payroll uses the same derived wage quoted for one employee",
      abs(s.labour.wage_bill() - s.labour.market.quote_annual("smith")) < 1e-6,
      (s.labour.wage_bill(), s.labour.market.quote_annual("smith")))

detail = S._agent_dispatch(s, NODES, {"cmd": "labour", "trade": "smith"})
check("scenario: labour detail exposes every wage component",
      all(component in detail["trade"]["wage_foundation"] for component in
          ("food", "housing", "tools", "skill_and_difficulty",
           "demographic_scarcity", "local_trade_scarcity")), detail)
