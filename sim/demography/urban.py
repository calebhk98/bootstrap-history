"""Where the nation's townspeople live and how many (Complaint 603).

A region's town is bounded by the food its farms grow beyond their own households' need plus what it can draw from other
regions' farms at the carriage cost of grain over land, river and sea (`sim/world/urban_share.py`). The opening seeds how
much of each region's people live in town from the civilisation's `urban_fraction` (an initial condition), shared out by
what each region's town can feed; afterwards a region's townspeople are that share of its people, never more than its
town can feed. `urban_fraction` is the one reading of the national share; no other code reads the civilisation's figure."""
from typing import Dict

from sim.geography.api import parameter_value, route_costs, settlement, usable_modes
from sim.world import agriculture, urban_share


class Urban:

    def people_for_urban_share(self) -> Dict[str, float]:
        tracked = self.people_by_tile()
        if tracked is not None:
            return tracked
        homes = self.needs.home_tiles_held()
        return {tile: self._bands().total * settlement.population_share(homes, tile)
                for tile in settlement.tile_ids(homes)}

    def urban_ceilings(self) -> Dict[str, float]:
        """{tile: people its town can feed}: the farms' surplus there plus what is carried in, kept for the year."""
        held = frozenset(self.needs.held_techniques(True))
        improvements = self.needs.built_ways()
        key = (self.needs.year(), self._bands().total, tuple(self.needs.home_tiles_held()), held, len(improvements),
               sum(map(sum, self.world.regions.values())))
        if key not in self._urban_ceilings_cache:
            self._urban_ceilings_cache.clear()
            self._urban_ceilings_cache[key] = self._computed_urban_ceilings(self.people_for_urban_share(), held, improvements)
        return self._urban_ceilings_cache[key]

    def _computed_urban_ceilings(self, people, held, improvements) -> Dict[str, float]:
        technique = self.needs.farming_technique()
        hectares_per_worker = agriculture.hectares_cropped_per_farm_worker(technique.crop, technique.toolkit)
        need = parameter_value("food_kcal_per_person_year")
        bands = self._bands()
        working_share = bands.working_age / bands.total if bands.total > 0.0 else 0.0
        grain_kcal_per_tonne = settlement.reference_kcal_per_tonne()
        surplus, tonne_hours = {}, {}
        for tile, tile_people in people.items():
            cropped = settlement.cropped_hectares(tile)
            food = settlement.capacity_kcal_per_year(tile)
            workers_wanted = cropped / hectares_per_worker
            if tile_people <= 0.0 or cropped <= 0.0 or food <= 0.0 or working_share <= 0.0:
                surplus[tile], tonne_hours[tile] = 0.0, 0.0
                continue
            kcal_per_worker = food / workers_wanted
            surplus[tile] = urban_share.farm_surplus_people(
                min(workers_wanted, tile_people * working_share), kcal_per_worker, 1.0 / working_share, need)
            tonne_hours[tile] = (agriculture.ANNUAL_LABOUR_HOURS_PER_FARM_WORKER * grain_kcal_per_tonne
                                 / kcal_per_worker)
        modes = usable_modes([held])
        towns = sorted(people)
        carriage = {tile: route_costs([tile], modes, improvements, None, None, held, None, towns)
                    for tile in towns if surplus[tile] > 0.0}
        return urban_share.town_ceilings(surplus, carriage, tonne_hours)

    def urban_people_by_tile(self) -> Dict[str, float]:
        """{tile: people living in town}: the region's opening share of its people in town, never more than its town can
        feed. The first read of a tile set seeds the shares from the civilisation's typed figure (a read that writes: the
        moment of that first read fixes the opening shares)."""
        people = self.people_for_urban_share()
        ceilings = self.urban_ceilings()
        stored = self.world.urban_share_of_people
        if sorted(stored) != sorted(people):
            stored = self.world.urban_share_of_people = urban_share.opening_shares(
                people, ceilings, float(self.needs.civilisation().get("urban_fraction", 0.0)))
        return {tile: min(ceilings.get(tile, 0.0), tile_people, stored[tile] * tile_people)
                for tile, tile_people in sorted(people.items())}

    def urban_fraction(self) -> float:
        """Share of the nation's people living in town, from its regions."""
        total = self._bands().total
        if total <= 0.0:
            return 0.0
        return min(1.0, sum(self.urban_people_by_tile().values()) / total)
