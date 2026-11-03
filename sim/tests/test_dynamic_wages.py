"""Endogenous wage foundations: food, housing, tools, skill, and scarcity. The wage arithmetic (sim/labour/wage_factors.py)
is called with prices built here, so a failure names the line of arithmetic; the wage foundation the labour command shows is test_labour_command_wage_foundation."""
QUICK_TOPIC = True
from .harness import *

from sim.engine.data import ANNUAL_WAGE
from sim.labour.labour_market_api import LabourMarket
from sim.engine.data import _STARTING_SCHEDULE
from sim.labour.wages import training_premium
from sim.workforce.wage_schedule import HOUSEHOLD_TIME_PREFERENCE
from sim.labour.wage_factors import annual_wage, housing_factor, tools_factor, weighted_factor
CHEMIST_TRAINING_YEARS = _STARTING_SCHEDULE.training_years["chemist"]

SHARES = (LabourMarket.WAGE_SHARE_FOOD, LabourMarket.WAGE_SHARE_HOUSING, LabourMarket.WAGE_SHARE_TOOLS,
          LabourMarket.WAGE_SHARE_SKILL_AND_DIFFICULTY)
HOUSING = (LabourMarket.HOUSING_PRESSURE_START_OCCUPANCY, LabourMarket.HOUSING_PRESSURE_BAND,
           LabourMarket.HOUSING_PRESSURE_MAX_MARKUP)


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
      abs(annual_wage(1000.0, 1.1, 1.3, 1.4, 1.5) - 1000.0 * 1.1 * 1.3 * 1.4 * 1.5) < 1e-9)
# the training premium is priced at the households' own time preference (the wage rule), so a trade's wage over the unskilled trade's
# is that premium, not a multiple chosen beforehand
premium = training_premium(CHEMIST_TRAINING_YEARS, HOUSEHOLD_TIME_PREFERENCE)
check("skill and job difficulty still distinguish trades at neutral prices (the calibrated table)",
      premium > 1.0 and abs(ANNUAL_WAGE["chemist"] / ANNUAL_WAGE["labourer"] - premium) < 1e-9, (ANNUAL_WAGE["chemist"], ANNUAL_WAGE["labourer"], premium))
