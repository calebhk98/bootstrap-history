"""Money moving between actors: every change of a purse names its purpose.

`credit` and `debit` live on `Actor`; an actor with a persistent record keeps
income and outlays by purpose, so its purse always equals its opening money
plus income less outlays. `transfer` is the one way a payer's loss becomes a
payee's gain, so money between actors is neither created nor destroyed.
"""
from typing import Any, Mapping, Union

Purpose = Union[str, Mapping[str, float]]


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


def parts(purpose: Purpose, amount: float) -> Mapping[str, float]:
	"""The labelled parts of a payment."""
	return purpose if isinstance(purpose, Mapping) else {purpose: amount}
