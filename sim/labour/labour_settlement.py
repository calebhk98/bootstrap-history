"""Where the household lives: its base tile, the town there, and how far a hire will travel to it.

The town's people come from the tile's share of the nation, so a smaller nation means a smaller town and a
poorer tile means a smaller town."""
from sim.constants import declare
import sim.geography.api as geography
from sim.geography.api import settlement


class Settlement:
    def __init__(self, world):
        self._world = world

    TOWN_MAX_SHARE_OF_TILE = declare(
        "TOWN_MAX_SHARE_OF_TILE", 0.5, kind="temporary_heuristic",
        unit="fraction of a tile's people", source=None, confidence="D",
        why="Largest share of a tile's people that can live in its one "
            "market town. Keeps the town inside the tile's headcount, and so "
            "inside the nation's; the share itself is tuned, not measured.")

    def held_tiles(self):
        """The tiles this nation holds."""
        return tuple(self._world.people.home_tiles_held())

    def settlement_tiles(self):
        """{tile id: people living there} for the tiles this nation holds: the regions' people once tracked, else
        the nation spread by food potential."""
        tracked = self._world.people.people_by_tile()
        if tracked is not None:
            return tracked
        homes = self.held_tiles()
        total = self._world.people.population.total
        return {tile: total * settlement.population_share(homes, tile)
                for tile in settlement.tile_ids(homes)}

    def base_tile(self):
        """The tile the household operates from."""
        chosen = self._world.workforce.base_tile
        homes = self.held_tiles()
        if chosen and chosen in settlement.tile_ids(homes):
            return chosen
        return settlement.default_base_tile(homes)

    def _town_population_at(self, tile):
        """People in `tile`'s town: a set share of the tile's own people (demography's count, `settlement_tiles`), or what a
        registered town provider says, capped at the tile's people."""
        tile_people = self.settlement_tiles().get(tile, 0.0)
        nominal = tile_people * self.TOWN_MAX_SHARE_OF_TILE
        provided = self._world.people.provided_town_population(tile, nominal)
        return nominal if provided is None else min(provided, tile_people)

    def town_mortality_premium_by_tile(self):
        """{tile: premium} for the tiles whose town carries a mortality premium from a registered provider: the premium
        of the town's people averaged over all the tile's people (a share of the baseline death rate). Empty with
        no provider."""
        if not self._world.people.has_town_premiums():
            return {}
        found = {}
        for tile, people in sorted(self.settlement_tiles().items()):
            town = self._town_population_at(tile)
            premium = self._world.people.provided_mortality_premium(tile, town)
            if premium and town > 0.0 and people > 0.0:
                found[tile] = premium * min(1.0, town / people)
        return found

    def home_town_population_estimate(self):
        """People in the base's town."""
        return self._town_population_at(self.base_tile())

    def held_technologies(self):
        """Technologies this actor's people can travel with: the civilisation's own and those built."""
        return frozenset(self._world.knowledge.held_and_running())

    def travel_days_to_tile(self, tile):
        """Days the household needs to reach `tile` by the fastest route over the modes its people hold
        (geography's route over the ways built, weighted by time); None when no route joins the tiles."""
        held = self.held_technologies()
        found = geography.route([self.base_tile()], [tile], geography.usable_modes([held]),
                                self._world.scenario.built_ways(), held_nodes=held, fastest=True)
        return None if found is None else found["days"]
