"""Money moving between actors: every change of a purse names its purpose.

`credit` and `debit` live on `Actor`; an actor with a persistent record keeps
income and outlays by purpose, so its purse always equals its opening money
plus income less outlays. `transfer` is the one way a payer's loss becomes a
payee's gain, so money between actors is neither created nor destroyed. A payer short of what it pays raises
`InsufficientFunds` with nothing moved; a caller that can do with less asks `payable` or pays by `pay_up_to`.
"""
import contextlib
from typing import Any, Callable, Iterator, List, Mapping, Optional, Union

from sim.book import ROUNDING_SHARE, InsufficientFunds

Purpose = Union[str, Mapping[str, float]]

# Called after each transfer as hook(payer, payee, amount, purpose) while an engine listens (`listening`), so it can
# charge what moving the coin cost. It is switched off while it runs, so its own postings are not charged again.
AFTER_TRANSFER: List[Optional[Callable[[Any, Any, float, Purpose], None]]] = [None]
_IN_HOOK = [False]
# The transfers the hook made, collected while `recording_charges` is active, so a caller can take them back.
CHARGES: List[Optional[List[tuple]]] = [None]


@contextlib.contextmanager
def recording_charges(into: List[tuple]) -> Iterator[None]:
	"""Collect (payer, payee, amount, purpose) of each transfer the hook makes inside the block."""
	before = CHARGES[0]
	CHARGES[0] = into
	try:
		yield
	finally:
		CHARGES[0] = before


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

	`purpose` is a label, or a mapping of label to the amount of each part when one
	payment covers several things; the amount moved is authoritative, so a mapping that totals more or less is booked in
	proportion (`scaled`). A payer in
	the one book draws what its purse lacks on its facility within its limit; beyond
	that, or beyond what the economy's lenders hold, the payment raises `InsufficientFunds`.
	"""
	if amount == 0:
		return
	purpose = scaled(purpose, amount)
	purses = getattr(payer, "purses", None)
	if purses is not None and getattr(payee, "purses", None) is purses:
		# both keep accounts in the one book: a single posting, the payer drawing on its facility if short
		purses.transfer(payer.account_id, payee.account_id, amount, purposes_label(purpose))
		payer.payments.note_outlay(purpose, amount)
		payee.payments.note_income(purpose, amount)
	else:
		payer.payments.debit(amount, purpose)
		payee.payments.credit(amount, purpose)
	if _IN_HOOK[0] and CHARGES[0] is not None:
		CHARGES[0].append((payer, payee, amount, purpose))
	hook = AFTER_TRANSFER[0]
	if hook is not None:
		AFTER_TRANSFER[0] = None
		_IN_HOOK[0] = True
		try:
			hook(payer, payee, amount, purpose)
		finally:
			AFTER_TRANSFER[0] = hook
			_IN_HOOK[0] = False


def payable(payer: Any, amount: float) -> float:
	"""The most of `amount` the payer can pay now: its purse, its deposit and what the economy's lenders will lend it
	(`Purses.payable`); all of it for a payer outside the one book. A caller that can do with less caps what it pays to this,
	or uses `pay_up_to`."""
	purses = getattr(payer, "purses", None)
	return amount if purses is None else float(purses.payable(payer.account_id, amount))


def pay_up_to(payer: Any, payee: Any, amount: float, purpose: Purpose) -> float:
	"""Pay `amount`, or as much of it as `payer` can (`payable`); answers what was paid, which is nothing for a payer with
	nothing to pay with. Never raises `InsufficientFunds`: the caller does with less."""
	affordable = payable(payer, amount)
	for attempt in (affordable, 0.0 if getattr(payer, "purses", None) is None else min(affordable, payer.purses.purse(payer.account_id))):
		if attempt <= 0.0:
			return 0.0
		try:
			transfer(payer, payee, attempt, purpose)
			return attempt
		except InsufficientFunds:   # the lenders refused the draw after all: try what the payer's purse itself holds
			continue
	return 0.0


def pay_in_full(payer: Any, payee: Any, amount: float, purpose: Purpose) -> bool:
	"""Pay all of `amount` or nothing: False, with nothing moved, when the payer cannot (`payable`) or the lenders refuse the draw."""
	if payable(payer, amount) < amount * (1.0 - ROUNDING_SHARE):
		return False
	try:
		transfer(payer, payee, amount, purpose)
	except InsufficientFunds:
		return False
	return True


def reverse(payee: Any, payer: Any, amount: float, purpose: Purpose) -> None:
	"""Take back a payment `payer` made to `payee`: the money returns and the books of both forget the payment.
	It repays no facility, charges no coin cost and posts no flow line."""
	if amount == 0:
		return
	purpose = scaled(purpose, amount)
	purses = getattr(payee, "purses", None)
	if purses is not None and getattr(payer, "purses", None) is purses:
		purses.reverse(payee.account_id, payer.account_id, amount, purposes_label(purpose))
	else:
		payee.payments.debit(amount, purpose)
		payer.payments.credit(amount, purpose)
		payee.payments.note_outlay(purpose, -amount)
		payer.payments.note_income(purpose, -amount)
	payee.payments.note_income(purpose, -amount)
	payer.payments.note_outlay(purpose, -amount)


def cover(payer: Any, payees: List[Any], amount: float) -> Callable[[], None]:
	"""Before `payer` pays `amount` to several payees in the one book: its facility is drawn once for what its
	purse lacks, not once per payment. Answers the call that gives the draw back (nothing to give back outside the one book)."""
	purses = getattr(payer, "purses", None)
	if purses is not None and all(getattr(payee, "purses", None) is purses for payee in payees):
		return purses.cover(payer.account_id, amount)
	return lambda: None


def purposes_label(purpose: Purpose) -> str:
	"""A posting's purpose as the book's one label."""
	return purpose if isinstance(purpose, str) else "+".join(sorted(purpose))


def scaled(purpose: Purpose, amount: float) -> Purpose:
	"""The purpose with a mapping's parts brought to total `amount`, in proportion; a label as it is."""
	if not isinstance(purpose, Mapping):
		return purpose
	total = sum(purpose.values())
	if total <= 0.0 or abs(total - amount) <= abs(amount) * ROUNDING_SHARE:
		return purpose
	return {name: part * amount / total for name, part in purpose.items()}


def parts(purpose: Purpose, amount: float) -> Mapping[str, float]:
	"""The labelled parts of a payment."""
	return purpose if isinstance(purpose, Mapping) else {purpose: amount}
