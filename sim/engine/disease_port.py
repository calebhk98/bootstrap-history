"""The engine's side of the disease wall: what the disease package reads from the simulation, and the yearly
step that hands its deaths, by age band, to `Population`.

The nation is one patch of three age bands (the demography module's bands). A pathogen reaches it through
`civ["disease_exposure"]["outside_contact"]`, a labelled temporary heuristic until the spatial stage derives
contact from routes. Technology acts through `disease_effects` on node mechanics. Nothing here names a
pathogen or a technology."""
import functools

from sim.disease import api as disease
from sim.geography.api import endemic_people_loss, tiles_held

nation, tuning = disease.nation, disease.nation_tuning
BANDS = tuning.BANDS
DISEASE_CARE_COLLAPSE_SENSITIVITY = tuning.DISEASE_CARE_COLLAPSE_SENSITIVITY
DISEASE_CONTACT_ANNUAL_CHANCE = tuning.DISEASE_CONTACT_ANNUAL_CHANCE
DISEASE_URBAN_DENSITY_RATIO = tuning.DISEASE_URBAN_DENSITY_RATIO


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
        return nation.contact_windows(self._sim.civ.get("disease_exposure"))

    def seed_text(self):
        return "disease:%s:%d" % (self._sim.civ.get("id"), self._sim._farm_year_weather_seed(0, region="disease"))

    def introductions(self, records, year):
        """Pathogens that arrive this year: listed in an open window, absent from the nation, and drawn."""
        return nation.introductions(records, self.contact_windows(), year, self.seed_text(), DISEASE_CONTACT_ANNUAL_CHANCE)

    def crowding_index(self):
        """The person-weighted density of the nation relative to a rural settlement."""
        return nation.crowding_index(self._sim.civ.get("urban_fraction", 0.0), DISEASE_URBAN_DENSITY_RATIO)

    def fatality_scale_by_band(self, nutrition_ratio):
        """Each band's multiplier on a pathogen's case fatality (see `nation.fatality_scale_by_band`)."""
        return nation.fatality_scale_by_band(self.people_by_band(), nutrition_ratio)

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

    def endemic_death_rates(self):
        """{band: excess deaths per head per year} from the endemic diseases of the tiles the nation holds."""
        return endemic_people_loss(tiles_held(self.civ, self.world_map), self.world_map)

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
        nutrition_ratio = self.population.nutrition_ratio(food_available_calories_per_day)
        pathogen_ids = sorted(set(state.records) | set(arrivals))
        fatality_by_pathogen, transmission = world.technology_scales(pathogen_ids)
        return nation.run_year(
            pathogens(), state.records, state.introduced, state.deaths, world.people_by_band(), nutrition_ratio,
            self.civ.get("urban_fraction", 0.0), arrivals, world.seed_text(), year, fatality_factor=fatality_by_pathogen,
            transmission_scale=transmission, care_sensitivity=DISEASE_CARE_COLLAPSE_SENSITIVITY,
            density_ratio=DISEASE_URBAN_DENSITY_RATIO)
