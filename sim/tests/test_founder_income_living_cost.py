"""Complaint 524: a household lives within what its income carries: the dependants' cost the surplus cannot carry is shed,
never the household's own subsistence, and a household in arrears also pays its creditors their share first."""
from .harness import *  # noqa: F401,F403

from sim.finance.rules import dependants_not_carried

QUICK_TOPIC = True

DEPENDANTS = 100.0

check("a surplus larger than the dependants' cost carries them all", dependants_not_carried(DEPENDANTS, 500.0, 0.0) == 0.0)
check("a surplus that just covers them sheds none", dependants_not_carried(DEPENDANTS, DEPENDANTS, 0.0) == 0.0)
check("half the cost in surplus sheds half", dependants_not_carried(DEPENDANTS, 50.0, 0.0) == 50.0)
check("no surplus sheds them all", dependants_not_carried(DEPENDANTS, 0.0, 0.0) == DEPENDANTS)
check("a loss sheds them all and no more than their cost", dependants_not_carried(DEPENDANTS, -80.0, 0.0) == DEPENDANTS)
check("creditors take their share of the surplus before the dependants",
      dependants_not_carried(DEPENDANTS, 100.0, 0.5) == 50.0 and dependants_not_carried(DEPENDANTS, 100.0, 0.5) > dependants_not_carried(DEPENDANTS, 100.0, 0.0))
check("with no dependants nothing is shed", dependants_not_carried(0.0, -5.0, 0.5) == 0.0)
check("what is shed is never negative nor above the dependants' cost",
      all(0.0 <= dependants_not_carried(DEPENDANTS, surplus, share) <= DEPENDANTS
          for surplus in (-1e9, -1.0, 0.0, 1.0, 99.0, 1e9) for share in (0.0, 0.5, 1.0)))
