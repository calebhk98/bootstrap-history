"""The state the ledger owns: one seat's tonnes ledger and the capacity keys swept out of every seat's."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LedgerWorld:
	# hours and patronage that rode in a seat's tonnes ledger and were swept out of it (sim/ledger/rules.py `settled_stock`)
	capacity_pool: Dict[str, float] = field(default_factory=dict)


@dataclass
class LedgerSeat:
	_material_stock_ledger: Optional[Dict[str, float]] = None    # tonnes by commodity key; made on first use (a StockLedger)
	_material_stock_opening: Optional[Dict[str, Any]] = None     # {"year", "tonnes"}: the stock as this year's accounting began
