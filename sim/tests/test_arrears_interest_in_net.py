"""The net a household is told counts the interest on its arrears as a cost, called as functions on chosen numbers."""
QUICK_TOPIC = True
from .harness import *  # noqa: F401,F403

from sim.finance.rules import interest_on_arrears, net_after_interest

check("interest on arrears is the debt times the rate", abs(interest_on_arrears(-3000.0, 0.12) - 360.0) < 1e-9)
check("a purse in credit pays no interest", interest_on_arrears(500.0, 0.12) == 0.0)
check("a debt at a nil rate costs nothing", interest_on_arrears(-3000.0, 0.0) == 0.0)
check("the net falls by the interest on the debt",
      abs(net_after_interest(131.0, -3000.0, 0.12) - (131.0 - 360.0)) < 1e-9)
check("a small surplus before interest turns into a deficit once arrears interest is counted",
      net_after_interest(131.0, -3000.0, 0.12) < 0.0)
check("the net is untouched when nothing is owed", net_after_interest(131.0, 10.0, 0.12) == 131.0)
