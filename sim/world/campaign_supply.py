"""What an army eats in a stretch of days and where the food comes from: what it carries, what it takes from the
tile it stands on, and what a column of pack animals brings from a held tile within reach.

Rations and the animal's own fodder are `military_logistics`' (Engels, Alexander the Great and the Logistics of the
Macedonian Army, ch. 1 and Appendix 1: about 3 lb of food a soldier a day, an animal eating much of its own load on a
long haul; Roth, The Logistics of the Roman Army at War, ch. 1: 850 g of grain a day, ch. 4 p. 222: a mule carries
135 kg). Plain functions of numbers; the engine reads the tiles and hands the figures in."""
from typing import NamedTuple

from sim.constants import declare
from sim.world import military_logistics as logistics

CAMPAIGN_SEASON_DAYS = declare(
    "CAMPAIGN_SEASON_DAYS", 200.0, kind="temporary_heuristic", unit="days a year an army can march and camp",
    source=None, confidence="D",
    why="Days of the year an army is in the field. A season set by the tile's cold, mud and harvest (the climate "
        "layers the map holds) would give it; no rule yet reads those for movement.",
    retire="a campaigning season read from the tile's temperature and rainfall layers")

TRAIN_ANIMALS_PER_SOLDIER = declare(
    "TRAIN_ANIMALS_PER_SOLDIER", 0.25, kind="temporary_heuristic", unit="pack animals per soldier",
    source=None, confidence="D",
    why="The baggage train a raised army takes. Engels (ch. 1, table 1) works out how many animals an army of its "
        "size needs for a stated number of days of grain; that table is not read here. A train bought from the "
        "owner's herds, at the price the market quotes, would replace the figure.",
    retire="army baggage animals drawn from the owner's living stock")

SEIZABLE_SHARE_OF_TILE_FOOD = declare(
    "SEIZABLE_SHARE_OF_TILE_FOOD", 0.05, kind="temporary_heuristic", unit="share of a tile's yearly food energy",
    source=None, confidence="D",
    why="The part of a tile's yearly food an army can take from granaries and fields in a year without the tile's own "
        "people being counted. The tile's standing crop and stores, kept by month, would give it.",
    retire="standing crop and granary stock of the tile, by month")

MIN_CARRIAGE_DAYS = 0.5     # a column's shortest trip, so a source on the army's own tile does not deliver without limit


class Feeding(NamedTuple):
    fed_share: float                # share of the need eaten, 0 to 1
    taken_forage_kg: float          # all taken from the land, what was eaten and what refilled the stock
    taken_carriage_kg: float        # all brought by the column, likewise
    from_stock_kg: float
    stock_after_kg: float


def daily_need_kg(soldiers: float) -> float:
    """Grain a force of `soldiers` eats in a day on campaign."""
    return max(0.0, soldiers) * logistics.ration_kg_grain_per_day()


def train_capacity_kg(animals: float) -> float:
    """What an army's pack animals can carry in all."""
    return max(0.0, animals) * logistics.pack_animal_load_capacity_kg()


def carriage_kg_per_day(animals: float, days_one_way: float) -> float:
    """Grain a shuttle of `animals` brings a day from a source `days_one_way` days off: each round trip delivers
    the animal's load less its own fodder for the trip out and back; nothing past the range where that is spent."""
    trip = max(days_one_way, MIN_CARRIAGE_DAYS)
    net = max(0.0, logistics.pack_animal_load_capacity_kg() - 2.0 * trip * logistics.pack_animal_daily_fodder_kg())
    return max(0.0, animals) * net / (2.0 * trip)


def carriage_range_days() -> float:
    """The farthest a column can bring anything from, in days one way."""
    return logistics.pack_animal_max_one_way_days(0.0)


def tile_stock_kg(food_kcal_per_year: float, drawn_kcal: float) -> float:
    """Grain an army can still take from a tile this year: its seizable share of the tile's yearly food, less what
    armies have already taken."""
    seizable = max(0.0, food_kcal_per_year) * SEIZABLE_SHARE_OF_TILE_FOOD - max(0.0, drawn_kcal)
    return max(0.0, seizable) / logistics.GRAIN_ENERGY_KCAL_PER_KG


def kcal_of(grain_kg: float) -> float:
    return grain_kg * logistics.GRAIN_ENERGY_KCAL_PER_KG


def feed(soldiers: float, days: float, stock_kg: float, forage_kg: float, carried_kg: float,
         capacity_kg: float) -> Feeding:
    """An army eats for `days`. It takes what it can from the land (`forage_kg` is all the tile gives in these days)
    and the column (`carried_kg` is all the column brings), then from its own stock; what land and column give past
    the need refills the stock up to `capacity_kg`. `fed_share` is the share of the need that was met."""
    need = daily_need_kg(soldiers) * max(0.0, days)
    forage, carried = max(0.0, forage_kg), max(0.0, carried_kg)
    if need <= 0.0:
        return Feeding(1.0, 0.0, 0.0, 0.0, stock_kg)
    from_forage = min(need, forage)
    from_carriage = min(need - from_forage, carried)
    from_stock = min(need - from_forage - from_carriage, max(0.0, stock_kg))
    eaten = from_forage + from_carriage + from_stock
    stock = stock_kg - from_stock
    room = max(0.0, capacity_kg - stock)
    refill_forage = min(room, forage - from_forage)
    refill_carriage = min(room - refill_forage, carried - from_carriage)
    return Feeding(min(1.0, eaten / need), from_forage + refill_forage, from_carriage + refill_carriage, from_stock,
                   stock + refill_forage + refill_carriage)
