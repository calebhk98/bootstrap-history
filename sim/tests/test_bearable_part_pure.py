"""bearable_part is the share of a loss that a purse and a credit line can take without capital ending below
the negative of the limit. Pure arithmetic on built inputs, and the module method that feeds it, over plain values."""
QUICK_TOPIC = True

from .harness import check

from sim.finance.rules import bearable_part
from sim.tests import finance_host

check("a loss within the purse is wholly bearable", bearable_part(3000.0, 5000.0, 100.0) == 3000.0)
check("a loss beyond the purse is borne up to the credit line left after paying",
      bearable_part(8000.0, 5000.0, 1500.0) == 6500.0)
check("a household already in arrears bears only what its remaining line allows",
      bearable_part(1000.0, -400.0, 900.0) == 500.0)
check("a household deeper in arrears than its line allows can bear nothing, never a negative part",
      bearable_part(1000.0, -2000.0, 900.0) == 0.0)


# The method hands the purse and the credit line at the capital left after paying to the rule.
_capitals_asked = []


def _line_at(capital):
    _capitals_asked.append(capital)
    return 1000.0 + max(capital, 0.0) * 0.1


_borrower = finance_host.build(acting_balance=5000.0)
_borrower.credit_limit = lambda revenue=None, upkeep=None, capital=None: _line_at(capital)
_bearable = _borrower.bearable_part_of(3000.0)
check("bearable_part_of reads the credit line at the capital left after paying",
      _capitals_asked == [2000.0] and _bearable == bearable_part(3000.0, 5000.0, 1200.0), (_capitals_asked, _bearable))
