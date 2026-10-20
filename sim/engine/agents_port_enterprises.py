"""What a state's own plants ask of the world: the inputs a plant uses up in a year."""
import math
from typing import Any, Dict

from sim.unit_conversions import KILOGRAMS_PER_TONNE

from .economy_port_setup import unit_mass_kg


class EnterpriseView:
	"""Read-only questions behind a state's plants; mixed into `SimWorld`."""

	_sim: Any

	def concern_inputs(self, node_id: str) -> Dict[str, float]:
		"""Tonnes of each material a concern of the node uses up in a year at its founding size, from its production
		entries; empty for a node whose figures are not derived from output."""
		baskets = self._sim.concern_baskets_now(node_id)
		if baskets is None:
			return {}
		inputs = {}
		for material, units in baskets.purchases.items():
			kilograms = unit_mass_kg(material)
			if units > 0.0 and math.isfinite(kilograms):
				inputs[material] = units * kilograms / KILOGRAMS_PER_TONNE
		return inputs
