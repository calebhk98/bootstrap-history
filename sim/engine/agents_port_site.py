"""What the land a concern occupies costs a firm that runs it: the view behind firm_entry.carrying_cost."""
from typing import Any

from sim.agents.api import supply
from sim.labour.api import production_data

KILOGRAMS_PER_TONNE = 1000.0


class SiteView:
	"""Read-only questions about the site of a concern; mixed into `SimWorld`."""

	_sim: Any

	def site_hectares(self, node_id: str, capacity: float = 1.0) -> float:
		"""Hectare-years of land a year of a concern run at `capacity` times its founding size ties up:
		for each production entry the concern gates that works land, its declared yearly output over
		the output of one batch, times the land one batch takes. Zero for a concern that declares no
		output or whose entries work no land (a building plot is not modelled)."""
		node = self.nodes[node_id]  # type: ignore[attr-defined]
		hectares = 0.0
		for entry in production_data().values():
			land_per_batch = float(entry.get("land_hectare_years") or 0.0)
			if entry.get("requires_node") != node_id or land_per_batch <= 0.0:
				continue
			for material, kilograms in sorted((entry.get("outputs") or {}).items()):
				tonnes = supply.concern_output_tonnes(node, node_id, material, 1.0, 1.0)
				if tonnes > 0.0 and kilograms > 0.0:
					hectares += tonnes * KILOGRAMS_PER_TONNE / kilograms * land_per_batch
					break
		return hectares * capacity

	def site_rent(self, node_id: str, capacity: float = 1.0) -> float:
		"""Yearly rent of the land a concern occupies, at the agent economy's land market's rent per
		hectare. TEMPORARY HEURISTIC (CLAUDE.md 4.4): a firm has no tile of its own, so it pays the mean
		rent of the land let; zero while the agent economy is off, which has no land market."""
		hectares = self.site_hectares(node_id, capacity)
		if hectares <= 0.0:
			return 0.0
		rent = self._sim.economy.agent_land_rent_per_hectare()
		return hectares * rent if rent else 0.0
