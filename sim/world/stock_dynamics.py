"""How held living stock changes in a year: natural increase from a herd that can breed, and loss.

Pure arithmetic on one quantity; which materials are stock and what their rates are is data
(`data/world/living_stock.json`), read by the engine, never named here.
"""


def next_units(units, natural_increase, annual_loss, breeding_minimum):
    """Units held a year on. A holding below `breeding_minimum` cannot breed, so it gains nothing
    and still suffers its loss; increase and loss are fractions of the holding."""
    units = float(units)
    grown = units * natural_increase if units >= breeding_minimum else 0.0
    return max(0.0, units + grown - units * annual_loss)
