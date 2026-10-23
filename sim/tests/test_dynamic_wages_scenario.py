"""SCENARIO (Complaint 640): the market's quote of a wage in a game (the arithmetic is called on built prices in test_dynamic_wages)."""
from .harness import *

sim = unopened_sim   # pins the engine's wage table and loanable-funds rate; the agent economy sets both in sim/economy

from sim.engine.data import ANNUAL_WAGE

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
