"""An order to sell stock at the year's clearing: what refuses it. Plain functions."""
from sim.refusal import Refusal

from .units_prose import mass_text

HELD_TOLERANCE = 1e-9


def asks_more_than_held(asked, held):
    return asked > held + HELD_TOLERANCE


def no_price_refusal(material):
    return Refusal("no_price", "%s has no price here, so it cannot be sold. Nothing was sold." % material,
                   material=material)


def not_enough_held_refusal(material, held, asked):
    return Refusal("not_enough_held", "you hold %s of %s, not %s. Nothing was sold." % (
        mass_text(held), material, mass_text(asked)), material=material, held_tonnes=held, asked_tonnes=asked)
