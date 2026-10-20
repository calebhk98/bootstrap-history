"""The engine's side of the disease wall: what the disease package reads from the simulation, and the yearly
step that hands its deaths, by age band, to `Population`.

The nation is one patch of three age bands (the demography module's bands). A pathogen reaches it from the
outside sources `civ["disease_exposure"]["outside_contact"]` names (map tiles where it lives, initial conditions
only): the chance falls with the fewest days of travel between the source's tiles and the tiles the nation holds,
over the routes its technologies and the outsiders' carriers open. When it arrives, who dies and when comes from
the model. Technology acts through `disease_effects` on node mechanics. Nothing here names a pathogen, a year or
a technology."""
import functools

from sim.refusal import LogLine

from sim.disease import api as disease
from . import externalities
from .units_prose import money_text
from sim.geography.api import endemic_people_loss, reach, tiles_held, usable_modes

nation, tuning = disease.nation, disease.nation_tuning
BANDS = tuning.BANDS
DISEASE_CARE_COLLAPSE_SENSITIVITY = tuning.DISEASE_CARE_COLLAPSE_SENSITIVITY
DISEASE_TRAVELLER_ANNUAL_CHANCE = tuning.DISEASE_TRAVELLER_ANNUAL_CHANCE
DISEASE_EMERGENCE_ANNUAL_CHANCE = tuning.DISEASE_EMERGENCE_ANNUAL_CHANCE
DISEASE_TRAVEL_DECAY_DAYS = tuning.DISEASE_TRAVEL_DECAY_DAYS
DISEASE_URBAN_DENSITY_RATIO = tuning.DISEASE_URBAN_DENSITY_RATIO

# below this share of working-age people dead, a seat notices nothing
EPIDEMIC_NOTICE_SHARE = 0.002


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

    def contact_sources(self):
        """The outside sources the civilisation says the pathogens come from (see `nation.contact_sources`)."""
        return nation.contact_sources(self._sim.civ.get("disease_exposure"))

    def seed_text(self):
        return "disease:%s:%d" % (self._sim.civ.get("id"), self._sim._farm_year_weather_seed(0, region="disease"))

    def travel_days(self, source):
        """The fewest days from the nearest of the source's tiles to a tile the nation holds, over the modes the
        nation's technologies open plus those the outsiders bring; None when no route joins them. Kept until the
        tiles held or the modes change."""
        sim = self._sim
        held = tuple(sorted(tiles_held(sim.civ, sim.world_map)))
        modes = tuple(sorted(set(usable_modes([sim.held_and_running()], sim.world_map)) | set(source["carrier_modes"])))
        cache = sim.__dict__.setdefault("_disease_travel_days", {})
        key = (held, modes, source["tiles"])
        if key not in cache:
            if len(cache) > 32:
                cache.clear()
            days = reach(held, modes, 1.0e9, world_map=sim.world_map) if held and source["tiles"] else {}
            cache[key] = min((days[tile] for tile in source["tiles"] if tile in days), default=None)
        return cache[key]

    def contact_weight(self, source):
        """The share of the source's contact the routes let through; one for a source that names no tiles."""
        return nation.contact_weight(self.travel_days(source)) if source["tiles"] else 1.0

    def introductions(self, records, year):
        """Pathogens that arrive this year: reachable from an open source, absent from the nation, and drawn."""
        chances = nation.arrival_chances(self.contact_sources(), year, self.contact_weight)
        return nation.introductions(records, chances, year, self.seed_text())

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
        return disease.technology_scales(
            pathogen_ids, [(spec, sim.civ_diffusion(node_id)) for node_id, spec in sim._effect_terms("disease_effects")])


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
        killed_before = dict(state.deaths)
        deaths = nation.run_year(
            pathogens(), state.records, state.introduced, state.deaths, world.people_by_band(), nutrition_ratio,
            self.civ.get("urban_fraction", 0.0), arrivals, world.seed_text(), year, fatality_factor=fatality_by_pathogen,
            transmission_scale=transmission, care_sensitivity=DISEASE_CARE_COLLAPSE_SENSITIVITY,
            density_ratio=DISEASE_URBAN_DENSITY_RATIO)
        self.__dict__["_epidemic_names"] = [pathogens()[pathogen_id].name for pathogen_id in sorted(state.deaths)
                                            if state.deaths[pathogen_id] > killed_before.get(pathogen_id, 0)]
        return deaths

    def epidemic_year(self, food_available_calories_per_day, year):
        """(epidemic deaths by band, disease burden, endemic death rates) for the year's population step: the
        epidemics run and cut each seat's staff before the burden and the endemic rates are read."""
        deaths = externalities.add_deaths(self.disease_year(food_available_calories_per_day, year), self, year)
        self.epidemic_hits_seats(deaths, year)
        return deaths, self._disease_burden(), self.endemic_death_rates()

    def epidemic_hits_seats(self, deaths_by_band, year):
        """Cut each playing seat's people and cash by the working-age share the year's epidemics killed; the reply
        is that share (zero when nothing was done)."""
        working_age = float(self.population.working_age)
        share = disease.working_age_death_share(deaths_by_band, working_age)
        if share < EPIDEMIC_NOTICE_SHARE:
            return 0.0
        names = self.__dict__.get("_epidemic_names") or ["an epidemic"]
        name = " and ".join(names)
        for seat_id in self.playing_seats():
            with self.act_as(seat_id):
                household = self.state.household
                people_before = household.scholars + household.artisans + sum(household.employees.values())
                staff_before = self.labour.staff_snapshot()
                self.apply_staff_survival(1 - share)
                household.directors_extra *= (1 - share)
                self.labour.log_staff_reduction(name, staff_before)
                cash = self.lose_capital(share * self.PLAGUE_CASH_LOSS_SHARE, "plague losses")
                parts = ["staff -%d%%" % round(share * 100)] if people_before > 0.05 else []
                if cash > 0.5:
                    parts.append("%s of takings lost while the trade stood idle" % money_text(cash, self, grouped=True))
                took_nothing = not parts
                household.log.append((year, LogLine(
                    "hazard_hit", "%s: %s. Empire-wide, %d%% of working-age people died" % (
                        name, ", ".join(parts) or "you had nothing it could take", round(share * 100)),
                    hazard=name, took_nothing=took_nothing, lapsed_hedges=[])))
        return share
