"""What the land module answers about carriage over the map: the modes that can carry a cargo, the facts of the modes, and the
cheapest and fastest ways between tiles. Mixed into `Land`."""
from typing import Any, Dict, Iterable, List, Mapping, Optional

from sim.assembly.api import Part
from sim.geography.api import (cargo_loss_per_day, carriage_rates, droving_carrier, dues_hours_per_tonne, modes_carrying, porter_carrier, reach,
                               route, train_carrier, usable_modes, walking_cargo_modes)


class MapCarriage(Part):
    """Mixed into `Land`."""


    def modes_usable(self, parties: Iterable[Iterable[str]], cargo: str = "goods") -> List[str]:
        """Sorted modes that carry `cargo` and that every party can use, from the technology nodes each holds."""
        return usable_modes(parties, self.parts.map_views.world_map, cargo)

    def modes_carrying(self, cargo: str) -> List[str]:
        """Sorted modes that take this class of cargo, whatever unlocks them."""
        return modes_carrying(cargo, self.parts.map_views.world_map)

    def carriage_facts(self) -> Dict[str, Any]:
        """{walking_modes: modes whose cargo walks, loss_per_day: {mode: share of the cargo lost a day on the road},
        dues_hours_per_tonne: {mode: labour hours of tolls or port dues per tonne}}."""
        return {"walking_modes": walking_cargo_modes(self.parts.map_views.world_map), "loss_per_day": cargo_loss_per_day(self.parts.map_views.world_map),
                "dues_hours_per_tonne": dues_hours_per_tonne(self.parts.map_views.world_map)}

    def mode_carrier(self, mode: str) -> Dict[str, Optional[Dict[str, Any]]]:
        """{train, droving, porter}: the mode as a rail carrier, a droving carrier or a porter carrier (each None where the mode is not that)."""
        world_map = self.parts.map_views.world_map
        return {"train": train_carrier(mode, world_map), "droving": droving_carrier(mode, world_map), "porter": porter_carrier(mode, world_map)}

    def mode_crews(self, modes: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        """{mode: {crew_trade, crew_hours_per_tonne_km, handling_hours_per_tonne, edge_classes}} for the modes that name a crew."""
        return carriage_rates(modes, self.parts.map_views.world_map)

    def cheapest_route(self, origin_tiles: Iterable[str], destination_tiles: Iterable[str], modes: Iterable[str],
                       improvements: Optional[Mapping[str, Mapping[str, Any]]] = None,
                       mode_costs: Optional[Mapping[str, float]] = None, handling_costs: Optional[Mapping[str, float]] = None,
                       held_nodes: Optional[Iterable[str]] = None, fastest: bool = False) -> Optional[Dict[str, Any]]:
        """The least-cost haul between two sets of tiles (the fewest-days one when `fastest`), or None when none joins them."""
        return route(origin_tiles, destination_tiles, modes, improvements, mode_costs=mode_costs, handling_costs=handling_costs,
                     held_nodes=held_nodes, world_map=self.parts.map_views.world_map, fastest=fastest)

    def reach_days(self, origin_tiles: Iterable[str], modes: Iterable[str], days_budget: float,
                   improvements: Optional[Mapping[str, Mapping[str, Any]]] = None,
                   held_nodes: Optional[Iterable[str]] = None) -> Dict[str, float]:
        """{tile: fewest days} reachable from these tiles by these modes within the budget."""
        return reach(origin_tiles, modes, days_budget, improvements, held_nodes=held_nodes, world_map=self.parts.map_views.world_map)
