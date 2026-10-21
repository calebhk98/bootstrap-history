"""SCENARIO (Complaint 640): Sim.bearable_part_of reads the credit line at the capital left after paying without writing
the household's capital (the cash ledger bars engine code from changing it outside the ledger). The arithmetic is
in test_bearable_part_pure.py."""
from .harness import *  # noqa: F401,F403

from unittest import mock

from sim.engine.economy_credit import bearable_part

# scenario: the method on an unopened game
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
held = household.capital
household.capital = held - amount
limit_after = game.credit_limit()
household.capital = held
check("scenario: bearing a loss writes no capital, and is the credit line at the capital left after paying",
      writes == [] and household.capital == held and abs(bearable - bearable_part(amount, held, limit_after)) < 1e-9,
      (writes, bearable, held, limit_after))
