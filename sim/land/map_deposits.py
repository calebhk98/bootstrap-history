"""What the land module answers about the deposits in the ground: the catalogue of what is mined, the deposits a party can name,
what was worked before the game began, the most a deposit yields and what prospecting finds. Mixed into `Land`."""
from typing import Any, Dict, Iterable, List, Mapping, Optional

from sim.geography.api import (endowment, mined_before, mine_demand_goods, ore_goods, parameter_value, prospect, resource_ids,
                               worked_deposits, working_rate_tonnes_per_year, works_priced_from_deposits)


class MapDeposits:
    """Mixed into `Land`."""

    world_map: Any
    _deposit_catalogue_cache: Optional[Dict[str, Any]] = None

    def deposit_catalogue(self) -> Dict[str, Any]:
        """What the map's catalogue says is mined, kept (the map does not change in a game): {mechanisms: {resource id: its
        mechanism}, metals: the resources that yield ore goods, ore_goods: {resource: {ore good: smelting recipes}},
        works_priced_materials: the resources whose running cost comes from the deposits' works, demand_goods: {resource:
        goods whose demand a mine of it supplies}, mining_trade: the trade whose wage prices mine labour}."""
        if self._deposit_catalogue_cache is None:
            world_map = self.world_map
            resources = world_map.catalogue("resources")
            ores = ore_goods(world_map)
            self._deposit_catalogue_cache = {
                "mechanisms": {resource: resources[resource].get("mechanism") for resource in resource_ids(world_map)},
                "metals": tuple(ores), "ore_goods": ores,
                "works_priced_materials": works_priced_from_deposits(world_map),
                "demand_goods": mine_demand_goods(world_map), "mining_trade": parameter_value("mining_trade", world_map)}
        return self._deposit_catalogue_cache

    def deposits_listed(self, tiles: Iterable[str], resource_id: str, year: int,
                        found: Iterable[Mapping[str, Any]] = ()) -> List[Dict[str, Any]]:
        """The deposits of a resource a party holding these tiles can name: the catalogue's that were first worked by `year`,
        and the prospected deposits `found`."""
        return worked_deposits(tiles, resource_id, year, found, self.world_map)

    def deposits_worked_before(self, tiles: Iterable[str], resource_id: str, year: int,
                               rates: Optional[Mapping[str, float]] = None) -> Dict[str, Any]:
        """What the known deposits of a resource on these tiles had yielded by `year` (`rates`: the tonnes a year each was worked)."""
        return mined_before(tiles, resource_id, year, self.world_map, rates)

    def deposit_working_rate(self, size_tonnes: float) -> float:
        """The most a deposit of this size yields a year."""
        return working_rate_tonnes_per_year(size_tonnes, self.world_map)

    def prospect_finds(self, tile: str, resource_id: str, effort: float, seed: Any) -> List[Dict[str, Any]]:
        """The hidden deposits `effort` person-days find on a tile; the same seed and effort give the same finds."""
        return prospect(tile, resource_id, effort, seed, self.world_map)

    def tile_endowment(self, tile: str, resource_id: str) -> Dict[str, Any]:
        """What the tile holds of a resource, as the catalogue and the district's expectation give it."""
        return endowment(tile, resource_id, self.world_map)
