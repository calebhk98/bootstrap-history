"""bearable_part is the share of a loss that a purse and a credit line can take without capital ending below
the negative of the limit. Pure arithmetic on built inputs; the method on a game is in
test_bearable_part_pure_scenario.py."""
QUICK_TOPIC = True

from .harness import check

from sim.engine.economy_credit import bearable_part

check("a loss within the purse is wholly bearable", bearable_part(3000.0, 5000.0, 100.0) == 3000.0)
check("a loss beyond the purse is borne up to the credit line left after paying",
      bearable_part(8000.0, 5000.0, 1500.0) == 6500.0)
check("a household already in arrears bears only what its remaining line allows",
      bearable_part(1000.0, -400.0, 900.0) == 500.0)
check("a household deeper in arrears than its line allows can bear nothing, never a negative part",
      bearable_part(1000.0, -2000.0, 900.0) == 0.0)
