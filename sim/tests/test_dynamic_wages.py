"""Endogenous wage foundations: food, housing, tools, skill, and scarcity."""
from .harness import *
from engine.data import ANNUAL_WAGE


s = sim()
# THE TOLERANCE IS RELATIVE, AND IT IS NOT ZERO, FOR A REAL REASON.
#
# This check had never run. It sat behind test_demographics.py's stray
# sys.exit, which ended every full-suite run ten topics before this one, so
# nobody saw that it fails on an absolute 1e-6 against a number of magnitude
# 281 - a demand for nine significant figures.
#
# It fails by 9.2e-7 relative, and the cause is the model being right rather
# than wrong. A smith's tool basket is iron and charcoal, and Rome at year
# zero already holds 223 inherited technologies that burn charcoal, so the
# charcoal market opens the game with 5.0 t/yr of real demand against it and
# material_price_factor("charcoal") is 1.0000183, not 1.0. A society that
# already smelts iron SHOULD price charcoal a hair above nothing, and the
# smith's wage should carry that hair. The "exactly 1.0" the docstring on
# wage_cost_factors used to claim was the overstatement; it now says what
# actually happens.
#
# 1e-4 relative keeps this check doing its job - every other check in this
# file looks for moves of 15% or more, and this one still catches any drift
# a thousand times smaller than those - without demanding that an endogenous
# market round-trip to a book value it is supposed to be replacing.
_expected = ANNUAL_WAGE["smith"] * s.price_index * s.wage_index
check("neutral starting conditions preserve the calibrated wage table",
      abs(s.annual_wage("smith") - _expected) / _expected < 1e-4,
      (s.annual_wage("smith"), _expected))

baseline = s.annual_wage("smith")
s.essential_price_ratio = lambda: 0.60
check("cheaper staple food lowers the wage required to live",
      s.annual_wage("smith") < baseline * 0.85,
      (baseline, s.annual_wage("smith")))

s = sim()
s.headcount = lambda: 9.0
s.supervision_room = lambda: 10.0
crowded = s.annual_wage("smith")
s.supervision_room = lambda: 20.0
check("expanding housing capacity relieves wage pressure",
      s.annual_wage("smith") < crowded, (crowded, s.annual_wage("smith")))

s = sim()
normal = s.annual_wage("smith")
s.material_price_factor = lambda material: 2.0 if material == "iron" else 1.0
check("scarce job tools raise the wage of a trade that must maintain them",
      s.annual_wage("smith") > normal, (normal, s.annual_wage("smith")))

s = sim()
check("skill and job difficulty still distinguish trades at neutral prices",
      s.annual_wage("chemist") > s.annual_wage("labourer") * 2,
      (s.annual_wage("chemist"), s.annual_wage("labourer")))

s.employees["smith"] = 1
check("the payroll uses the same derived wage quoted for one employee",
      abs(s.wage_bill() - s.annual_wage("smith")) < 1e-6,
      (s.wage_bill(), s.annual_wage("smith")))

detail = S._agent_dispatch(s, NODES, {"cmd": "labour", "trade": "smith"})
check("labour detail exposes every wage component",
      all(k in detail["trade"]["wage_foundation"] for k in
          ("food", "housing", "tools", "skill_and_difficulty",
           "demographic_scarcity", "local_trade_scarcity")), detail)
