"""Where the nation's townspeople live and how many (Complaint 603).

A region's town is bounded by the food its farms grow beyond their own households' need plus what it can draw from other
regions' farms at the carriage cost of grain over land, river and sea (`sim/world/urban_share.py`). The opening seeds how
much of each region's people live in town from the civilisation's `urban_fraction` (an initial condition), shared out by
what each region's town can feed; afterwards a region's townspeople are that share of its people, never more than its
town can feed. `urban_fraction()` is the one reading of the national share; no other code reads the civilisation's figure.
"""
from typing import Dict

from sim.geography import api as geography
from sim.geography.api import settlement
from sim.world import agriculture, urban_share

URBAN_SHARE_BAND_KEYS = ("low", "high", "threshold", "source", "confidence")


class UrbanShareMixin:

    def _people_for_urban_share(self) -> Dict[str, float]:
        tracked = self.people_by_tile()
        if tracked is not None:
            return tracked
        homes = self.home_tiles_held()
        return {tile: self.population.total * settlement.population_share(homes, tile)
                for tile in settlement.tile_ids(homes)}

    def urban_ceilings(self) -> Dict[str, float]:
        """{tile: people its town can feed}: the farms' surplus there plus what is carried in, kept for the year."""
        held = self.labour.held_technologies()
        improvements = self.state.economy.improvements
        key = (self.state.scenario.year, self.population.total, tuple(self.home_tiles_held()), held, len(improvements),
               sum(map(sum, self.state.population.regions.values())))
        cache = self.__dict__.setdefault("_urban_ceilings_cache", {})
        if key not in cache:
            cache.clear()
            cache[key] = self._computed_urban_ceilings(self._people_for_urban_share(), held, improvements)
        return cache[key]

    def _computed_urban_ceilings(self, people, held, improvements) -> Dict[str, float]:
        technique = self.labour._farming_technique()
        hectares_per_worker = agriculture.hectares_cropped_per_farm_worker(technique.crop, technique.toolkit)
        need = geography.parameter_value("food_kcal_per_person_year")
        working_share = self.population.working_age / self.population.total if self.population.total > 0.0 else 0.0
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
        modes = geography.usable_modes([held])
        towns = sorted(people)
        carriage = {tile: geography.route_costs([tile], modes, improvements, None, None, held, None, towns)
                    for tile in towns if surplus[tile] > 0.0}
        return urban_share.town_ceilings(surplus, carriage, tonne_hours)

    def urban_people_by_tile(self) -> Dict[str, float]:
        """{tile: people living in town}: the region's opening share of its people in town, never more than its town can feed."""
        people = self._people_for_urban_share()
        ceilings = self.urban_ceilings()
        stored = self.state.population.urban_share_of_people
        if sorted(stored) != sorted(people):
            stored = self.state.population.urban_share_of_people = urban_share.opening_shares(
                people, ceilings, float(self.civ.get("urban_fraction", 0.0)))
        return {tile: min(ceilings.get(tile, 0.0), tile_people, stored[tile] * tile_people)
                for tile, tile_people in sorted(people.items())}

    def urban_fraction(self) -> float:
        """Share of the nation's people living in town, from its regions."""
        total = self.population.total
        if total <= 0.0:
            return 0.0
        return min(1.0, sum(self.urban_people_by_tile().values()) / total)
