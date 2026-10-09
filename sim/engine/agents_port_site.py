"""What the land a concern occupies costs a firm that runs it: the view behind firm_entry.carrying_cost."""
from typing import Any, Optional

from sim.agents.api import supply
from sim.constants import declare
from sim.labour.api import production_data
from sim.unit_conversions import KILOGRAMS_PER_TONNE

SQUARE_METRES_PER_HECTARE = 10000.0
FLOOR_AREA_PER_WORKER_SQUARE_METRES = declare(
	"FLOOR_AREA_PER_WORKER_SQUARE_METRES", 30.0, kind="temporary_heuristic",
	unit="square metres of site per person on a concern's staff", source=None, confidence="D",
	why="The ground a concern's workshop, plant and yard take per person working there, priced at the land "
		"market's rent. Stands in for a floor plan per concern, which no data gives.")


class SiteView:
	"""Read-only questions about the site of a concern; mixed into `SimWorld`."""

	_sim: Any

	def worked_hectares(self, node_id: str, capacity: float = 1.0) -> float:
		"""Hectare-years of land a year of a concern run at `capacity` times its founding size works: for
		each production entry the concern gates that works land, its declared yearly output over the
		output of one batch, times the land one batch takes. Zero for a concern that declares no output
		or whose entries work no land."""
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

	def plot_hectares(self, node_id: str, capacity: float = 1.0) -> float:
		"""Hectares of building plot a concern run at `capacity` times its founding size occupies: its
		staff at the stated floor area per person (workshop, plant and yard together)."""
		people = sum(self.concern_staff(node_id).values()) * capacity  # type: ignore[attr-defined]
		return people * FLOOR_AREA_PER_WORKER_SQUARE_METRES / SQUARE_METRES_PER_HECTARE

	def site_hectares(self, node_id: str, capacity: float = 1.0) -> float:
		"""Hectares a concern occupies: the plot its staff need and the land its output works."""
		return self.plot_hectares(node_id, capacity) + self.worked_hectares(node_id, capacity)

	def land_rent_at(self, tile: Optional[str]) -> float:
		"""Yearly rent of a hectare on a tile: the agent economy's land market's rent there (the mean rent
		of the land let where none was let on the tile); the engine's land price while it is off."""
		rent = self._sim.economy.agent_land_rent_at(tile)
		if rent is None or rent <= 0.0:
			return float(self.material_price("hectare_land"))  # type: ignore[attr-defined]
		return float(rent)

	def site_rent(self, node_id: str, capacity: float = 1.0, tile: Optional[str] = None) -> float:
		"""Yearly rent of the site a concern run at `capacity` times its founding size occupies, on the
		tile its firm stands on."""
		return self.site_hectares(node_id, capacity) * self.land_rent_at(tile)
