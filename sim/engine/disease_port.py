"""The engine's side of the disease wall: what the disease package reads from the simulation, and the yearly
step that hands its deaths, by age band, to `Population`.

The nation is one patch of three age bands (the demography module's bands). A pathogen reaches it through
`civ["disease_exposure"]["outside_contact"]`, a labelled temporary heuristic until the spatial stage derives
contact from routes. Technology acts through `disease_effects` on node mechanics. Nothing here names a
pathogen or a technology."""
import functools
import random

from sim.constants import declare
from sim.disease import api as disease
from sim.world import demography

BANDS = ("children", "working_age", "elderly")
AGE_VULNERABILITY = {"children": demography.STARVATION_VULNERABILITY_CHILD,
                     "working_age": demography.STARVATION_VULNERABILITY_WORKING_AGE,
                     "elderly": demography.STARVATION_VULNERABILITY_ELDERLY}
AGEING = {"children": ("working_age", 1.0 / demography.CHILD_BAND_WIDTH_YEARS),
          "working_age": ("elderly", 1.0 / demography.WORKING_AGE_BAND_WIDTH_YEARS)}
INTRODUCTION_BAND = "working_age"

DISEASE_CONTACT_ANNUAL_CHANCE = declare(
    "DISEASE_CONTACT_ANNUAL_CHANCE", 0.25, kind="temporary_heuristic",
    unit="dimensionless (chance per year, per listed pathogen, while it is not circulating)",
    source=None, confidence="D",
    why="Stands in for the outside world exporting infected travellers along routes: while a civilisation's "
        "outside-contact window is open and a listed pathogen is absent from the nation, one introduction "
        "happens with this chance each year, drawn from the disease package's own hash of the game's seed, "
        "never Sim.rng. Retired when the spatial stage carries infected people over geography routes.")
DISEASE_CONTACT_INFECTED_PEOPLE = declare(
    "DISEASE_CONTACT_INFECTED_PEOPLE", 10, kind="temporary_heuristic", unit="people", source=None, confidence="D",
    why="Infected working-age people an introduction brings. Stands in for the traveller flux the spatial stage "
        "derives; an arrival of a few people dies out by chance in a small share of draws, which the chain-binomial "
        "step produces by itself.")
AGE_FATALITY_FROM_STARVATION_VULNERABILITY = declare(
    "AGE_FATALITY_FROM_STARVATION_VULNERABILITY", 1.0, kind="temporary_heuristic",
    unit="dimensionless (exponent of the band's starvation vulnerability in its relative case fatality)",
    source=None, confidence="D",
    why="A pathogen's case fatality is one number for the whole population. Its split across bands reuses the "
        "demography module's relative vulnerability of children, working-age adults and the elderly (sourced for "
        "famine, direction supported for epidemic disease, magnitude borrowed), rescaled so the population-weighted "
        "mean stays the pathogen's own figure. The nutrition shortfall multiplies it by the same curve baseline "
        "mortality uses. Replaced by per-band fatality in the pathogen files when sourced.")


@functools.lru_cache(maxsize=1)
def pathogens():
    return disease.load_pathogens()


class DiseaseWorld:
    """What the disease step reads from one simulation."""

    def __init__(self, sim):
        self._sim = sim

    @property
    def population(self):
        return self._sim.population

    def people_by_band(self):
        return {band: float(getattr(self.population, band)) for band in BANDS}

    def contact_windows(self):
        """[(pathogen ids, first year, last year)] the civilisation says the outside world reaches it in."""
        exposure = self._sim.civ.get("disease_exposure") or {}
        return [(tuple(entry["pathogens"]), entry["years"][0], entry["years"][1])
                for entry in exposure.get("outside_contact", ())]

    def seed_text(self):
        return "disease:%s:%d" % (self._sim.civ.get("id"), self._sim._farm_year_weather_seed(0, region="disease"))

    def introductions(self, records, year):
        """Pathogens that arrive this year: listed in an open window, absent from the nation, and drawn."""
        arrivals = []
        for pathogen_ids, first_year, last_year in self.contact_windows():
            if not first_year <= year <= last_year:
                continue
            for pathogen_id in pathogen_ids:
                if disease.is_circulating(records, pathogen_id):
                    continue
                draw = random.Random("%s:contact:%s:%d" % (self.seed_text(), pathogen_id, year)).random()
                if draw < DISEASE_CONTACT_ANNUAL_CHANCE:
                    arrivals.append(pathogen_id)
        return arrivals

    def fatality_scale_by_band(self, nutrition_ratio):
        """Each band's multiplier on a pathogen's case fatality: its relative vulnerability, rescaled to a
        population-weighted mean of one, times the shortfall of food it is living through."""
        people = self.people_by_band()
        total = sum(people.values())
        weight = {band: AGE_VULNERABILITY[band] ** AGE_FATALITY_FROM_STARVATION_VULNERABILITY for band in BANDS}
        mean = sum(people[band] * weight[band] for band in BANDS) / total if total > 0 else 1.0
        return {band: weight[band] / mean * demography.nutrition_mortality_multiplier(nutrition_ratio, AGE_VULNERABILITY[band])
                for band in BANDS}

    def technology_scales(self, pathogen_ids):
        """({pathogen id: multiplier on case fatality}, {pathogen id: multiplier on transmission}) from the
        `disease_effects` of the technologies the nation has taken up (the share of the country that holds
        a node scales how much of its relief applies)."""
        sim = self._sim
        fatality = {pathogen_id: 1.0 for pathogen_id in pathogen_ids}
        transmission = dict(fatality)
        for node_id, spec in sim._effect_terms("disease_effects"):
            reach = sim.civ_diffusion(node_id)
            if reach <= 0.0:
                continue
            target = fatality if spec["acts_on"] == "case_fatality" else transmission
            for pathogen_id in spec.get("pathogens") or pathogen_ids:
                if pathogen_id in target:
                    target[pathogen_id] *= 1.0 - (1.0 - spec["factor"]) * reach
        return fatality, transmission


class DiseasePortMixin:
    """Gives `Sim` its yearly disease step. The state is `self.state.disease` (saved with the game)."""

    def disease_year(self, food_available_calories_per_day, year=None):
        """Run the year's epidemics and return `{band: deaths}` for `Population.step(epidemic_deaths=...)`.

        Call after agriculture has set this year's food and before `Population.step`. Does nothing, at no cost,
        for a civilisation that lists no outside contact and has no epidemic under way."""
        world = DiseaseWorld(self)
        state = self.state.disease
        year = self.year if year is None else year
        arrivals = world.introductions(state.records, year)
        if not arrivals and not state.records:
            return {}
        known = pathogens()
        nutrition_ratio = self.population.nutrition_ratio(food_available_calories_per_day)
        pathogen_ids = sorted(set(state.records) | set(arrivals))
        fatality_by_pathogen, transmission = world.technology_scales(pathogen_ids)
        result = disease.advance_year(
            known, state.records, world.people_by_band(), world.seed_text(), introductions=arrivals,
            introduction_band=INTRODUCTION_BAND, introduction_size=DISEASE_CONTACT_INFECTED_PEOPLE, ageing=AGEING,
            fatality_scale=world.fatality_scale_by_band(nutrition_ratio), transmission_scale=transmission,
            fatality_factor=fatality_by_pathogen)
        for pathogen_id in result.introduced:
            state.introduced.setdefault(pathogen_id, []).append(year)
        for pathogen_id, deaths in result.deaths_by_pathogen.items():
            state.deaths[pathogen_id] = state.deaths.get(pathogen_id, 0) + sum(deaths.values())
        return {band: float(count) for band, count in result.deaths_by_band.items()}
