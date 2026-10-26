"""The engine's side of the disease wall: what the disease package reads from the simulation, and the yearly
step that hands its deaths, by age band, to `Population`.

The nation is a metapopulation: one patch of three age bands (the demography module's bands) per tile held,
infection passing between tiles by the traffic between them (`sim/disease/metapopulation.py`). A pathogen reaches
it from the outside sources `civ["disease_exposure"]["outside_contact"]` names (map tiles where it lives, initial
conditions only): the chance falls with the fewest days of travel between the source's tiles and the tiles the
nation holds, over the routes its technologies and the outsiders' carriers open, and it enters at the held tile
those routes reach first. Pathogens `civ["disease_exposure"]["endemic"]` names are already in the people at the
start, at the immune state their own numbers imply. When one spreads, who dies and when comes from the model. Technology acts through `disease_effects` on node mechanics. Nothing here names a pathogen, a year or
a technology."""
import functools


from sim.disease import api as disease
from . import externalities
from .units_prose import money_text
from sim.geography.api import endemic_people_loss, reach, settlement, tile_facts, tiles_held, usable_modes
from sim.reporting.api import RecordEvent

nation, tuning, spread = disease.nation, disease.nation_tuning, disease.metapopulation
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

    def held_tiles(self):
        """The tiles the nation holds, sorted."""
        sim = self._sim
        held = sim.home_tiles_held() if hasattr(sim, "home_tiles_held") else tiles_held(sim.civ, sim.world_map)
        return sorted(held)

    def people_by_tile(self):
        """{tile: {band: people}} over the tiles held: the regions the engine tracks once they cover the tiles,
        else the nation's bands shared by each tile's share of the land's food."""
        sim = self._sim
        held = self.held_tiles()
        stored = sim.view("regional_people")()
        if stored and sorted(stored) == settlement.tile_ids(held):
            return {tile: dict(zip(BANDS, stored[tile])) for tile in held}
        shares = settlement.population_shares(held)
        national = self.people_by_band()
        return {tile: {band: national[band] * shares.get(tile, 0.0) for band in BANDS} for tile in held}

    def area_by_tile(self):
        return {tile: tile_facts(tile, self._sim.world_map)["land_area_km2"] for tile in self.held_tiles()}

    def crowding_by_tile(self, people_by_tile):
        """{tile: crowding}: density over the people-weighted mean, times the nation's crowding index."""
        return spread.crowding_by_tile(people_by_tile, self.area_by_tile(), self.crowding_index())

    def trips(self, people_by_tile):
        """{(tile, tile): trips in a year} between the tiles: the crews of last year's carried goods, last year's
        migrants and the everyday travel between bordering tiles."""
        sim = self._sim
        held = self.held_tiles()
        borders = settlement.borders_among(held, sim.world_map)
        local_borders = spread.borders_through_empty(people_by_tile, borders)
        carried = sim._domestic_flow_ledger() if hasattr(sim, "_domestic_flow_ledger") else {}
        flows = getattr(sim, "_last_regional_step", None) or {}
        emigrants = {tile: flow.emigration for tile, flow in flows.items()}
        immigrants = {tile: flow.immigration for tile, flow in flows.items()}
        return spread.add_trips(spread.trade_trips(carried, held), spread.migrant_trips(emigrants, immigrants, borders),
                                spread.local_trips(people_by_tile, local_borders))

    def contacts(self, people_by_tile):
        return spread.contacts_from_trips(self.trips(people_by_tile), people_by_tile)

    def entry(self, source):
        """{held tile: fewest days} from the nearest of the source's tiles, over the modes the nation's
        technologies open plus those the outsiders bring; empty when no route joins them. Kept until the tiles
        held or the modes change."""
        sim = self._sim
        held = tuple(self.held_tiles())
        modes = tuple(sorted(set(usable_modes([sim.held_and_running()], sim.world_map)) | set(source["carrier_modes"])))
        cache = sim.__dict__.setdefault("_disease_entry", {})
        key = (held, modes, source["tiles"])
        if key not in cache:
            if len(cache) > 32:
                cache.clear()
            days = reach(source["tiles"], modes, 1.0e9, world_map=sim.world_map) if held and source["tiles"] else {}
            cache[key] = {tile: days[tile] for tile in held if tile in days}
        return cache[key]

    def travel_days(self, source):
        reached = self.entry(source)
        return min(reached.values()) if reached else None

    def contact_weight(self, source):
        """The share of the source's contact the routes let through; one for a source that names no tiles."""
        return nation.contact_weight(self.travel_days(source)) if source["tiles"] else 1.0

    def entry_tiles(self, arrivals, year, people_by_tile, contacts):
        """{arriving pathogen: [tiles it enters at]}: of the open sources, the one with the most contact; the
        populated held tile its routes reach first in each group of tiles the traffic joins, so long as the group
        is within one travel-decay distance of the soonest reached (a source naming no tiles enters at the most
        populous tile)."""
        populated = {tile for tile, bands in people_by_tile.items() if sum(bands.values()) > 0.0}
        busiest = max(sorted(people_by_tile), key=lambda tile: sum(people_by_tile[tile].values()), default=None)
        groups = [[tile for tile in group if tile in populated] for group in spread.components(contacts, set(people_by_tile))]
        entered = {}
        for pathogen_id in arrivals:
            best = None
            for source in self.contact_sources():
                if pathogen_id not in source["pathogens"] or (
                        source["first_year"] is not None and not source["first_year"] <= year <= source["last_year"]):
                    continue
                weight = self.contact_weight(source)
                days = {tile: days for tile, days in self.entry(source).items() if tile in populated}
                tiles = spread.entry_tiles(days, groups, DISEASE_TRAVEL_DECAY_DAYS) if source["tiles"] else [busiest]
                if weight > 0.0 and tiles and (best is None or weight > best[0]):
                    best = (weight, tiles)
            entered[pathogen_id] = best[1] if best else [busiest]
        return entered

    def endemic_pathogens(self):
        """The pathogens the civilisation's people already carry at the start (initial conditions)."""
        return tuple(sorted((self._sim.civ.get("disease_exposure") or {}).get("endemic", ())))

    def introductions(self, records, year):
        """Pathogens that arrive this year: reachable from an open source, absent from the nation, and drawn."""
        chances = nation.arrival_chances(self.contact_sources(), year, self.contact_weight)
        return [pathogen_id for pathogen_id in nation.introductions({}, chances, year, self.seed_text())
                if not spread.is_circulating(records, pathogen_id)]

    def crowding_index(self):
        """The person-weighted density of the nation relative to a rural settlement."""
        return nation.crowding_index(self._sim.urban_fraction(), DISEASE_URBAN_DENSITY_RATIO)

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
        """Run the year's epidemics and return `{band: deaths}` for `Population.step(epidemic_deaths=...)`; the
        same deaths by tile are left in `epidemic_deaths_by_tile`.

        Call after agriculture has set this year's food and before `Population.step`. Does nothing, at no cost,
        for a civilisation that lists no outside contact, no endemic pathogen and has no epidemic under way."""
        world = DiseaseWorld(self)
        state = self.state.disease
        year = self.year if year is None else year
        self.__dict__.pop("_epidemic_forecast", None)
        arrivals = world.introductions(state.records, year)
        endemic = world.endemic_pathogens()
        if not arrivals and not state.records and not endemic:
            self.__dict__["_epidemic_deaths_by_tile"] = {}
            return {}
        nutrition_ratio = self.population.nutrition_ratio(food_available_calories_per_day)
        people = world.people_by_tile()
        pathogen_ids = sorted(set(state.records) | set(arrivals) | set(endemic))
        fatality_by_pathogen, transmission = world.technology_scales(pathogen_ids)
        killed_before = dict(state.deaths)
        contacts = world.contacts(people)
        by_tile = spread.run_year(
            pathogens(), state.records, state.introduced, state.deaths, people, contacts,
            world.crowding_by_tile(people), world.fatality_scale_by_band(nutrition_ratio),
            world.entry_tiles(arrivals, year, people, contacts), world.seed_text(), year, fatality_factor=fatality_by_pathogen,
            transmission_scale=transmission, care_sensitivity=DISEASE_CARE_COLLAPSE_SENSITIVITY, endemic=endemic)
        self.__dict__["_epidemic_deaths_by_tile"] = by_tile
        self.__dict__["_epidemic_names"] = [pathogens()[pathogen_id].name for pathogen_id in sorted(state.deaths)
                                            if state.deaths[pathogen_id] > killed_before.get(pathogen_id, 0)]
        return spread.deaths_by_band(by_tile)

    def epidemic_deaths_by_tile(self):
        """{tile: {band: deaths}} the last disease year killed."""
        return self.__dict__.get("_epidemic_deaths_by_tile") or {}

    def epidemic_forecast(self, food_available_calories_per_day=None):
        """The model's own forecast of the coming year from the infections now and the contact between tiles,
        with no new arrival: {"expected_deaths", "expected_working_age_share", "by_pathogen": [{pathogen, name,
        infected, expected_deaths}], "expected_deaths_by_tile": {tile: {band: deaths}}, "arrival_chances":
        {pathogen: chance of reaching the nation this year}}. Nothing is drawn and nothing changes; kept until the
        next disease year."""
        cached = self.__dict__.get("_epidemic_forecast")
        if cached is not None:
            return cached
        world = DiseaseWorld(self)
        state = self.state.disease
        year = self.year
        people = world.people_by_tile()
        by_pathogen, by_tile = [], {}
        if state.records:
            nutrition_ratio = (self.population.nutrition_ratio(food_available_calories_per_day)
                               if food_available_calories_per_day is not None else 1.0)
            fatality_by_pathogen, transmission = world.technology_scales(sorted(state.records))
            forecast = spread.forecast_year(
                pathogens(), state.records, people, world.contacts(people), world.crowding_by_tile(people),
                world.fatality_scale_by_band(nutrition_ratio), world.seed_text(), year,
                fatality_factor=fatality_by_pathogen, transmission_scale=transmission)
            for pathogen_id, row in forecast.items():
                killed = sum(sum(bands.values()) for bands in row["expected_deaths_by_tile"].values())
                by_pathogen.append({"pathogen": pathogen_id, "name": pathogens()[pathogen_id].name,
                                    "infected": row["infected"], "expected_deaths": round(killed)})
                for tile, bands in row["expected_deaths_by_tile"].items():
                    for band, count in bands.items():
                        by_tile.setdefault(tile, {}).setdefault(band, 0.0)
                        by_tile[tile][band] += count
        expected = spread.deaths_by_band(by_tile)
        chances = nation.arrival_chances(world.contact_sources(), year, world.contact_weight)
        result = {"expected_deaths": round(sum(expected.values())),
                  "expected_working_age_share": disease.working_age_death_share(expected, float(self.population.working_age)),
                  "by_pathogen": by_pathogen, "expected_deaths_by_tile": by_tile,
                  "arrival_chances": {pathogen_id: round(chance, 4) for pathogen_id, chance in sorted(chances.items())
                                      if not spread.is_circulating(state.records, pathogen_id)}}
        self.__dict__["_epidemic_forecast"] = result
        return result

    def regional_disease_loss(self, tile):
        """The share of a working-age person on `tile` the diseases there take in a year: the endemic death rate
        of the tile's land plus the model's forecast of this year's epidemics on it (the nation's share on a tile it
        does not hold, where no infection is followed). Over a year, so a party's losses on arrival follow from it."""
        endemic = endemic_people_loss([tile], self.world_map).get("working_age", 0.0)
        forecast = self.epidemic_forecast()
        people = DiseaseWorld(self).people_by_tile()
        if tile in people:
            working_age = people[tile]["working_age"]
            killed = forecast["expected_deaths_by_tile"].get(tile, {}).get("working_age", 0.0)
            epidemic = killed / working_age if working_age > 0.0 else 0.0
        else:
            epidemic = forecast["expected_working_age_share"]
        return min(1.0, endemic + epidemic)

    def frontier_disease_loss(self):
        """The mean `regional_disease_loss` over the tiles held that border a tile not held: where a campaign
        in the field meets the country's neighbours."""
        held = set(DiseaseWorld(self).held_tiles())
        borders = settlement.borders_among(sorted(held), self.world_map)
        frontier = [tile for tile in sorted(held) if any(other not in held for other in borders.get(tile, ()))]
        if not frontier:
            return 0.0
        return sum(self.regional_disease_loss(tile) for tile in frontier) / len(frontier)

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
                self.send(RecordEvent.in_year(year, "hazard_hit", "%s: %s. Empire-wide, %d%% of working-age people died" % (
                        name, ", ".join(parts) or "you had nothing it could take", round(share * 100)), hazard=name, took_nothing=took_nothing, lapsed_hedges=[]))
        return share
