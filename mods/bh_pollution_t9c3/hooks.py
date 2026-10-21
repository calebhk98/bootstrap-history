"""Industrial pollution from the year's physical throughput: emissions per tile, exposure, harm, and what cleans it.

Emissions are the tonnes the producers actually ran (last year's runs times each recipe's inputs and outputs) times
the per-kilogram factors in data/pollution/emissions.json. A steady-state box over the tile's settled airshed turns
them into a concentration; the exposure-response table turns that into excess deaths and lost yield. Nothing here
names a civilisation, a technology that is not in the data file, or a flat industry penalty.
"""
import json
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pollution", "emissions.json")
SECONDS_PER_YEAR = 365.25 * 24 * 3600
MICROGRAMS_PER_KILOGRAM = 1e9
SQUARE_METRES_PER_SQUARE_KILOMETRE = 1e6
AGE_BANDS = ("children", "working_age", "elderly")
TOP_TILES_SHOWN = 8

_TABLE = []


def table():
    if not _TABLE:
        with open(DATA_FILE, encoding="utf-8") as source:
            _TABLE.append(json.load(source))
    return _TABLE[0]


def _kilograms_per_unit(material):
    from sim.engine.material_units import tonnes_per_unit
    return tonnes_per_unit(material) * 1000.0


def emissions_by_tile(sim):
    """({tile: {species: kg}}, {tile: {source id: {species: kg}}}) from the producers' last full year, empty before
    the economy has run."""
    if not sim.economy.agent.opened():
        return {}, {}
    from sim.economy import api as economy_api
    economy = sim.economy.agent.economy()
    recipes = economy.setup.recipes
    sources = table()["sources"]
    by_tile, drivers = {}, {}
    for producer in economy_api.all_producers(economy):
        runs = max(producer.last_runs, 0.0)
        recipe = recipes.get(producer.recipe_id)
        if runs <= 0.0 or recipe is None:
            continue
        for source_id, source in sources.items():
            flows = recipe.inputs if source["basis"] == "input" else recipe.outputs
            quantity = flows.get(source["material"], 0.0)
            if quantity <= 0.0:
                continue
            kilograms = runs * quantity * _kilograms_per_unit(source["material"])
            for species, spec in source["species"].items():
                released = kilograms * spec["kg_per_kg"]
                tile_species = by_tile.setdefault(producer.tile, {})
                tile_species[species] = tile_species.get(species, 0.0) + released
                tile_drivers = drivers.setdefault(producer.tile, {}).setdefault(source_id, {})
                tile_drivers[species] = tile_drivers.get(species, 0.0) + released
    return by_tile, drivers


def abatement(sim):
    """{species: share of the emission that escapes}, from the cleanup technologies the nation holds."""
    escaping = {}
    for entry in table()["abatement"]:
        if not sim.has(entry["node"]):
            continue
        for species in entry["species"]:
            escaping[species] = escaping.get(species, 1.0) * (1.0 - entry["efficiency"])
    return escaping


def _people_by_tile(sim):
    return dict(sim.labour.settlement_tiles())


def _airshed_square_metres(sim, tile, people):
    dispersion = table()["dispersion"]
    tile_area = sim.world_map.tiles[tile]["land_area_km2"] * SQUARE_METRES_PER_SQUARE_KILOMETRE
    footprint = people * dispersion["settled_land_square_metres_per_person"]["value"]
    return min(tile_area, max(footprint, 1.0))


def concentration(kilograms_a_year, airshed_square_metres):
    """Annual-mean micrograms per cubic metre from a steady-state box: rate / (wind speed x mixing height x width)."""
    dispersion = table()["dispersion"]
    width = airshed_square_metres ** 0.5
    rate = kilograms_a_year / SECONDS_PER_YEAR
    volume_flow = dispersion["wind_speed_metres_per_second"]["value"] * dispersion["mixing_height_metres"]["value"] * width
    return rate / volume_flow * MICROGRAMS_PER_KILOGRAM


def assess(sim):
    """The year's pollution picture: per tile emissions after cleanup, concentration, excess deaths by band, yield factor."""
    from sim.world import demography
    raw, drivers = emissions_by_tile(sim)
    escaping = abatement(sim)
    people_by_tile = _people_by_tile(sim)
    total_people = sum(people_by_tile.values()) or 1.0
    population = sim.population
    baseline = {"children": demography.BASELINE_ANNUAL_MORTALITY_RATE_CHILD,
                "working_age": demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE,
                "elderly": demography.BASELINE_ANNUAL_MORTALITY_RATE_ELDERLY}
    response = table()["exposure_response"]
    crop = response["sulphur_dioxide"]
    critical = crop["crop_critical_level_microgram_per_cubic_metre"]["value"]
    loss_per_critical = crop["yield_loss_per_critical_level_exceeded"]["value"]
    tiles, deaths_by_band, yield_factor_by_tile = [], {band: 0.0 for band in AGE_BANDS}, {}
    for tile in sorted(raw):
        emitted = {species: kilograms * escaping.get(species, 1.0) for species, kilograms in raw[tile].items()}
        people = people_by_tile.get(tile, 0.0)
        airshed = _airshed_square_metres(sim, tile, people)
        micrograms = {species: concentration(kilograms, airshed) for species, kilograms in emitted.items()}
        slope = response["particulate"]["mortality_relative_risk_per_microgram_per_cubic_metre"]
        excess_share = slope * micrograms.get("particulate", 0.0)
        tile_deaths = {}
        for band in AGE_BANDS:
            band_people = getattr(population, band) * people / total_people
            tile_deaths[band] = min(band_people, band_people * baseline[band] * excess_share)
            deaths_by_band[band] += tile_deaths[band]
        # the crop damage works over the whole tile's farmland, so the box is the tile
        regional = concentration(emitted.get("sulphur_dioxide", 0.0),
                                 sim.world_map.tiles[tile]["land_area_km2"] * SQUARE_METRES_PER_SQUARE_KILOMETRE)
        exceeded = max(0.0, regional / critical - 1.0)
        yield_factor = max(0.0, 1.0 - loss_per_critical * exceeded)
        if yield_factor < 1.0:
            yield_factor_by_tile[tile] = yield_factor
        tiles.append({"tile": tile, "people": round(people), "airshed_km2": round(airshed / SQUARE_METRES_PER_SQUARE_KILOMETRE, 1),
                      "emitted_kg": {species: round(kilograms, 1) for species, kilograms in sorted(emitted.items())},
                      "cleaned_kg": {species: round(raw[tile][species] - emitted[species], 1)
                                     for species in sorted(emitted) if raw[tile][species] > emitted[species]},
                      "micrograms_per_cubic_metre": {species: round(value, 4) for species, value in sorted(micrograms.items())},
                      "excess_deaths": {band: round(value, 2) for band, value in tile_deaths.items()},
                      "yield_factor": round(yield_factor, 4),
                      "drivers": {source: {species: round(kilograms, 1) for species, kilograms in sorted(species_kg.items())}
                                  for source, species_kg in sorted(drivers[tile].items())}})
    return {"tiles": tiles, "deaths_by_band": deaths_by_band, "yield_factor_by_tile": yield_factor_by_tile,
            "cleanup_held": sorted(entry["node"] for entry in table()["abatement"] if sim.has(entry["node"]))}


def externalities(sim, year):
    """The engine hook's answer (any mod can feed it): deaths by band and a yield factor per tile."""
    picture = assess(sim)
    return {"deaths_by_band": picture["deaths_by_band"], "yield_factor_by_tile": picture["yield_factor_by_tile"]}


def record_pollution(sim, write):
    """Hand `write(store, tile, value)` the year's particulate concentration and yield factor of every settled or emitting tile."""
    picture = assess(sim)
    rows = {row["tile"]: row for row in picture["tiles"]}
    for tile in sorted(set(rows) | set(_people_by_tile(sim))):
        row = rows.get(tile)
        write("particulate_micrograms_per_cubic_metre", tile, row["micrograms_per_cubic_metre"].get("particulate", 0.0) if row else 0.0)
        write("pollution_yield_factor", tile, row["yield_factor"] if row else 1.0)


def register(api):
    register_externality = getattr(api, "externality", None)
    if register_externality is not None:
        register_externality(externalities)
    # Each year's picture is kept in tile stores, so `map layer <store>` shows where the air is foul and the harvest harmed.
    api.store("particulate_micrograms_per_cubic_metre", keyed_by="tile", default=None, unit="micrograms per cubic metre")
    api.store("pollution_yield_factor", keyed_by="tile", default=None, unit="share of the harvest left")
    api.phase("record_pollution", "world",
              lambda sim, seats: record_pollution(sim, lambda store, tile, value: api.write_store(sim, store, tile, value)),
              after="market")

    @api.command("pollution", group="mods",
                 summary="Emissions, exposure and harm from the year's industrial throughput, by tile",
                 usage=["pollution"],
                 description="Reads the tonnes of coal burned and mined and of ore smelted that the producers ran last year, "
                             "turns them into emissions per tile with the factors in the mod's data, disperses them over the "
                             "tile's settled airshed, and shows the concentration, the excess deaths and lost harvest that "
                             "exposure implies, and the cleanup technologies held. Drivers name which source made each kilogram.")
    def pollution(sim, nodes, cmd, ended):
        picture = assess(sim)
        year = sim.state.scenario.year
        memory = api.state(sim.state.interface)
        memory.setdefault("history", {})[str(year)] = {
            "excess_deaths": round(sum(picture["deaths_by_band"].values()), 2),
            "tiles_emitting": len(picture["tiles"])}
        ranked = sorted(picture["tiles"], key=lambda row: (-sum(row["excess_deaths"].values()), -sum(row["emitted_kg"].values())))
        totals = {}
        for row in picture["tiles"]:
            for species, kilograms in row["emitted_kg"].items():
                totals[species] = totals.get(species, 0.0) + kilograms
        return {"ok": True, "command": "bh_pollution_t9c3:pollution", "year": year,
                "totals_emitted_kg": {species: round(value, 1) for species, value in sorted(totals.items())},
                "excess_deaths_by_band": {band: round(value, 2) for band, value in picture["deaths_by_band"].items()},
                "cleanup_held": picture["cleanup_held"],
                "tiles_emitting": len(picture["tiles"]), "tiles": ranked[:TOP_TILES_SHOWN],
                "applied_to_the_game": getattr(api, "externality", None) is not None,
                "note": "Read-only on engines without the externality hook: the deaths and yield factors are what the hook "
                        "would apply, not what happened."}
