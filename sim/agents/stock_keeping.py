"""What an actor keeps of what it bought: goods delivered to a buyer that keeps its purchases join its stores."""
from typing import Dict, Mapping


def add_delivery(stores: Dict[str, float], delivered_tonnes: Mapping[str, float]) -> None:
	"""Add each delivered material's tonnes to the stores; a delivery of nothing adds no entry."""
	for material in sorted(delivered_tonnes):
		tonnes = float(delivered_tonnes[material])
		if tonnes > 0.0:
			stores[material] = stores.get(material, 0.0) + tonnes
