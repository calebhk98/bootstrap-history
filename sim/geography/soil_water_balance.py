"""A tile's yearly water balance: rain against the evaporation its temperature and sun allow (Complaint 543).

Standalone: pure functions of numbers. Evaporation is the FAO-56 Hargreaves form on twelve monthly temperatures that follow
a sine between the coldest and warmest month, with the sun's extraterrestrial radiation for the tile's latitude. The
ratio of rain to that evaporation is UNEP's aridity index.
"""
import math

from sim.unit_conversions import CIVIL_DAYS_PER_YEAR as DAYS_PER_YEAR

SOLAR_CONSTANT_MJ_PER_SQUARE_METRE_MINUTE = 0.0820
MINUTES_PER_DAY = 24.0 * 60.0
MM_PER_MJ_PER_SQUARE_METRE = 0.408          # one over the latent heat of vaporisation, 2.45 MJ per kg
MONTHS_PER_YEAR = 12
HARGREAVES_COEFFICIENT = 0.0023
HARGREAVES_TEMPERATURE_OFFSET_C = 17.8
MID_MONTH_DAYS_OF_YEAR = tuple(int(15 + 30.4 * month) for month in range(MONTHS_PER_YEAR))


def extraterrestrial_radiation_mm_per_day(latitude_degrees: float, day_of_year: int) -> float:
    """FAO-56 eq 21 with dr (eq 23), declination (eq 24) and sunset hour angle (eq 25), as equivalent evaporation."""
    latitude = math.radians(latitude_degrees)
    angle = 2.0 * math.pi * day_of_year / DAYS_PER_YEAR
    distance = 1.0 + 0.033 * math.cos(angle)
    declination = 0.409 * math.sin(angle - 1.39)
    cosine_hour_angle = max(-1.0, min(1.0, -math.tan(latitude) * math.tan(declination)))
    sunset = math.acos(cosine_hour_angle)
    megajoules = (MINUTES_PER_DAY / math.pi * SOLAR_CONSTANT_MJ_PER_SQUARE_METRE_MINUTE * distance
                  * (sunset * math.sin(latitude) * math.sin(declination)
                     + math.cos(latitude) * math.cos(declination) * math.sin(sunset)))
    return megajoules * MM_PER_MJ_PER_SQUARE_METRE


def monthly_temperatures_c(mean_c: float, coldest_month_c: float, warmest_month_c: float):
    """Twelve monthly means: a sine through the coldest and warmest month about the annual mean, coldest at month zero."""
    amplitude = max(0.0, (warmest_month_c - coldest_month_c) / 2.0)
    return [mean_c - amplitude * math.cos(2.0 * math.pi * month / MONTHS_PER_YEAR) for month in range(MONTHS_PER_YEAR)]


def evaporation_mm_per_year(latitude_degrees: float, mean_c: float, coldest_month_c: float, warmest_month_c: float,
                            daily_range_c: float) -> float:
    """Hargreaves reference evaporation summed over the months (FAO-56 eq 52); months below freezing evaporate nothing.
    `daily_range_c` is the daily maximum less minimum. The coldest month falls in the winter of the tile's hemisphere."""
    northern = latitude_degrees >= 0.0
    total = 0.0
    for month, temperature in enumerate(monthly_temperatures_c(mean_c, coldest_month_c, warmest_month_c)):
        day = MID_MONTH_DAYS_OF_YEAR[month] + (0 if northern else int(DAYS_PER_YEAR / 2))
        radiation = extraterrestrial_radiation_mm_per_day(latitude_degrees, int(day % DAYS_PER_YEAR) or 1)
        if temperature <= 0.0:
            continue
        per_day = (HARGREAVES_COEFFICIENT * (temperature + HARGREAVES_TEMPERATURE_OFFSET_C)
                   * math.sqrt(daily_range_c) * radiation)
        total += max(0.0, per_day) * DAYS_PER_YEAR / MONTHS_PER_YEAR
    return total


def aridity_index(rain_mm: float, evaporation_mm: float):
    """Rain over evaporation (UNEP aridity index); None when nothing evaporates, so the caller must choose."""
    return None if evaporation_mm <= 0.0 else rain_mm / evaporation_mm


def months_at_or_above(threshold_c: float, mean_c: float, coldest_month_c: float, warmest_month_c: float) -> float:
    """Months of the year whose temperature, on the same sine, is at or above `threshold_c` (fractional)."""
    steps = 120
    amplitude = max(0.0, (warmest_month_c - coldest_month_c) / 2.0)
    above = sum(1 for step in range(steps)
                if mean_c - amplitude * math.cos(2.0 * math.pi * (step + 0.5) / steps) >= threshold_c)
    return MONTHS_PER_YEAR * above / steps
