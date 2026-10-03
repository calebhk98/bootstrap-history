"""Subsistence floors of warmth, clothing and shelter, calculated from a tile's climate.

Per person per year, in the units of data/world/needs.json: warmth_mj is megajoules of fuel heat,
clothing_kg is kg of cloth equivalent, shelter_m3 is cubic metres of wall or frame. Nothing here is
authored per civilisation: a tile's Koppen class and latitude give a sinusoidal year
(sim/geography/climate_temperatures.py) and the floors follow from heat balance.

Warmth: heat the dwelling loses below the balance temperature, divided by how much of a hearth's fuel
heat stays in the dwelling. The balance temperature is the outdoor temperature below which heating is
needed; it is lower than the indoor setpoint because body and cooking heat already present supply the
difference. Lighting is not modelled.
Clothing: insulation (clo) in heat balance outdoors in the coldest month, ISO 7730 / Fanger:
required total insulation = (skin temperature - air temperature) / dry heat loss per square metre;
one clo is 0.155 square metre kelvin per watt; the air layer takes part of it.
Shelter: floor area under a roof everywhere; walls enclose the dwelling where the coldest month is below
the balance temperature, thick enough that the inner wall surface stays within a few kelvin of the air.
"""
from sim.constants import declare
from sim.geography.api import (
    KOPPEN_TROPICAL_COLDEST_MONTH_MINIMUM_CELSIUS, daily_temperatures, representative_extremes)

HEATING_BALANCE_TEMPERATURE_CELSIUS = declare(
    "HEATING_BALANCE_TEMPERATURE_CELSIUS", 15.5,
    kind="engineering_estimate", unit="degrees Celsius",
    source="UK heating degree-day base temperature (CIBSE TM41, Met Office): internal gains cover the "
           "gap up to the indoor setpoint",
    confidence="B",
    why="Outdoor temperature below which a dwelling needs added heat; body and cooking heat are already "
        "counted in it, so no separate gain is subtracted.")

DWELLING_HEAT_LOSS_WATTS_PER_KELVIN_PER_PERSON = declare(
    "DWELLING_HEAT_LOSS_WATTS_PER_KELVIN_PER_PERSON", 25.0,
    kind="engineering_estimate", unit="watts per kelvin per person",
    source="Fabric plus air-change loss of a small pre-industrial cottage (a few tens of square metres, "
           "thick walls, leaky) shared by a household; the modern UK average dwelling is several times "
           "larger in absolute loss for fewer people",
    confidence="D",
    why="Converts degree-days into heat the household must supply. Not a function of wall thickness here, "
        "so a thicker wall costs material but does not lower the heat need; refine with a dwelling model.")

HEARTH_FUEL_HEAT_SHARE_KEPT_IN_DWELLING = declare(
    "HEARTH_FUEL_HEAT_SHARE_KEPT_IN_DWELLING", 0.4,
    kind="engineering_estimate", unit="dimensionless (delivered heat per unit of fuel heat)",
    source="Chimneyless or open central hearth: most combustion heat stays inside, the smoke or flue "
           "carries part away; open fireplaces with chimneys keep far less",
    confidence="D",
    why="Converts heat the dwelling needs into the fuel heat of data/world/needs.json "
        "(warmth_and_light, 'megajoules of fuel heat', effectiveness being heating value per kg).")

SKIN_TEMPERATURE_CELSIUS = declare(
    "SKIN_TEMPERATURE_CELSIUS", 33.0,
    kind="biological_parameter", unit="degrees Celsius",
    source="Fanger (1970), ISO 7730: mean skin temperature in thermal comfort",
    confidence="B",
    why="Hot side of the temperature difference the clothing and air layer must hold.")

LIGHT_ACTIVITY_METABOLIC_HEAT_WATTS_PER_SQUARE_METRE = declare(
    "LIGHT_ACTIVITY_METABOLIC_HEAT_WATTS_PER_SQUARE_METRE", 93.0,
    kind="biological_parameter", unit="watts per square metre of body surface",
    source="1 met is 58.15 W/m2 (ISO 7730); light outdoor activity taken as 1.6 met (ISO 8996)",
    confidence="B",
    why="Heat the body gives off at light activity; sets how much insulation holds heat balance.")

DRY_SHARE_OF_METABOLIC_HEAT = declare(
    "DRY_SHARE_OF_METABOLIC_HEAT", 0.75,
    kind="biological_parameter", unit="dimensionless",
    source="Respiration and skin evaporation take about a quarter of metabolic heat (Fanger 1970)",
    confidence="B",
    why="Only the dry share crosses the clothing layer by conduction and radiation.")

CLO_IN_SQUARE_METRE_KELVIN_PER_WATT = declare(
    "CLO_IN_SQUARE_METRE_KELVIN_PER_WATT", 0.155,
    kind="physical_constant", unit="square metre kelvin per watt per clo",
    source="ISO 9920 definition of the clo", confidence="A",
    why="Unit conversion from thermal resistance to clo.")

OUTDOOR_AIR_LAYER_INSULATION_CLO = declare(
    "OUTDOOR_AIR_LAYER_INSULATION_CLO", 0.4,
    kind="engineering_estimate", unit="clo",
    source="ISO 9920: still-air boundary layer about 0.7 clo, less in the breeze outdoors",
    confidence="C",
    why="Insulation the surrounding air gives, which clothing need not supply.")

MINIMUM_COVERING_CLO = declare(
    "MINIMUM_COVERING_CLO", 0.3,
    kind="temporary_heuristic", unit="clo",
    source=None, confidence="D",
    why="Covering for sun, wear and modesty wanted even where the cold month needs no insulation; a "
        "cultural and sun-exposure floor, to be replaced by a model of sun and custom.")

CLOTH_KILOGRAMS_PER_CLO_PER_PERSON = declare(
    "CLOTH_KILOGRAMS_PER_CLO_PER_PERSON", 2.0,
    kind="engineering_estimate", unit="kg of cloth per clo per person",
    source="Order of the mass of clothed ensembles against their insulation (ISO 9920, McCullough and "
           "Jones 1984 ensemble tables); woven wool and linen are bulkier than modern fabric",
    confidence="D",
    why="Converts the insulation a person needs into the cloth of needs.json.")

GARMENT_SERVICE_LIFE_YEARS = declare(
    "GARMENT_SERVICE_LIFE_YEARS", 4.0,
    kind="engineering_estimate", unit="years", source=None, confidence="D",
    why="Wardrobe is replaced over this span; yearly need is the wardrobe divided by it.")

FLOOR_AREA_SQUARE_METRES_PER_PERSON = declare(
    "FLOOR_AREA_SQUARE_METRES_PER_PERSON", 3.5,
    kind="biological_parameter", unit="square metres per person",
    source="Sphere Handbook minimum covered area per person (more in cold climates, not applied)",
    confidence="B",
    why="Floor under a roof everywhere; sets the roof and the wall perimeter.")

PERSONS_PER_HOUSEHOLD = declare(
    "PERSONS_PER_HOUSEHOLD", 5.0,
    kind="initial_condition", unit="persons",
    source="Pre-industrial mean household size (Laslett 1972)", confidence="C",
    why="Persons sharing one dwelling, so walls shared between them are counted once.")

WALL_HEIGHT_METRES = declare(
    "WALL_HEIGHT_METRES", 2.2,
    kind="engineering_estimate", unit="metres", source=None, confidence="D",
    why="Eave height of a one-storey dwelling.")

WALL_THERMAL_CONDUCTIVITY_WATTS_PER_METRE_KELVIN = declare(
    "WALL_THERMAL_CONDUCTIVITY_WATTS_PER_METRE_KELVIN", 0.5,
    kind="engineering_estimate", unit="W/(m K)",
    source="Between timber (0.13), turf and wattle-and-daub (0.3 to 0.7) and fired or earth masonry (0.6 to 1)",
    confidence="D",
    why="Wall thickness follows from the resistance needed and this conductivity.")

COLD_WALL_SURFACE_DROP_KELVIN = declare(
    "COLD_WALL_SURFACE_DROP_KELVIN", 3.0,
    kind="engineering_estimate", unit="kelvin",
    source="ISO 7730 limits the cold-wall radiant asymmetry; a few kelvin below room air is the usual design limit",
    confidence="C",
    why="Largest gap between room air and inner wall surface tolerated, which fixes the wall resistance.")

INNER_SURFACE_RESISTANCE = declare(
    "INNER_SURFACE_RESISTANCE", 0.13,
    kind="physical_constant", unit="square metre kelvin per watt",
    source="ISO 6946 internal surface resistance, horizontal heat flow", confidence="A",
    why="Resistance of the air film on the wall's inner face.")

OUTER_SURFACE_RESISTANCE = declare(
    "OUTER_SURFACE_RESISTANCE", 0.04,
    kind="physical_constant", unit="square metre kelvin per watt",
    source="ISO 6946 external surface resistance", confidence="A",
    why="Resistance of the air film on the wall's outer face.")

MINIMUM_WALL_THICKNESS_METRES = declare(
    "MINIMUM_WALL_THICKNESS_METRES", 0.1,
    kind="engineering_estimate", unit="metres", source=None, confidence="D",
    why="Thinnest wall or screen that keeps out rain and wind (wattle and daub, planks, mats).")

MINIMUM_ROOF_THICKNESS_METRES = declare(
    "MINIMUM_ROOF_THICKNESS_METRES", 0.2,
    kind="engineering_estimate", unit="metres of frame and covering", source=None, confidence="D",
    why="Thinnest roof that sheds rain (thatch, shingle, frame); roofs also need the wall's insulation.")

OPEN_FRAME_ENCLOSED_FRACTION = declare(
    "OPEN_FRAME_ENCLOSED_FRACTION", 0.25,
    kind="temporary_heuristic", unit="dimensionless (share of the perimeter walled)",
    source=None, confidence="D",
    why="Where no month is cold, a lean-to or open frame needs only screens against rain and wind for "
        "part of its perimeter; replace with a rain, wind and privacy model.")

STRUCTURE_SERVICE_LIFE_YEARS = declare(
    "STRUCTURE_SERVICE_LIFE_YEARS", 30.0,
    kind="engineering_estimate", unit="years", source=None, confidence="D",
    why="Dwelling frame and walls are replaced over this span; yearly need is the structure divided by it.")

SECONDS_PER_DAY = declare(
    "SECONDS_PER_DAY", 86400.0,
    kind="physical_constant", unit="seconds per day", source="definition", confidence="A",
    why="Unit conversion from degree-days to kelvin-seconds.")

JOULES_PER_MEGAJOULE = declare(
    "JOULES_PER_MEGAJOULE", 1.0e6,
    kind="physical_constant", unit="joules per megajoule", source="definition", confidence="A",
    why="Unit conversion.")


def warmth_delivered_mj(coldest, warmest):
    """Heat the dwelling must be given per person per year (MJ), from the heating degree-days."""
    degree_days = sum(max(0.0, HEATING_BALANCE_TEMPERATURE_CELSIUS - temperature)
                      for temperature in daily_temperatures(coldest, warmest))
    return (degree_days * SECONDS_PER_DAY * DWELLING_HEAT_LOSS_WATTS_PER_KELVIN_PER_PERSON
            / JOULES_PER_MEGAJOULE)


def required_clothing_insulation_clo(coldest):
    """Insulation of the outfit for the coldest month: heat balance at light activity, never below the
    minimum covering."""
    dry_heat_loss = LIGHT_ACTIVITY_METABOLIC_HEAT_WATTS_PER_SQUARE_METRE * DRY_SHARE_OF_METABOLIC_HEAT
    total_clo = ((SKIN_TEMPERATURE_CELSIUS - coldest) / dry_heat_loss) / CLO_IN_SQUARE_METRE_KELVIN_PER_WATT
    return max(MINIMUM_COVERING_CLO, total_clo - OUTDOOR_AIR_LAYER_INSULATION_CLO)


def clothing_kg_per_year(coldest):
    return (required_clothing_insulation_clo(coldest) * CLOTH_KILOGRAMS_PER_CLO_PER_PERSON
            / GARMENT_SERVICE_LIFE_YEARS)


def _enclosed_fraction(coldest):
    """Share of the perimeter walled: all of it below the balance temperature, the open-frame share once
    the coldest month is as warm as the tropical class bound, linear between."""
    warm = KOPPEN_TROPICAL_COLDEST_MONTH_MINIMUM_CELSIUS
    cold = HEATING_BALANCE_TEMPERATURE_CELSIUS
    ramp = min(1.0, max(0.0, (warm - coldest) / (warm - cold)))
    return OPEN_FRAME_ENCLOSED_FRACTION + (1.0 - OPEN_FRAME_ENCLOSED_FRACTION) * ramp


def wall_thickness_metres(coldest):
    """Wall thickness giving the resistance that holds the inner surface within the tolerated drop."""
    temperature_difference = max(0.0, HEATING_BALANCE_TEMPERATURE_CELSIUS - coldest)
    total_resistance = INNER_SURFACE_RESISTANCE * temperature_difference / COLD_WALL_SURFACE_DROP_KELVIN
    material_resistance = max(0.0, total_resistance - INNER_SURFACE_RESISTANCE - OUTER_SURFACE_RESISTANCE)
    return max(MINIMUM_WALL_THICKNESS_METRES,
               material_resistance * WALL_THERMAL_CONDUCTIVITY_WATTS_PER_METRE_KELVIN)


def shelter_m3_per_year(coldest):
    """Wall and roof volume per person per year; the roof is as thick as the wall where walls are needed."""
    household_floor = FLOOR_AREA_SQUARE_METRES_PER_PERSON * PERSONS_PER_HOUSEHOLD
    thickness = wall_thickness_metres(coldest)
    enclosed = _enclosed_fraction(coldest)
    wall_volume = (4.0 * household_floor ** 0.5 * WALL_HEIGHT_METRES * enclosed * thickness)
    roof_volume = household_floor * max(MINIMUM_ROOF_THICKNESS_METRES, thickness * enclosed)
    return (wall_volume + roof_volume) / PERSONS_PER_HOUSEHOLD / STRUCTURE_SERVICE_LIFE_YEARS


def floors_for_class(class_code, latitude):
    """Floors for one Koppen class at a latitude."""
    coldest, warmest = representative_extremes(class_code, latitude)
    return {"warmth_mj": warmth_delivered_mj(coldest, warmest) / HEARTH_FUEL_HEAT_SHARE_KEPT_IN_DWELLING,
            "clothing_kg": clothing_kg_per_year(coldest),
            "shelter_m3": shelter_m3_per_year(coldest)}


def floors_for_tile(tile_record):
    """Per person per year floors of a tile record (lat, koppen_class, optional koppen_sample_mix).
    Floors are nonlinear in temperature, so a sampled mix of classes is averaged over the floors,
    weighted by sample counts, not over temperatures."""
    latitude = tile_record["lat"]
    mix = tile_record.get("koppen_sample_mix") or {tile_record["koppen_class"]: 1}
    total_samples = float(sum(mix.values()))
    floors = {"warmth_mj": 0.0, "clothing_kg": 0.0, "shelter_m3": 0.0}
    for class_code in sorted(mix):
        class_floors = floors_for_class(class_code, latitude)
        for name in floors:
            floors[name] += class_floors[name] * mix[class_code] / total_samples
    return floors


def floors_for_civilisation_tiles(geography, tile_ids, population_by_tile=None):
    """Floors of each tile and their population-weighted mean (equal weights when no population given)."""
    tiles = geography["land_tiles"]["tiles"]
    population_by_tile = population_by_tile or {}
    by_tile = {tile_id: floors_for_tile(tiles[tile_id]) for tile_id in sorted(tile_ids)}
    weights = {tile_id: population_by_tile.get(tile_id, 1.0) for tile_id in by_tile}
    total_weight = sum(weights.values())
    if not by_tile or total_weight <= 0:
        raise ValueError("no tiles with population to weight")
    mean = {name: sum(by_tile[tile_id][name] * weights[tile_id] for tile_id in by_tile) / total_weight
            for name in ("warmth_mj", "clothing_kg", "shelter_m3")}
    return {"by_tile": by_tile, "weighted_mean": mean}
