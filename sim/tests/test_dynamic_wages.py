"""Endogenous wage foundations: food, housing, tools, skill, and scarcity."""
from .harness import *
from engine.data import ANNUAL_WAGE


s = sim()
check("neutral starting conditions preserve the calibrated wage table",
      abs(s.annual_wage("smith")
          - ANNUAL_WAGE["smith"] * s.price_index * s.wage_index) < 1e-6,
      s.annual_wage("smith"))

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
