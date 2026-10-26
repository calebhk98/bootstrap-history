"""The ledger's rules as plain functions of the accounts they change."""
import collections
from typing import Any, Dict, Mapping, Optional

from sim.agents.api import payroll


def add_tonnes(stock: Dict[str, float], opening: Dict[str, float], commodity: str, tonnes: float) -> None:
	"""Tonnes added to (or, negative, taken from) a holder's stock and to this year's opening snapshot of it. The
	snapshot is taken before the change, so a holder's first change of a year is not counted twice."""
	stock[commodity] += tonnes
	opening[commodity] = opening.get(commodity, 0.0) + tonnes


def pay_wages(registry: Any, payer: Any, amount: float, purpose: Any, workers_edge: Any) -> None:
	"""Wages reach the free strata in proportion to their members, or the workers edge while there are none."""
	payroll.pay_households(registry, payer, amount, purpose, workers_edge)


# keys that ride in the tonnes ledger but are not tonnes: capacity hours and patronage move to the economy's capacity pool
NON_PHYSICAL_CAPACITY_KEYS = frozenset(("scholar_hours", "machinist_hours", "patronage"))


class StockLedger(collections.Counter):
	"""A seat's tonnes by commodity key. It notes when a capacity key may have been written into it, so the move of those
	into the capacity pool is not redone on every read, and counts the commands that wrote it (`writes`), so a reading
	worked out from it can tell that it changed."""

	unswept = True
	writes = 0

	def __setitem__(self, key: str, value: float) -> None:
		if key not in self:
			self.unswept = True
		super().__setitem__(key, value)


def settled_stock(held: Optional[Mapping[str, float]], capacity_pool: Dict[str, float]) -> StockLedger:
	"""The seat's tonnes ledger from what the state holds (nothing yet, or a plain dict a loaded save hands back), with the
	capacity keys swept into `capacity_pool` the first time they are seen."""
	stock = held
	if stock is None:
		stock = StockLedger()
	elif not isinstance(stock, StockLedger):
		stock = StockLedger(stock)      # a resumed save hands the ledger back as a plain dict
	if stock.unswept:
		for key in [key for key in stock if key in NON_PHYSICAL_CAPACITY_KEYS or key.endswith("_hours")]:
			capacity_pool[key] = capacity_pool.get(key, 0.0) + stock.pop(key)
		stock.unswept = False
	return stock


def year_opening_record(record: Optional[Dict[str, Any]], year: int, stock: Mapping[str, float]) -> Dict[str, Any]:
	"""The snapshot of stock the year's accounting works from: the record kept if it is this year's, else a new one
	holding a copy of `stock`."""
	if not record or record.get("year") != year:
		return {"year": year, "tonnes": dict(stock)}
	return record
