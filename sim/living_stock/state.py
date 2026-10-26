"""The state living stock owns. The held tonnes are not here: they are rows of the ledger."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class LivingStockWorld:
	# stock material -> units of the held herd the society's producers keep, which the founder is not billed to raise
	society_herds: Dict[str, float] = field(default_factory=dict)
