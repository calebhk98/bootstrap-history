"""The yearly disease step: who is infected, who dies, and the deaths by band the population step takes."""
import functools

from . import metapopulation as spread, nation_tuning as tuning
from .loader import load_pathogens


@functools.lru_cache(maxsize=1)
def pathogens():
    return load_pathogens()


class Epidemics:

    def run_epidemic_year(self, command):
        """Run the year's epidemics and answer `{band: deaths}` for the population step; the same deaths by tile are
        left in `epidemic_deaths_by_tile`. Does nothing, at no cost, for a civilisation that lists no outside contact,
        no endemic pathogen and has no epidemic under way. Called after agriculture has set this year's food and before
        the population step."""
        state = self.world
        year = command.year
        self._forecast = None
        arrivals = self.introductions(state.records, year)
        endemic = self.endemic_pathogens()
        if not arrivals and not state.records and not endemic:
            self._deaths_by_tile = {}
            self.bump("epidemics")
            return {}
        nutrition_ratio = self.needs.nutrition_ratio(command.food_kcal_per_day)
        people = self.people_by_tile()
        pathogen_ids = sorted(set(state.records) | set(arrivals) | set(endemic))
        fatality_by_pathogen, transmission = self.technology_scales(pathogen_ids)
        killed_before = dict(state.deaths)
        contacts = self.contacts(people)
        by_tile = spread.run_year(
            pathogens(), state.records, state.introduced, state.deaths, people, contacts,
            self.crowding_by_tile(people), self.fatality_scale_by_band(nutrition_ratio),
            self.entry_tiles(arrivals, year, people, contacts), self.seed_text(), year, fatality_factor=fatality_by_pathogen,
            transmission_scale=transmission, care_sensitivity=tuning.DISEASE_CARE_COLLAPSE_SENSITIVITY, endemic=endemic)
        self._deaths_by_tile = by_tile
        self._names = [pathogens()[pathogen_id].name for pathogen_id in sorted(state.deaths)
                       if state.deaths[pathogen_id] > killed_before.get(pathogen_id, 0)]
        self.bump("epidemics")
        return spread.deaths_by_band(by_tile)

    def epidemic_deaths_by_tile(self):
        """{tile: {band: deaths}} the last disease year killed."""
        return self._deaths_by_tile or {}
