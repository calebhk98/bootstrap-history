"""A household state that holds a number as its purse, for tests of readers that take the purse from a view (`acting_balance`)
and of state containers that need some household beside them. The real purse is the seat's account in the actors' book
(sim/ledger/seat_account.py); a test of money moving uses `sim/tests/money_host.py`."""
from dataclasses import dataclass

from sim.engine.state import HouseholdState


@dataclass
class PurseHousehold(HouseholdState):
    capital: float = 0.0
