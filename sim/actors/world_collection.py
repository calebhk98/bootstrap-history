"""What the home state's officials collect, tile by tile: the people on each tile, the routes open to the state."""
from typing import Any, Dict, List

from sim.agents.api import FAR_DAYS, CollectionView, collection
from sim.geography.api import settlement


class HomeCollection(CollectionView):
	"""The shared reading of the collected share, over the home state's held tiles and the game's map."""

	def collection_people_by_tile(self) -> Dict[str, float]:
		"""People on each tile the state holds: the tracked regions' where they cover the tiles, else the nation spread by settlement."""
		needs = self.world.needs
		tracked = needs.people_by_tile()
		if tracked is not None:
			return dict(tracked)
		held = self.world.revenue.held_tiles()
		return collection.spread_people(needs.population_total(), settlement.population_shares(held))

	def collection_modes(self) -> List[str]:
		"""The route modes the state's held technologies open."""
		return self.world.needs.home_modes()

	def collection_reach(self, seat: str, modes: Any) -> Dict[str, float]:
		"""{tile: fewest days} from the seat's tile by these modes over the game's map."""
		return self.world.needs.reach_days([seat], modes, FAR_DAYS)
