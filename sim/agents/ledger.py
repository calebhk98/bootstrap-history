"""Money moving between actors: every change of a purse names its purpose.

`credit` and `debit` live on `Actor`; an actor with a persistent record keeps
income and outlays by purpose, so its purse always equals its opening money
plus income less outlays. `transfer` is the one way a payer's loss becomes a
payee's gain, so money between actors is neither created nor destroyed.
"""
import contextlib
from typing import Any, Callable, Iterator, List, Mapping, Optional, Union

Purpose = Union[str, Mapping[str, float]]

# Called after each transfer as hook(payer, payee, amount, purpose) while an engine listens (`listening`), so it can
# charge what moving the coin cost. It is switched off while it runs, so its own postings are not charged again.
AFTER_TRANSFER: List[Optional[Callable[[Any, Any, float, Purpose], None]]] = [None]


@contextlib.contextmanager
def listening(hook: Callable[[Any, Any, float, Purpose], None]) -> Iterator[None]:
	"""Let `hook` see every transfer made inside the block."""
	before = AFTER_TRANSFER[0]
	AFTER_TRANSFER[0] = hook
	try:
		yield
	finally:
		AFTER_TRANSFER[0] = before


def transfer(payer: Any, payee: Any, amount: float, purpose: Purpose) -> None:
	"""Move `amount` from `payer` to `payee`.

	`purpose` is a label, or a mapping of label to share of the amount when one
	payment covers several things; the amount moved is authoritative. A
	household's purse may go negative, as it always could.
	"""
	if amount == 0:
		return
	payer.debit(amount, purpose)
	payee.credit(amount, purpose)
	hook = AFTER_TRANSFER[0]
	if hook is not None:
		AFTER_TRANSFER[0] = None
		try:
			hook(payer, payee, amount, purpose)
		finally:
			AFTER_TRANSFER[0] = hook


def settle(account: Any, other: Any, new_balance: float, purpose: Purpose) -> None:
	"""Bring `account`'s purse to `new_balance` by moving the difference to or from `other`."""
	difference = new_balance - account.money
	if difference > 0.0:
		transfer(other, account, difference, purpose)
	elif difference < 0.0:
		transfer(account, other, -difference, purpose)


def parts(purpose: Purpose, amount: float) -> Mapping[str, float]:
	"""The labelled parts of a payment."""
	return purpose if isinstance(purpose, Mapping) else {purpose: amount}
