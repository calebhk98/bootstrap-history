"""SCENARIO (Complaint 640): the labour command in a game shows the wage foundation (the arithmetic is called on built prices in test_dynamic_wages)."""
from .harness import *

s = unopened_sim()

detail = S._agent_dispatch(s, NODES, {"cmd": "labour", "trade": "smith"})
check("scenario: labour detail exposes every wage component",
      all(component in detail["trade"]["wage_foundation"] for component in
          ("food", "housing", "tools", "skill_and_difficulty",
           "demographic_scarcity", "local_trade_scarcity")), detail)
