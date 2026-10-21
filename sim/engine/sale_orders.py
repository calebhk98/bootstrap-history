"""A sale of stock at the market: how much sells, what refuses it, and what the reply reports. Plain functions."""
from sim.refusal import Refusal

from .units_prose import mass_text

HELD_TOLERANCE = 1e-9


def tonnes_sold(asked, held, market_room):
    """An order is cut to what is held and to what the market will still take this year."""
    return min(asked, held, market_room)


def asks_more_than_held(asked, held):
    return asked > held + HELD_TOLERANCE


def not_enough_held_refusal(material, held, asked):
    return Refusal("not_enough_held", "you hold %s of %s, not %s. Nothing was sold." % (
        mass_text(held), material, mass_text(asked)), material=material, held_tonnes=held, asked_tonnes=asked)


def market_full_refusal(material, held, market_room):
    return Refusal("market_full", "the market has taken all of %s that it will absorb this year. Nothing was sold."
                   % material, material=material, held_tonnes=held, market_room_tonnes=market_room)


def sale_reply(material, sold, asked, held_after, room_after, capital):
    """The reply of a sale: what sold, and the holding and market room the next sale draws on."""
    return {"ok": True, "material": material, "sold_tonnes": sold, "asked_tonnes": asked,
            "stock_on_hand_tonnes": held_after, "market_will_still_take_tonnes": room_after,
            "capital": round(capital, 1)}
