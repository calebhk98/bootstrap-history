"""bearable_part is the share of a loss that a purse and a credit line can take without capital ending below
the negative of the limit. Pure arithmetic on built inputs; one scenario that Sim.bearable_part_of reads the
credit line at the capital left after paying without writing the household's capital (the cash ledger bars
engine code from changing it outside the ledger)."""
from .harness import *  # noqa: F401,F403

from unittest import mock

from sim.engine.economy_credit import bearable_part

check("a loss within the purse is wholly bearable", bearable_part(3000.0, 5000.0, 100.0) == 3000.0)
check("a loss beyond the purse is borne up to the credit line left after paying",
      bearable_part(8000.0, 5000.0, 1500.0) == 6500.0)
check("a household already in arrears bears only what its remaining line allows",
      bearable_part(1000.0, -400.0, 900.0) == 500.0)
check("a household deeper in arrears than its line allows can bear nothing, never a negative part",
      bearable_part(1000.0, -2000.0, 900.0) == 0.0)

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
