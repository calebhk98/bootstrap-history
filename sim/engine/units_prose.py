"""Quantities inside sentences the engine writes: each goes through here.

A sentence names a mass, an area, a sum of money or a temperature with `mass_text`, `area_text`, `money_text` or
`temperature_text`, never with a hand-written unit word. The text is written by the scenario module's functions
(sim/scenario/quantity_text.py); these take the game, or none, and hand over what the words are read from: the
civilisation's coin, the unit registry and the unit the player chose."""
from typing import Any

from sim.scenario.api import Display, quantity_text

from . import units

_NATIVE = quantity_text.NATIVE
per_year = quantity_text.per_year
plain_number = quantity_text.plain_number


def _display(sim: Any) -> Display:
    civ = getattr(sim, "civ", None)   # sim is None when a tool renders prose without a game
    return Display(civ, units.registry(), units.chosen_units(), lambda: units.unit_context(sim))


def mass_text(amount: float, sim: Any = None, digits: int = 0, grouped: bool = False, short: bool = False,
              unit: str = "tonne") -> str:
    """A mass given in `unit` (tonnes unless said): '12 tonnes' by default ('12 t' when short)."""
    return quantity_text.mass_text(amount, _display(sim), digits, grouped, short, unit, sim is not None)


def area_text(amount: float, sim: Any = None, digits: int = 0, grouped: bool = False, short: bool = False,
              unit: str = "hectare") -> str:
    """An area given in `unit` (hectares unless said)."""
    return quantity_text.area_text(amount, _display(sim), digits, grouped, short, unit, sim is not None)


def temperature_text(celsius: float, sim: Any = None, digits: int = 0, grouped: bool = False,
                     short: bool = False) -> str:
    return quantity_text.temperature_text(celsius, _display(sim), digits, grouped, short, sim is not None)


def money_text(amount: float, sim: Any, digits: int = 0, grouped: bool = False, short: bool = False) -> str:
    """A sum in the civilisation's coin: '1200 denarii' ('1200 den' when short) by default."""
    return quantity_text.money_text(amount, _display(sim), digits, grouped, short, sim is not None)


def mass_rate_text(amount: float, sim: Any = None, digits: int = 0, grouped: bool = False, short: bool = True,
                   unit: str = "tonne") -> str:
    """A mass flow per year: 12 t/year by default, 12 tonnes a year when not short."""
    return quantity_text.mass_rate_text(amount, _display(sim), digits, grouped, short, unit, sim is not None)


def mass_per_area_text(tonnes_per_area: float, sim: Any = None, digits: int = 0, area: str = "square_metre") -> str:
    """A yield per area ('0.0004 tonnes per square metre'; `area` names the area unit it is given per); both parts follow the chosen units."""
    return quantity_text.mass_per_area_text(tonnes_per_area, _display(sim), digits, area, sim is not None)
