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
    source="Diodorus 5.37 (Spanish mines meet 'flowing subterranean "
           "rivers', drawn off by Archimedean screws in successive lifts) "
           "and Pliny NH 33.97 (bailers standing night and day at Baebelo) "
           "give the direction; no inflow rate was found in a source opened.",
    confidence="D",
    why="Drainage is the largest uncertain term of a deep mine; the lift "
        "work per tonne of water is physical, the inflow is a guess. "
        "Drainage adits (Bettenay) would lower it.")

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


def rock_broken_tonnes_per_tonne_ore(depth_class):
    """Tonnes of rock broken for each tonne of ore presented."""
    return 1.0 / ORE_SHARE_OF_ROCK_BROKEN_BY_DEPTH[depth_class]


def works_hours_per_tonne_ore(depth_class, hardness_class,
                              lift_hours_per_tonne_metre, depth_metres,
                              shift_hours):
    """{term: labourer-hours per tonne of ORE} for hoisting, carrying,
    drainage and timbering. Breaking and fire-setting stay in deposits.py."""
    carry_trips = 1000.0 / CARRY_LOAD_KILOGRAMS
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
        "drainage": WATER_LIFTED_TONNES_PER_TONNE_ORE_BY_DEPTH[depth_class] * lift_head,
        "timbering": timbering,
    }
