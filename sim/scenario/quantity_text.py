"""Quantities inside sentences: a mass, an area, a sum of money or a number, written in the units the player chose.

A sentence names a quantity with these functions, never with a hand-written unit word. Values are given in the unit the
game works in (tonnes, hectares, the civilisation's coin). With no unit chosen the text is the one the game always
wrote; otherwise the number is converted and the chosen unit's name follows it. Every function takes a `Display`: what
the words and conversions are read from."""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional

from .unit_math import from_base, money_short, money_word, to_base, unit_factor, unit_label

# native unit id -> (unit id, singular, plural, short word) as the game writes it with no unit chosen.
NATIVE = {
	"tonne": ("tonne", "tonne", "tonnes", "t"),
	"kilogram": ("kilogram", "kilogram", "kilograms", "kg"),
	"hectare": ("hectare", "hectare", "hectares", "ha"),
	"square_metre": ("square_metre", "square metre", "square metres", "m2"),
	"celsius": ("celsius", "degree Celsius", "degrees Celsius", "C"),
}


@dataclass
class Display:
	"""What a text is written from: the civilisation (its coin words), the unit registry, the unit chosen per dimension, and
	the per-game numbers some units need (asked only when a conversion happens)."""
	civilisation: Optional[Mapping[str, Any]]
	registry: Mapping[str, Any]
	chosen: Mapping[str, str]
	context: Callable[[], Dict[str, float]]


def number(value: float, digits: int, grouped: bool) -> str:
	return format(value, (",.%df" if grouped else ".%df") % digits)


def plain_number(value: float, digits: int = 0) -> str:
	"""A count, a number of people or of hours with thousands separators: no mass, area, money or temperature."""
	return format(value, ",.%df" % digits)


def converted(dimension: str, native_unit: str, value: float, display: Display):
	"""(value, unit name, symbol) of a native-unit quantity in the chosen unit of its dimension, or None to write it as native."""
	unit = display.chosen.get(dimension)
	registry = display.registry
	if not unit or unit == native_unit or unit not in registry["units"]:
		return None
	context = display.context()
	base = to_base(registry, native_unit, value, context)
	name, symbol = unit_label(registry["units"][unit], display.civilisation)
	return from_base(registry, unit, base, context), name, symbol


def unit_words(display: Display, dimension: str, value: float, shown: tuple, short: bool, digits: int) -> str:
	"""The words after a converted number: the symbol, or the name (plural unless the number reads as one)."""
	_, name, symbol = shown
	if short:
		return symbol
	spec = display.registry["units"].get(display.chosen.get(dimension))
	if spec is None or spec.get("label_from") == "civ_currency" or round(value, digits) == 1:
		return name
	return spec.get("plural") or name + "s"


def quantity_text(dimension: str, native: tuple, value: float, display: Display, digits: int, grouped: bool, short: bool,
                  in_game: bool = True) -> str:
	"""`in_game` False writes money as native (there is no coin without a game)."""
	shown = None
	if in_game or dimension != "money":
		shown = converted(dimension, native[0], value, display)
	if shown is None:
		word = native[3] if short else native[1] if round(value, digits) == 1 else native[2]
		return "%s %s" % (number(value, digits, grouped), word)
	return "%s %s" % (number(shown[0], digits, grouped), unit_words(display, dimension, shown[0], shown, short, digits))


def mass_text(amount: float, display: Display, digits: int = 0, grouped: bool = False, short: bool = False,
              unit: str = "tonne", in_game: bool = True) -> str:
	"""A mass given in `unit` (tonnes unless said): '12 tonnes' by default ('12 t' when short)."""
	return quantity_text("mass", NATIVE[unit], amount, display, digits, grouped, short, in_game)


def area_text(amount: float, display: Display, digits: int = 0, grouped: bool = False, short: bool = False,
              unit: str = "hectare", in_game: bool = True) -> str:
	"""An area given in `unit` (hectares unless said)."""
	return quantity_text("area", NATIVE[unit], amount, display, digits, grouped, short, in_game)


def temperature_text(celsius: float, display: Display, digits: int = 0, grouped: bool = False, short: bool = False,
                     in_game: bool = True) -> str:
	return quantity_text("temperature", NATIVE["celsius"], celsius, display, digits, grouped, short, in_game)


def money_text(amount: float, display: Display, digits: int = 0, grouped: bool = False, short: bool = False,
               in_game: bool = True) -> str:
	"""A sum in the civilisation's coin: '1200 denarii' ('1200 den' when short) by default."""
	civilisation = display.civilisation
	native = ("civ_coin", money_word(civilisation), money_word(civilisation), money_short(civilisation))
	return quantity_text("money", native, amount, display, digits, grouped, short, in_game)


def per_year(text: str, short: bool = False) -> str:
	"""A quantity text as a yearly rate: '12 tonnes a year', or '12 t/year' when short."""
	return "%s/year" % text if short else "%s a year" % text


def mass_rate_text(amount: float, display: Display, digits: int = 0, grouped: bool = False, short: bool = True,
                   unit: str = "tonne", in_game: bool = True) -> str:
	"""A mass flow per year: 12 t/year by default, 12 tonnes a year when not short."""
	return per_year(mass_text(amount, display, digits, grouped, short, unit, in_game), short)


def mass_per_area_text(tonnes_per_area: float, display: Display, digits: int = 0, area: str = "square_metre",
                       in_game: bool = True) -> str:
	"""A yield per area ('0.0004 tonnes per square metre'; `area` names the area unit it is given per); both parts follow the chosen units."""
	registry = display.registry
	context = display.context()
	chosen = display.chosen.get("area")
	if not chosen or chosen not in registry["units"] or chosen == area:
		return "%s per %s" % (mass_text(tonnes_per_area, display, digits, in_game=in_game), NATIVE[area][1])
	native_areas_per_unit = to_base(registry, chosen, 1.0, context) / unit_factor(registry["units"][area], context)
	name = unit_label(registry["units"][chosen], display.civilisation)[0]
	return "%s per %s" % (mass_text(tonnes_per_area * native_areas_per_unit, display, digits, in_game=in_game), name)
