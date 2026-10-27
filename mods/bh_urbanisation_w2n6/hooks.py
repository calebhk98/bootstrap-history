"""Urbanisation model on land tiles: where non-farm people can live and what living there costs.

For each tile the nation holds, the town is what two drivers allow; nothing is a fixed city size:
  food reach  the farm surplus of every tile within a haul of the town, shared with the other towns that reach it;
  jobs        the people of non-farm households, placed on tiles in proportion to the food they can assemble,
              plus the dependants of the founder's own non-farm employees at the base tile.
Costs fall out of physical quantities: water at the WHO basic-access level, housing volume from the tile's climate,
and a disease premium on mortality that grows with crowding and shrinks as the water and sanitation technologies
the engine already counts (its disease burden) are held. Each year a phase stores every tile's town and premium; the
town provider the mod registers hands them to the labour market and to the population step.
"""
import json
import os

from sim.engine import ui_port
from sim.engine.data import ROOT
from sim.geography import api as geography
from sim.world import climate_needs, demography

# temporary heuristics, each named with what should replace it (see the mod README)
DEFAULT_FOOD_HAUL_DAYS = 3.0           # replace: the haul at which freight cost of grain eats the surplus's value
CROWDING_HALF_POPULATION = 20000.0     # replace: housing density and the contact rate of a town's people
URBAN_DISEASE_PREMIUM_AT_FULL_CROWDING = 1.0   # replace: excess urban mortality measured from the disease model
ROWS_SHOWN = 12


def _water_litres_per_person_day():
    with open(os.path.join(ROOT, "data", "world", "needs.json"), encoding="utf-8") as source:
        return json.load(source)["needs"]["water"]["subsistence_per_capita_per_year"] / 365.0


def _adult_equivalents_per_head(population):
    total = population.total
    if total <= 0.0:
        return 1.0
    return (population.children * demography.CHILD_CALORIE_EQUIVALENT + population.working_age
            + population.elderly * demography.ELDERLY_CALORIE_EQUIVALENT) / total


def _food_reach(sim, tiles, days):
    """{tile: {tile within haul: days}} over the routes the nation's technologies open."""
    held = sim.labour.held_technologies()
    modes = geography.usable_modes([held])
    built = sim.view("built_ways")()
    return {tile: {other: spent for other, spent in geography.reach([tile], modes, days, built, held_nodes=held).items()
                   if other in tiles}
            for tile in tiles}


def _tile_record(tile):
    facts = geography.queries.tile_facts(tile)
    return {"lat": facts["lat"], "koppen_class": facts["climate_class"]}


def urban_report(sim, days=DEFAULT_FOOD_HAUL_DAYS, limit=ROWS_SHOWN):
    people = sim.labour.settlement_tiles()
    tiles = sorted(people)
    population = sim.population
    need_kcal = (demography.SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY * _adult_equivalents_per_head(population))
    surplus = {tile: max(0.0, geography.settlement.capacity_kcal_per_day(tile) - people[tile] * need_kcal)
               for tile in tiles}
    reach = _food_reach(sim, set(tiles), days)
    reached_by = {tile: 0 for tile in tiles}
    for tile in tiles:
        for other in reach[tile]:
            reached_by[other] += 1
    assembled = {tile: sum(surplus[other] / max(1, reached_by[other]) for other in reach[tile]) for tile in tiles}
    food_ceiling = {tile: assembled[tile] / need_kcal if need_kcal > 0.0 else 0.0 for tile in tiles}

    # People in non-farm households: the start-date urban share (an initial condition of the civilisation) kept
    # in step with the population, plus the households of everyone the founder and the firms now employ.
    working_share = population.working_age / population.total if population.total > 0.0 else 0.0
    employed = sum(count for trade, count in sim.view("staff")()["employees"].items() if trade != "labourer")
    founder_dependants = employed / working_share - employed if working_share > 0.0 else 0.0
    firm_households = sim.view("actor_staff_total")() / working_share if working_share > 0.0 else 0.0
    nonfarm_people = population.total * float(sim.civ.get("urban_fraction", 0.0)) + firm_households
    total_assembled = sum(assembled.values())
    base = sim.labour.base_tile()

    disease_burden = ui_port.disease_burden(sim)
    water_litres = _water_litres_per_person_day()
    baseline_death_rate = demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
    rows = []
    for tile in tiles:
        market_share = assembled[tile] / total_assembled if total_assembled > 0.0 else 0.0
        jobs_pull = nonfarm_people * market_share + (founder_dependants if tile == base else 0.0)
        town = min(jobs_pull, food_ceiling[tile])
        crowding = town / (town + CROWDING_HALF_POPULATION)
        premium = disease_burden * URBAN_DISEASE_PREMIUM_AT_FULL_CROWDING * crowding
        record = {"tile": tile, "name": geography.tile_names.tile_name(tile), "tile_people": round(people[tile]),
                  "town_people": round(town), "bound_by": "food reach" if food_ceiling[tile] < jobs_pull else "jobs",
                  "jobs_pull_people": round(jobs_pull), "food_ceiling_people": round(food_ceiling[tile]),
                  "tiles_in_food_reach": len(reach[tile]),
                  "water_cubic_metres_per_day": round(town * water_litres / 1000.0, 1),
                  "urban_mortality_premium": round(premium, 4),
                  "excess_deaths_per_year": round(town * baseline_death_rate * premium, 1)}
        if town > 0.0:
            floors = climate_needs.floors_for_tile(_tile_record(tile))
            record["housing_wall_and_roof_cubic_metres_per_year"] = round(town * floors["shelter_m3"])
        rows.append(record)
    rows.sort(key=lambda row: (-row["town_people"], row["tile"]))
    housed = sum(row["town_people"] for row in rows)
    return {"ok": True, "food_haul_days": days, "nonfarm_people": round(nonfarm_people), "people_in_towns": housed,
            "nonfarm_people_in_no_town": round(max(0.0, nonfarm_people + founder_dependants - housed)),
            "urban_share_of_nation": round(housed / population.total, 4) if population.total > 0.0 else 0.0,
            "disease_burden": round(disease_burden, 3), "towns": rows[:limit], "tiles_counted": len(rows),
            "note": "a derived view: nothing here changes who lives where or who dies; the drivers are the columns"}


def record_towns(sim, write, days=DEFAULT_FOOD_HAUL_DAYS):
    """Hand `write(store, tile, value)` the derived town and its mortality premium of every tile the nation holds."""
    for row in urban_report(sim, days, limit=None)["towns"]:
        write("town_people", row["tile"], row["town_people"])
        write("urban_mortality_premium", row["tile"], row["urban_mortality_premium"])


def register(api):
    towns_store = api.store("town_people", keyed_by="tile", default=None, unit="people")
    premium_store = api.store("urban_mortality_premium", keyed_by="tile", default=None, unit="share of the baseline death rate")

    # The year's derivation is kept in the stores (saved with the game), so the labour market and the population step read
    # one number per tile and a loaded game answers the same as the live one.
    api.phase("derive_towns", "world", lambda sim, seats: record_towns(sim, lambda store, tile, value: api.write_store(sim, store, tile, value)),
              after="money_world")
    api.town_provider("towns", lambda labour, tile, nominal: towns_store.get(labour.simulation_for_providers(), tile),
                      mortality_premium=lambda labour, tile, town: premium_store.get(labour.simulation_for_providers(), tile))

    @api.command("towns", group="society", summary="Towns derived from jobs, food reach and disease, per tile",
                 usage=["bh_urbanisation_w2n6:towns", '{"cmd":"bh_urbanisation_w2n6:towns","days":5}'],
                 description="Shows, for each tile the nation holds, the town its non-farm jobs and the food "
                             "reachable within a haul allow, the water and housing it needs and the mortality "
                             "premium crowding adds while water and sanitation technologies are missing.",
                 options={"days": "days of haul that count as food reach (default %s)" % DEFAULT_FOOD_HAUL_DAYS})
    def towns(sim, nodes, cmd, ended):
        days = DEFAULT_FOOD_HAUL_DAYS
        if isinstance(cmd, dict) and cmd.get("days") is not None:
            try:
                days = max(0.0, float(cmd["days"]))
            except (TypeError, ValueError):
                return {"ok": False, "error": "days must be a number"}
        report = urban_report(sim, days)
        api.state(sim.state.interface)["last_people_in_towns"] = report["people_in_towns"]
        return report
