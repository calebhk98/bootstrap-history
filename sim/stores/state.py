"""The stores module's saved state."""
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class StoresWorld:
	# declared store -> {tile, actor or "actor|actor" key: value differing from the default}
	values: Dict[str, Dict[str, Any]] = field(default_factory=dict)
