"""bearable_part is the share of a loss that a purse and a credit line can take without capital ending below
the negative of the limit. Pure arithmetic on built inputs, and the method that feeds it on a stand-in."""
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


# The method hands the purse and the credit line at the capital left after paying to the rule, and writes no capital.
import types

from sim.engine.economy_credit import CreditMixin


class _Household:
    def __init__(self, capital):
        object.__setattr__(self, "capital", capital)
        object.__setattr__(self, "writes", [])

    def __setattr__(self, name, value):
        self.writes.append((name, value))
        object.__setattr__(self, name, value)


class _Borrower(CreditMixin):
    def __init__(self, capital, line_at):
        self.state = types.SimpleNamespace(household=_Household(capital))
        self._line_at = line_at
        self.capitals_asked = []

    def credit_limit(self, _capital=None):
        self.capitals_asked.append(_capital)
        return self._line_at(_capital)


_borrower = _Borrower(5000.0, lambda capital: 1000.0 + max(capital, 0.0) * 0.1)
_bearable = _borrower.bearable_part_of(3000.0)
check("bearable_part_of reads the credit line at the capital left after paying",
      _borrower.capitals_asked == [2000.0] and _bearable == bearable_part(3000.0, 5000.0, 1200.0),
      (_borrower.capitals_asked, _bearable))
check("bearable_part_of writes no capital", _borrower.state.household.writes == []
      and _borrower.state.household.capital == 5000.0, _borrower.state.household.writes)
