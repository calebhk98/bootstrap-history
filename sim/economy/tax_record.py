"""What the economy keeps about taxation from year to year (the state's budget is its own dataclass, `state_budget.py`)."""
from dataclasses import dataclass, field
from typing import Any, Dict

from .record_parts import OwnedRecord


@dataclass
class TaxRecord(OwnedRecord):
    tax_history: Dict[str, Dict[str, float]] = field(default_factory=dict)   # form -> last year's base and the state's own take (tax_farming.py)
    tax_farms: Dict[str, Dict[str, Any]] = field(default_factory=dict)   # form -> this year's farmer and price; empty between years

    SAVED_SORTED = ("tax_history",)
    TRANSIENT = ("tax_farms",)   # set and cleared inside the year
