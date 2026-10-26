"""The money gate on beginning a project, called as a function on numbers the test chooses."""
QUICK_TOPIC = True
from .harness import *  # noqa: F401,F403

from sim.projects.api import start_money
start_shortfall = start_money.start_shortfall

check("a bill inside cash plus credit has no shortfall",
      start_shortfall(price=900.0, owed_on_work_in_hand=0.0, extra_owed=0.0, capital=400.0, credit_limit=600.0)[2] == 0.0)
check("a bill exactly at the ceiling is affordable",
      start_shortfall(price=1000.0, owed_on_work_in_hand=0.0, extra_owed=0.0, capital=400.0, credit_limit=600.0)[2] == 0.0)
owed, ceiling, shortfall = start_shortfall(
    price=700.0, owed_on_work_in_hand=300.0, extra_owed=0.0, capital=400.0, credit_limit=600.0)
check("work in hand counts against the ceiling", (owed, ceiling, shortfall) == (300.0, 1000.0, 0.0),
      (owed, ceiling, shortfall))
check("work in hand makes a bill that would fit alone unaffordable",
      start_shortfall(price=800.0, owed_on_work_in_hand=300.0, extra_owed=0.0, capital=400.0, credit_limit=600.0)[2] == 100.0)
check("extra_owed counts exactly like work in hand",
      start_shortfall(price=800.0, owed_on_work_in_hand=0.0, extra_owed=300.0, capital=400.0, credit_limit=600.0)
      == start_shortfall(price=800.0, owed_on_work_in_hand=300.0, extra_owed=0.0, capital=400.0, credit_limit=600.0))
check("an enormous extra_owed leaves a shortfall",
      start_shortfall(price=1.0, owed_on_work_in_hand=0.0, extra_owed=1e9, capital=400.0, credit_limit=600.0)[2] > 0.0)
check("debt adds nothing to what can be raised, it only uses up the line",
      start_shortfall(price=500.0, owed_on_work_in_hand=0.0, extra_owed=0.0, capital=-200.0, credit_limit=600.0)[1] == 600.0)
