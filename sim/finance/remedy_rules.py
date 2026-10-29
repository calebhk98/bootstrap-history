"""The lines a refused purchase lists as ways to raise cash, as plain functions of the figures each command itself uses."""
from typing import Callable, List, Optional, Sequence, Tuple

REMEDY_LIMIT = 6
SMALLEST_SAVING = 0.5   # a saving of no more than this is not worth a line

Remedy = Optional[Tuple[float, str]]


def sale_remedy(material: str, tonnes: float, money: float, money_text: Callable[..., str]) -> Remedy:
	"""Selling a material, worth `money` now for `tonnes`; None when the market pays nothing."""
	if money <= 0:
		return None
	return money, "sell %s %s (brings %s now)" % (material, "{:,.1f}".format(tonnes), money_text(money, grouped=True))


def mothball_remedy(node_id: str, saving: float, money_text: Callable[..., str]) -> Remedy:
	"""Mothballing a concern, which stops `saving` a year of upkeep."""
	if saving <= SMALLEST_SAVING:
		return None
	return saving, "mothball %s (stops %s a year of upkeep)" % (node_id, money_text(saving, grouped=True))


def mine_closing_remedy(material: str, saving: float, money_text: Callable[..., str]) -> Remedy:
	"""Closing the mines of a material, which stops `saving` a year of mine costs."""
	if saving <= SMALLEST_SAVING:
		return None
	return saving, "close %s (stops %s a year of mine costs)" % (material, money_text(saving, grouped=True))


def firing_remedy(trade: str, people: float, wage: float, money_text: Callable[..., str]) -> Remedy:
	"""Letting go the staff of a trade, which stops `wage` a year for each person; None when nobody is hired."""
	if people <= 0 or wage <= SMALLEST_SAVING:
		return None
	return wage, "fire %s (stops %s a year per person)" % (trade, money_text(wage, grouped=True))


def top_remedies(found: Sequence[Tuple[float, str]], limit: int = REMEDY_LIMIT) -> List[str]:
	"""The lines of the largest amounts, the largest first (equal amounts keep the order found)."""
	return [line for _amount, line in sorted(found, key=lambda entry: -entry[0])[:limit]]
