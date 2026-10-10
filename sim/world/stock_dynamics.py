"""How held living stock changes in a year: natural increase from a herd that can breed, loss, and what a
smuggler risks.

Pure arithmetic on one quantity; which materials are stock and what their rates are is data
(`data/world/living_stock.json`), read by the engine, never named here.
"""


def next_units(units, natural_increase, annual_loss, breeding_minimum, growth_room=None):
    """Units held a year on. A holding below `breeding_minimum` cannot breed, so it gains nothing
    and still suffers its loss; increase and loss are fractions of the holding. `growth_room`, when
    given, is the most the holding may gain in the year (what its feed or pasture will carry); a
    herd with no room gains nothing."""
    units = float(units)
    grown = units * natural_increase if units >= breeding_minimum else 0.0
    if growth_room is not None:
        grown = min(grown, max(0.0, float(growth_room)))
    return max(0.0, units + grown - units * annual_loss)


def feed_room(capacity, held):
    """What a feed supply that carries `capacity` still has room for beside `held`; never negative."""
    return max(0.0, float(capacity) - float(held))


def catch_chance(state_capacity, visibility):
    """Chance a theft of stock is found out: the owning state's reach (the share of its offences it
    catches) times how visible the taking is, both 0..1."""
    return min(1.0, max(0.0, float(state_capacity)) * min(1.0, max(0.0, float(visibility))))


def is_caught(draw, chance):
    """Whether a uniform draw in 0..1 falls inside the chance of being caught."""
    return float(draw) < float(chance)
