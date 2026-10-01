"""Fire-setting wood: the fuel a hand mine burns to break hard rock.

Standalone: takes a hardness class name, reads no other module. The labour
here is cutting and delivering the wood to the face; the wood's own land
claim is the price solver's business, not a deposit's.
"""
from sim.constants import declare

MINING_SHIFT_HOURS = declare(
    "MINING_SHIFT_HOURS", 8.0, kind="temporary_heuristic",
    unit="labourer-hours per miner-day",
    source="Converts the man-days quoted by Timberlake 1990 (via Bettenay "
           "2022, Metalla 26.2, Table 2) and the forest worker-days of "
           "Bettenay's section on wood sourcing into hours. The shift "
           "length itself was not found in a source opened for this task.",
    confidence="D",
    why="Underground shifts were shorter than a field day; replace with a "
        "sourced shift length.")

FIRE_SET_ROCK_TONNES_PER_TONNE_OF_WOOD = declare(
    "FIRE_SET_ROCK_TONNES_PER_TONNE_OF_WOOD", 0.6, kind="engineering_estimate",
    unit="tonnes of rock brought down per tonne of wood burned",
    source="Bettenay 2022, Metalla 26.2, Table 1 (read from the open-access "
           "PDF): Fournel lead-silver mines average 0.6 over 66 experiments "
           "(range 0.3-1.2); Kongsberg 0.4 (Timberlake 1990); Melle 0.7 and "
           "up to 2.8; Great Orme copper 0.8-3. Wood mass there uses a "
           "density of 0.7.",
    confidence="C",
    why="Sets the fuel a fire-set tonne of rock needs; the spread between "
        "experiments is wide, the Fournel mean is the largest sample.")

WOOD_DELIVERED_TONNES_PER_WORKER_DAY = declare(
    "WOOD_DELIVERED_TONNES_PER_WORKER_DAY", 1.25, kind="engineering_estimate",
    unit="tonnes of green wood felled, hauled and delivered per forest worker-day",
    source="Bettenay 2022, Metalla 26.2: 'somewhere in the order of 1-1.5 "
           "tonnes of green wood per forest worker per day' for an early "
           "medieval mine with forest within a few kilometres; modern hand "
           "operations reach 2.5-3.5. Midpoint of the early medieval range.",
    confidence="C",
    why="Turns the wood a fire-set needs into labour.")

# Share of the rock a hardness class breaks by fire-setting. Hard rock:
# Bettenay and the hard class's own source (Rio Tinto, Dacian quartz) say
# fire-setting was the way in. Softer rock is broken with hammer and wedge;
# the share for medium rock is unsourced and left at none rather than guessed.
FIRE_SET_SHARE_OF_ROCK_BY_HARDNESS = declare(
    "FIRE_SET_SHARE_OF_ROCK_BY_HARDNESS", {"soft": 0.0, "medium": 0.0, "hard": 1.0},
    kind="temporary_heuristic",
    unit="fraction of the rock tonnage broken by fire-setting",
    source=None, confidence="D",
    why="Only hard rock is charged wood until a source gives the share for "
        "ordinary vein rock (Complaints/610).")


def fire_setting_labour_hours_per_tonne_rock(hardness_class):
    """Labourer-hours of wood cutting and delivery per tonne of rock broken
    in a `hardness_class` working."""
    share = FIRE_SET_SHARE_OF_ROCK_BY_HARDNESS.get(hardness_class, 0.0)
    wood_tonnes_per_tonne_rock = share / FIRE_SET_ROCK_TONNES_PER_TONNE_OF_WOOD
    return wood_tonnes_per_tonne_rock / WOOD_DELIVERED_TONNES_PER_WORKER_DAY * MINING_SHIFT_HOURS
