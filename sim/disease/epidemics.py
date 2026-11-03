"""The yearly disease step: who is infected, who dies, and the deaths by band the population step takes."""
import functools

from sim.assembly.api import Part

from . import metapopulation as spread, nation_tuning as tuning
from .loader import load_pathogens


@functools.lru_cache(maxsize=1)
def pathogens():
    return load_pathogens()


class Epidemics(Part):

    def __init__(self, module):
        super().__init__(module)
        self._deaths_by_tile = None  # the last disease year's deaths by tile; empty after a load, as the engine's was
        self.names = None            # the pathogens that killed in the last disease year

    def run_epidemic_year(self, command):
        """Run the year's epidemics and answer `{band: deaths}` for the population step; the same deaths by tile are
        left in `epidemic_deaths_by_tile`. Does nothing, at no cost, for a civilisation that lists no outside contact,
        no endemic pathogen and has no epidemic under way. Called after agriculture has set this year's food and before
        the population step."""
        state = self.world
        year = command.year
        self.parts.forecast.forget()
        arrivals = self.parts.contact.introductions(state.records, year)
        endemic = self.parts.contact.endemic_pathogens()
        if not arrivals and not state.records and not endemic:
            self._deaths_by_tile = {}
            self.bump("epidemics")
            return {}
        nutrition_ratio = self.needs.nutrition_ratio(command.food_kcal_per_day)
        people = self.parts.people.people_by_tile()
        pathogen_ids = sorted(set(state.records) | set(arrivals) | set(endemic))
        fatality_by_pathogen, transmission = self.parts.contact.technology_scales(pathogen_ids)
        killed_before = dict(state.deaths)
        contacts = self.parts.people.contacts(people)
        by_tile = spread.run_year(
            pathogens(), state.records, state.introduced, state.deaths, people, contacts,
            self.parts.people.crowding_by_tile(people), self.parts.people.fatality_scale_by_band(nutrition_ratio),
            self.parts.contact.entry_tiles(arrivals, year, people, contacts), self.parts.contact.seed_text(), year, fatality_factor=fatality_by_pathogen,
            transmission_scale=transmission, care_sensitivity=tuning.DISEASE_CARE_COLLAPSE_SENSITIVITY, endemic=endemic)
        self._deaths_by_tile = by_tile
        self.names = [pathogens()[pathogen_id].name for pathogen_id in sorted(state.deaths)
                       if state.deaths[pathogen_id] > killed_before.get(pathogen_id, 0)]
        self.bump("epidemics")
        return spread.deaths_by_band(by_tile)

    def epidemic_deaths_by_tile(self):
        """{tile: {band: deaths}} the last disease year killed."""
        return self._deaths_by_tile or {}
