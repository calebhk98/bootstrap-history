"""A seat founds a bank: any seat whose knowledge holds a node declaring `deposit_banking` may put capital into one.

The bank is an agent of the agent economy like any a household founds (sim/economy/banks.py): it takes deposits from households,
lends them on, keeps a reserve, and can be run on. The seat's capital leaves its money and is the bank's own capital; what the bank
earns beyond that capital and the capital it keeps behind its loans is paid back to the seat."""
from typing import Any, Optional

from sim.refusal import Refusal

BANKING_MECHANIC = "deposit_banking"


def refusal_for(knows_banking: bool, capital: Any, money: float) -> Optional[Refusal]:
	"""Why the seat cannot found a bank with `capital`, or None."""
	if not knows_banking:
		return Refusal("no_banking_institution", "You do not hold a technology that lets you take deposits and lend them on; "
		               "'available' lists what you could begin.")
	if isinstance(capital, bool) or not isinstance(capital, (int, float)) or capital <= 0.0:
		return Refusal("capital_not_positive", "The capital is an amount of money above zero.", capital=capital)
	if capital > money:
		return Refusal("capital_exceeds_cash", "You hold less than that to put into a bank.", capital=capital, cash=money)
	return None
