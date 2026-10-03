"""Representative monthly temperatures of a tile, from its Koppen-Geiger class and latitude.

The class definitions bound the coldest-month and warmest-month means (and the number of months at or
above the growing threshold). A tile is placed inside those bounds by its latitude, then given a
sinusoidal year. Pure functions of their arguments; no engine, no files.
A per-tile monthly temperature field from a climate dataset would replace all of it.
"""
import math

from sim.constants import declare
from sim.world.demand import DAYS_PER_YEAR

MONTHS_PER_YEAR = 12

KOPPEN_TROPICAL_COLDEST_MONTH_MINIMUM_CELSIUS = declare(
    "KOPPEN_TROPICAL_COLDEST_MONTH_MINIMUM_CELSIUS", 18.0,
    kind="physical_constant", unit="degrees Celsius",
    source="Koppen-Geiger class definition (Beck et al. 2018): group A needs every month at or above this",
    confidence="A",
    why="Definitional lower bound of the coldest-month mean in a tropical (A) tile.")

KOPPEN_TEMPERATE_COLDEST_MONTH_MINIMUM_CELSIUS = declare(
    "KOPPEN_TEMPERATE_COLDEST_MONTH_MINIMUM_CELSIUS", -3.0,
    kind="physical_constant", unit="degrees Celsius",
    source="Koppen-Geiger class definition (Beck et al. 2018 uses -3, the original 0): C above, D below",
    confidence="A",
    why="Definitional boundary between temperate (C) and continental (D) tiles; the -3 convention is "
        "the one the tile classes were generated with.")

KOPPEN_GROWING_MONTH_THRESHOLD_CELSIUS = declare(
    "KOPPEN_GROWING_MONTH_THRESHOLD_CELSIUS", 10.0,
    kind="physical_constant", unit="degrees Celsius",
    source="Koppen-Geiger class definition: months at or above this are counted; polar E has none",
    confidence="A",
    why="Definitional: counts the warm months that separate letters b and c, and bounds polar tiles.")

KOPPEN_HOT_SUMMER_WARMEST_MONTH_MINIMUM_CELSIUS = declare(
    "KOPPEN_HOT_SUMMER_WARMEST_MONTH_MINIMUM_CELSIUS", 22.0,
    kind="physical_constant", unit="degrees Celsius",
    source="Koppen-Geiger third letter a: warmest month at or above this",
    confidence="A",
    why="Definitional bound separating third letter a from b.")

KOPPEN_SUBARCTIC_EXTREME_COLDEST_MONTH_MAXIMUM_CELSIUS = declare(
    "KOPPEN_SUBARCTIC_EXTREME_COLDEST_MONTH_MAXIMUM_CELSIUS", -38.0,
    kind="physical_constant", unit="degrees Celsius",
    source="Koppen-Geiger third letter d: coldest month below this",
    confidence="A",
    why="Definitional bound of the very cold continental subclass.")

KOPPEN_WARM_MONTHS_FOR_LETTER_B = declare(
    "KOPPEN_WARM_MONTHS_FOR_LETTER_B", 4.0,
    kind="physical_constant", unit="months at or above the growing threshold",
    source="Koppen-Geiger third letter b: at least four such months; c: one to three",
    confidence="A",
    why="Definitional count; letter c has fewer, so letter c's upper bound uses one month fewer.")

KOPPEN_HOT_DRY_ANNUAL_MEAN_MINIMUM_CELSIUS = declare(
    "KOPPEN_HOT_DRY_ANNUAL_MEAN_MINIMUM_CELSIUS", 18.0,
    kind="physical_constant", unit="degrees Celsius",
    source="Koppen-Geiger dry-climate third letter h: annual mean at or above this; k below",
    confidence="A",
    why="Definitional split of dry (B) tiles into hot and cold.")

MONTHLY_MEAN_LOWEST_ON_EARTH_CELSIUS = declare(
    "MONTHLY_MEAN_LOWEST_ON_EARTH_CELSIUS", -60.0,
    kind="engineering_estimate", unit="degrees Celsius",
    source="Order of the coldest monthly means at Antarctic plateau and Siberian stations",
    confidence="C",
    why="Closes the open cold end of the classes that have no lower bound (D, E).")

MONTHLY_MEAN_HIGHEST_ON_EARTH_CELSIUS = declare(
    "MONTHLY_MEAN_HIGHEST_ON_EARTH_CELSIUS", 38.0,
    kind="engineering_estimate", unit="degrees Celsius",
    source="Order of the hottest monthly means at hot-desert stations",
    confidence="C",
    why="Closes the open hot end of the classes that have no upper bound (A, B, third letter a).")

TROPICAL_COLDEST_MONTH_MAXIMUM_CELSIUS = declare(
    "TROPICAL_COLDEST_MONTH_MAXIMUM_CELSIUS", 28.0,
    kind="engineering_estimate", unit="degrees Celsius",
    source="Order of the coldest-month means of the warmest lowland tropics",
    confidence="C",
    why="Closes the open hot end of the coldest-month interval of tropical (A) and hot dry tiles.")

COLD_CONTINENTAL_COLDEST_MONTH_CELSIUS = declare(
    "COLD_CONTINENTAL_COLDEST_MONTH_CELSIUS", -40.0,
    kind="engineering_estimate", unit="degrees Celsius",
    source="Order of coldest-month means of the coldest inhabited continental interiors (Siberian stations)",
    confidence="C",
    why="Cold end of the coldest-month interval for continental (D), tundra (ET) and cold dry (BWk, BSk) tiles, "
        "which are less cold than the ice cap or the d subclass.")

LATITUDE_OF_POLE_DEGREES = declare(
    "LATITUDE_OF_POLE_DEGREES", 90.0,
    kind="physical_constant", unit="degrees",
    source=None, confidence="A",
    why="Geometry: the latitude scale on which a tile's place between the warm and cold ends is read.")

LATITUDE_PLACEMENT_WITHIN_BOUNDS = declare(
    "LATITUDE_PLACEMENT_WITHIN_BOUNDS", 1.0,
    kind="temporary_heuristic",
    unit="dimensionless (share of the interval between warm and cold ends travelled from equator to pole)",
    source=None, confidence="D",
    why="The class bounds an interval of coldest and warmest month; where inside it a tile sits is "
        "unknown without a climate dataset, so it is placed linearly by absolute latitude (equator at "
        "the warm end, pole at the cold end). Replace with a per-tile monthly temperature field.")


def _place(warm_end, cold_end, latitude):
    """A value between the warm end and the cold end of an interval, by absolute latitude."""
    share = LATITUDE_PLACEMENT_WITHIN_BOUNDS * abs(latitude) / LATITUDE_OF_POLE_DEGREES
    return warm_end + min(1.0, max(0.0, share)) * (cold_end - warm_end)


def _warmest_for_months_above_threshold(coldest, months):
    """Warmest month at which a sinusoidal year spends `months` months at or above the growing threshold
    (mean + amplitude * cos(pi * share of year) equals the threshold, solved for the warmest month)."""
    cosine = math.cos(math.pi * months / MONTHS_PER_YEAR)
    return (2.0 * KOPPEN_GROWING_MONTH_THRESHOLD_CELSIUS - coldest * (1.0 - cosine)) / (1.0 + cosine)


def coldest_month_interval(class_code):
    """(warm end, cold end) of the coldest-month mean the class allows."""
    group = class_code[0]
    if group == "A":
        return TROPICAL_COLDEST_MONTH_MAXIMUM_CELSIUS, KOPPEN_TROPICAL_COLDEST_MONTH_MINIMUM_CELSIUS
    if group == "C":
        return KOPPEN_TROPICAL_COLDEST_MONTH_MINIMUM_CELSIUS, KOPPEN_TEMPERATE_COLDEST_MONTH_MINIMUM_CELSIUS
    if group == "D":
        if class_code.endswith("d"):
            return KOPPEN_SUBARCTIC_EXTREME_COLDEST_MONTH_MAXIMUM_CELSIUS, MONTHLY_MEAN_LOWEST_ON_EARTH_CELSIUS
        return KOPPEN_TEMPERATE_COLDEST_MONTH_MINIMUM_CELSIUS, COLD_CONTINENTAL_COLDEST_MONTH_CELSIUS
    if group == "E":
        if class_code == "EF":
            return -KOPPEN_GROWING_MONTH_THRESHOLD_CELSIUS, MONTHLY_MEAN_LOWEST_ON_EARTH_CELSIUS
        return 0.0, COLD_CONTINENTAL_COLDEST_MONTH_CELSIUS
    if group == "B":
        if class_code.endswith("h"):
            # annual mean at least the hot-dry minimum with the hottest possible summer bounds the winter
            return (TROPICAL_COLDEST_MONTH_MAXIMUM_CELSIUS,
                    2.0 * KOPPEN_HOT_DRY_ANNUAL_MEAN_MINIMUM_CELSIUS - MONTHLY_MEAN_HIGHEST_ON_EARTH_CELSIUS)
        return KOPPEN_GROWING_MONTH_THRESHOLD_CELSIUS, COLD_CONTINENTAL_COLDEST_MONTH_CELSIUS
    raise ValueError("unknown Koppen class %r" % class_code)


def warmest_month_interval(class_code, coldest):
    """(warm end, cold end) of the warmest-month mean the class allows, given the coldest month."""
    group = class_code[0]
    hot = MONTHLY_MEAN_HIGHEST_ON_EARTH_CELSIUS
    growing = KOPPEN_GROWING_MONTH_THRESHOLD_CELSIUS
    third = class_code[-1] if len(class_code) == 3 else ""
    if group == "E":
        if class_code == "EF":
            return 0.0, MONTHLY_MEAN_LOWEST_ON_EARTH_CELSIUS / 2.0
        return growing, 0.0
    if group == "B":
        mean_limit = min(hot, max(growing, 2.0 * KOPPEN_HOT_DRY_ANNUAL_MEAN_MINIMUM_CELSIUS - coldest))
        return (hot, mean_limit) if third == "h" else (mean_limit, growing)
    if third == "a":
        return hot, KOPPEN_HOT_SUMMER_WARMEST_MONTH_MINIMUM_CELSIUS
    if third == "b":
        lowest = _warmest_for_months_above_threshold(coldest, KOPPEN_WARM_MONTHS_FOR_LETTER_B)
        return KOPPEN_HOT_SUMMER_WARMEST_MONTH_MINIMUM_CELSIUS, min(lowest, KOPPEN_HOT_SUMMER_WARMEST_MONTH_MINIMUM_CELSIUS)
    if third in ("c", "d"):
        highest = _warmest_for_months_above_threshold(coldest, KOPPEN_WARM_MONTHS_FOR_LETTER_B - 1.0)
        return max(highest, growing), growing
    return hot, max(coldest, growing)  # group A has no third letter


def representative_extremes(class_code, latitude):
    """(coldest month mean, warmest month mean) in Celsius for a class at a latitude."""
    coldest = _place(*coldest_month_interval(class_code), latitude)
    warmest = _place(*warmest_month_interval(class_code, coldest), latitude)
    return coldest, max(warmest, coldest)


def daily_temperatures(coldest, warmest):
    """A sinusoidal year, one mean temperature per day, coldest at day zero."""
    mean = 0.5 * (coldest + warmest)
    amplitude = 0.5 * (warmest - coldest)
    days = int(DAYS_PER_YEAR)
    return [mean - amplitude * math.cos(2.0 * math.pi * day / days) for day in range(days)]


def monthly_temperatures(coldest, warmest):
    """Twelve monthly means of the sinusoidal year, the coldest first."""
    mean = 0.5 * (coldest + warmest)
    amplitude = 0.5 * (warmest - coldest)
    return [mean - amplitude * math.cos(2.0 * math.pi * month / MONTHS_PER_YEAR)
            for month in range(MONTHS_PER_YEAR)]
