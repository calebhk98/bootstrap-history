"""The labour a hand mine spends besides breaking rock: barren rock, hauling,
hoisting, draining, timbering. Standalone: depth and hardness class names in,
labourer-hours out. Ventilation shafts are charged with the shaft build in
sim/world/deposits.py (VENTILATION_OPENINGS_PER_WORKING_SHAFT).

Basis of grade: a deposit's grade is metal per tonne of ORE as stoped and
presented to dressing (the figures in the geography deposit catalogue are described
as ore grades). Rock broken per tonne of ore is higher by the barren rock
that comes with it (Complaints/348). Barren rock is broken but stowed
underground, so only breaking, fire-setting and timbering scale with rock;
hoisting, carrying and draining scale with ore.
"""
from sim.constants import declare
from sim.world.mine_fire_setting import (
    WOOD_DELIVERED_TONNES_PER_WORKER_DAY as _WOOD_TONNES_PER_WORKER_DAY)

# Bettenay 2022 (Metalla 26.2) Table 4 note 3 gives 50 / 60 / 65 percent for
# realistic / optimistic / extreme Melle; his note 4 calls it an allowance
# (probably insufficient) for shaft-sinking spoil, exploratory drives, waste
# at the face, dilution and discards. Shaft spoil is charged separately here
# (shaft_cost_labour_hours).
ORE_SHARE_OF_ROCK_BROKEN_BY_DEPTH = declare(
    "ORE_SHARE_OF_ROCK_BROKEN_BY_DEPTH",
    {"surface": 1.0, "shallow_vein": 0.65, "deep_vein": 0.5},
    kind="temporary_heuristic",
    unit="tonnes of ore presented per tonne of rock broken",
    source="Bettenay 2022, Metalla 26.2, Table 4 (50-65 percent, Melle, a "
           "thin discontinuous deposit he calls among the worst). Shallow "
           "veins take the best credible value, deep workings the realistic "
           "one. Surface working takes none: stripping overburden is not "
           "charged (Complaints/349).",
    confidence="D",
    why="Sets the barren rock a tonne of ore drags with it; a wide rich "
        "vein would do better, a pod-and-pillar working worse.")

CARRY_LOAD_KILOGRAMS = declare(
    "CARRY_LOAD_KILOGRAMS", 100.0, kind="engineering_estimate",
    unit="kilograms of ore per carrier trip",
    source="Agricola, De re metallica (Hoover translation), Book VI: ore is "
           "wheeled out in barrows, a barrow taking about two buckets drawn "
           "from a shaft. Hand baskets carry less.",
    confidence="C", why="Sets trips per tonne of ore carried.")

CARRY_SPEED_METRES_PER_HOUR = declare(
    "CARRY_SPEED_METRES_PER_HOUR", 3000.0, kind="biological_parameter",
    unit="metres/hour over the whole round trip",
    source=None, confidence="D",
    why="Walking pace with a barrow in a low gallery; loading and tipping "
        "time not counted.")

HAUL_DISTANCE_METRES_BY_DEPTH = declare(
    "HAUL_DISTANCE_METRES_BY_DEPTH",
    {"surface": 100.0, "shallow_vein": 150.0, "deep_vein": 400.0},
    kind="temporary_heuristic",
    unit="metres from the face to the shaft foot or portal, plus the "
         "surface carry to dressing",
    source="Pliny NH 33.97 (quoted in Agricola's notes) has the Baebelo "
           "workings driven fifteen hundred paces, so a face is not at the "
           "shaft foot.",
    confidence="D",
    why="the deposit catalogue carries a depth class, not a plan; replace with "
        "layout data.")

WATER_LIFTED_TONNES_PER_TONNE_ORE_BY_DEPTH = declare(
    "WATER_LIFTED_TONNES_PER_TONNE_ORE_BY_DEPTH",
    {"surface": 0.0, "shallow_vein": 0.5, "deep_vein": 3.0},
    kind="temporary_heuristic",
    unit="tonnes of water lifted from the sump per tonne of ore raised",
    source="No inflow rate per tonne of ore exists in a source opened "
           "(Complaints/349 searched: Willies 1997 on Rio Tinto, read in "
           "full; Bettenay 2022, Kakavoyannis 2001, Morin-Hamon 2023, read; "
           "Agricola searched; Domergue, Davies, Healy not openable). Direction: Diodorus 5.37 (Spanish mines meet "
           "'flowing subterranean rivers', drawn off by Archimedean screws "
           "in successive lifts), Pliny NH 33.97 (bailers night and day at "
           "Baebelo). Willies 1997: a Rio Tinto wheel lifts about 86 litres "
           "a minute, a battery of eight pairs lifting 29 m removes about 250 "
           "tonnes of water a day with 48 to 64 men; the district's 4 to 5 "
           "million tonnes of ore (from about 6 million tonnes of slag) over "
           "a working life of one to a few centuries is some 150 to 600 "
           "tonnes of ore a day, so a single battery is 0.4 to 1.7 tonnes of "
           "water per tonne of ore, and a deep mine of several batteries "
           "several times that. Best-supported range 0.4 to about 7; the "
           "shallow and deep values sit inside it and are kept.",
    confidence="D",
    why="Drainage is the largest uncertain term of a deep mine; the lift "
        "work per tonne of water is physical, the inflow is a guess. "
        "Drainage adits lower the head it is lifted through "
        "(mine_technique.py).")

TIMBERED_SHARE_OF_WORKINGS_BY_HARDNESS = declare(
    "TIMBERED_SHARE_OF_WORKINGS_BY_HARDNESS",
    {"soft": 1.0, "medium": 0.4, "hard": 0.15},
    kind="temporary_heuristic", unit="fraction of working length timbered",
    source=None, confidence="D",
    why="Soft ground needs a set every few metres, sound hard rock hardly "
        "any; Bettenay names timbering as a use of wood but gives no "
        "quantity.")

TIMBER_WOOD_TONNES_PER_TIMBERED_METRE = declare(
    "TIMBER_WOOD_TONNES_PER_TIMBERED_METRE", 0.05, kind="engineering_estimate",
    unit="tonnes of green wood per metre of timbered drive",
    source="One set (two posts and a cap, round timber about 15 cm by 2 m, "
           "0.7 t/m^3) every 1.5 m.",
    confidence="D", why="Wood to hold a drive open.")

TIMBER_FITTING_HOURS_PER_TIMBERED_METRE = declare(
    "TIMBER_FITTING_HOURS_PER_TIMBERED_METRE", 1.5, kind="temporary_heuristic",
    unit="labourer-hours per metre of timbered drive", source=None,
    confidence="D", why="Dressing, carrying down and setting the timber.")

DRIVE_ROCK_TONNES_PER_METRE = declare(
    "DRIVE_ROCK_TONNES_PER_METRE", 5.2, kind="engineering_estimate",
    unit="tonnes of rock per metre of drive",
    source="2 square metres of section at 2.6 t/m^3 (Kongsberg's drive is "
           "about 3 square metres).",
    confidence="C", why="Turns timber per metre into timber per tonne.")

# Natural draught needs an inlet and an outlet at different heights;
# Bettenay: Melle-type workings need "multiple shafts to aid ventilation and
# ore removal".
VENTILATION_OPENINGS_PER_WORKING_SHAFT = declare(
    "VENTILATION_OPENINGS_PER_WORKING_SHAFT", 1.0, kind="engineering_estimate",
    unit="extra ventilation shafts per working shaft",
    source="Bettenay 2022: vertical shafts to ventilate faces and dissipate "
           "fire-setting fumes. Natural draught needs two openings.",
    confidence="C", why="Charged as a second shaft without hoist or sump.")


LAMP_FLAME_POWER_WATTS = declare(
    "LAMP_FLAME_POWER_WATTS", 60.0, kind="temporary_heuristic",
    unit="watts of heat from one miner's oil lamp flame",
    source="No measured oil consumption of a Roman or Greek lamp was found "
           "(Complaints/349 searched the EXARC lamp experiment, the "
           "Amsterdam Mithraeum lamp experiment and replica-lamp makers: "
           "none gives a rate). Small wick flames burn in the tens of "
           "watts; range 40 to 80.",
    confidence="D",
    why="Lighting is a surface-and-underground cost the hours do not carry; "
        "lamp_oil_kilograms_per_labourer_hour turns it into oil.")

OLIVE_OIL_ENERGY_MEGAJOULES_PER_KILOGRAM = declare(
    "OLIVE_OIL_ENERGY_MEGAJOULES_PER_KILOGRAM", 37.0, kind="physical_constant",
    unit="megajoules per kilogram", source="Heat of combustion of vegetable "
    "oil, handbook value.", confidence="A", why="Turns lamp power into oil.")


def lamp_oil_kilograms_per_labourer_hour():
    """Olive oil one lamp burns in an hour underground. At the oil's price
    this is under one percent of the hours of a silver deposit's ore, which
    is why no recipe carries it as an input (the ore recipes carry no
    inputs; measure with the solver's olive_oil_kg price)."""
    return (LAMP_FLAME_POWER_WATTS * 3600.0 / 1.0e6
            / OLIVE_OIL_ENERGY_MEGAJOULES_PER_KILOGRAM)


def rock_broken_tonnes_per_tonne_ore(depth_class):
    """Tonnes of rock broken for each tonne of ore presented."""
    return 1.0 / ORE_SHARE_OF_ROCK_BROKEN_BY_DEPTH[depth_class]


def works_hours_per_tonne_ore(depth_class, hardness_class,
                              lift_hours_per_tonne_metre, depth_metres,
                              shift_hours, effects=None,
                              drainage_hours_per_tonne_metre=None):
    """{term: labourer-hours per tonne of ORE} for hoisting, carrying,
    drainage and timbering. Breaking and fire-setting stay in deposits.py.
    `effects` (mine_technique.combine) lowers the head water is lifted
    through and the load a carrier takes; `drainage_hours_per_tonne_metre` is
    the lift cost of the water device in use and defaults to the hoist's."""
    effects = effects or {}
    if drainage_hours_per_tonne_metre is None:
        drainage_hours_per_tonne_metre = lift_hours_per_tonne_metre
    drained_head = depth_metres * (1.0 - effects.get("gravity_drained_head_share", 0.0))
    load_kilograms = max(CARRY_LOAD_KILOGRAMS, effects.get("haulage_load_kilograms", 0.0))
    carry_trips = 1000.0 / load_kilograms
    haul = (carry_trips * 2.0 * HAUL_DISTANCE_METRES_BY_DEPTH[depth_class]
            / CARRY_SPEED_METRES_PER_HOUR)
    timber_hours_per_metre = (
        TIMBER_WOOD_TONNES_PER_TIMBERED_METRE / _WOOD_TONNES_PER_WORKER_DAY
        * shift_hours + TIMBER_FITTING_HOURS_PER_TIMBERED_METRE)
    timbering = (TIMBERED_SHARE_OF_WORKINGS_BY_HARDNESS[hardness_class]
                 * timber_hours_per_metre / DRIVE_ROCK_TONNES_PER_METRE
                 * rock_broken_tonnes_per_tonne_ore(depth_class))
    lift_head = lift_hours_per_tonne_metre * depth_metres
    return {
        "hoist": lift_head,
        "haulage": haul,
        "drainage": (WATER_LIFTED_TONNES_PER_TONNE_ORE_BY_DEPTH[depth_class]
                     * drainage_hours_per_tonne_metre * drained_head),
        "timbering": timbering,
    }
