"""bearable_part_of reads the credit line at the capital left after paying without writing the household's capital
(the cash ledger bars engine code from changing it outside the ledger). Fast: one unopened game."""
from .harness import *  # noqa: F401,F403

from unittest import mock

game = sim()
household = game.state.household
household.capital = 5000.0
amount = 3000.0

writes = []
household_type = type(household)
original_setattr = household_type.__setattr__


def recording_setattr(self, name, value):
	if name == "capital":
		writes.append(value)
	original_setattr(self, name, value)


with mock.patch.object(household_type, "__setattr__", recording_setattr):
	bearable = game.bearable_part_of(amount)
check("bearing a loss does not write the household's capital", writes == [], writes)

# the same figure read the long way: the capital really left after paying
held = household.capital
household.capital = held - amount
limit_after = game.credit_limit()
household.capital = held
check("the bearable part is what the credit line leaves at the capital after paying",
      abs(bearable - min(amount, max(0.0, held + limit_after))) < 1e-9, (bearable, held, limit_after))
check("capital is unchanged after the question", household.capital == held, household.capital)
