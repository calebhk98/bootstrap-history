"""Quantities inside sentences the engine writes: each goes through here.

A sentence names a mass, an area, a sum of money or a temperature with
`mass_text`, `area_text`, `money_text` or `temperature_text`, never with a
hand-written unit word. Values are given in the unit the engine works in
(tonnes, hectares, the civilisation's coin, degrees Celsius). With no unit
chosen the text is the one the game always wrote; otherwise the number is
converted and the chosen unit's name follows it (units.py).
"""
from typing import Any

from . import units
from .data import money_short, money_word

# native unit id -> (unit id, singular, plural, short word) as the game writes it with no unit chosen.
_NATIVE = {
    "tonne": ("tonne", "tonne", "tonnes", "t"),
    "kilogram": ("kilogram", "kilogram", "kilograms", "kg"),
    "hectare": ("hectare", "hectare", "hectares", "ha"),
    "square_metre": ("square_metre", "square metre", "square metres", "m2"),
    "celsius": ("celsius", "degree Celsius", "degrees Celsius", "C"),
}


def _number(value: float, digits: int, grouped: bool) -> str:
    return format(value, (",.%df" if grouped else ".%df") % digits)


def _unit_words(dimension: str, value: float, shown: tuple, short: bool, digits: int) -> str:
    """The words after a converted number: the symbol, or the name (plural unless the number reads as one)."""
    _, name, symbol = shown
    if short:
        return symbol
    spec = units.registry()["units"].get(units.chosen_units().get(dimension))
    if spec is None or spec.get("label_from") == "civ_currency" or round(value, digits) == 1:
        return name
    return spec.get("plural") or name + "s"


def _text(dimension: str, native: tuple, value: float, sim: Any, digits: int, grouped: bool, short: bool) -> str:
    shown = None
    if sim is not None or dimension != "money":
        shown = units.format_field({"dimension": dimension, "native": native[0]}, value, sim)
    if shown is None:
        word = native[3] if short else native[1] if round(value, digits) == 1 else native[2]
        return "%s %s" % (_number(value, digits, grouped), word)
    return "%s %s" % (_number(shown[0], digits, grouped), _unit_words(dimension, shown[0], shown, short, digits))


def mass_text(amount: float, sim: Any = None, digits: int = 0, grouped: bool = False, short: bool = False,
              unit: str = "tonne") -> str:
    """A mass given in `unit` (tonnes unless said): '12 tonnes' by default ('12 t' when short)."""
    return _text("mass", _NATIVE[unit], amount, sim, digits, grouped, short)


def area_text(amount: float, sim: Any = None, digits: int = 0, grouped: bool = False, short: bool = False,
              unit: str = "hectare") -> str:
    """An area given in `unit` (hectares unless said)."""
    return _text("area", _NATIVE[unit], amount, sim, digits, grouped, short)


def temperature_text(celsius: float, sim: Any = None, digits: int = 0, grouped: bool = False,
                     short: bool = False) -> str:
    return _text("temperature", _NATIVE["celsius"], celsius, sim, digits, grouped, short)


def money_text(amount: float, sim: Any, digits: int = 0, grouped: bool = False, short: bool = False) -> str:
    """A sum in the civilisation's coin: '1200 denarii' ('1200 den' when short) by default."""
    civ = getattr(sim, "civ", None)
    return _text("money", ("civ_coin", money_word(civ), money_word(civ), money_short(civ)), amount, sim, digits, grouped, short)


def per_year(text: str, short: bool = False) -> str:
    """A quantity text as a yearly rate: '12 tonnes a year', or '12 t/year' when short."""
    return "%s/year" % text if short else "%s a year" % text


def mass_rate_text(amount: float, sim: Any = None, digits: int = 0, grouped: bool = False, short: bool = True,
                   unit: str = "tonne") -> str:
    """A mass flow per year: 12 t/year by default, 12 tonnes a year when not short."""
    return per_year(mass_text(amount, sim, digits, grouped, short, unit), short)


def mass_per_area_text(tonnes_per_area: float, sim: Any = None, digits: int = 0, area: str = "square_metre") -> str:
    """A yield per area ('0.0004 tonnes per square metre'; `area` names the area unit it is given per); both parts follow the chosen units."""
    reg = units.registry()
    context = units.unit_context(sim)
    chosen = units.chosen_units().get("area")
    if not chosen or chosen not in reg["units"] or chosen == area:
        return "%s per %s" % (mass_text(tonnes_per_area, sim, digits), _NATIVE[area][1])
    native_areas_per_unit = units.to_base(reg, chosen, 1.0, context) / units.unit_factor(reg["units"][area], context)
    name = units.unit_label(reg["units"][chosen], getattr(sim, "civ", None))[0]
    return "%s per %s" % (mass_text(tonnes_per_area * native_areas_per_unit, sim, digits), name)


def plain_number(value: float, digits: int = 0) -> str:
    """A count, a number of people or of hours with thousands separators: no mass, area, money or temperature."""
    return format(value, ",.%df" % digits)
