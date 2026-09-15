"""Regression coverage for civilization-specific, explicit opening knowledge."""
from .harness import *  # noqa: F401,F403


_expected_grants = {
    "rome_100ad": 139,
    "han_china_100ad": 106,
    "norse_900ad": 92,
    "england_1300": 114,
    "mexica_1500": 33,
}
for _civ, _count in _expected_grants.items():
    _start = sim(civ=_civ)
    check("%s grants exactly its declared starting state" % _civ,
          _start.granted == set(_start.civ["starting_techs"])
          and len(_start.granted) == _count,
          sorted(_start.granted))

# These are free Roman/Mediterranean nodes in the universal graph.  Their
# prerequisites being empty or already known must not silently confer them on
# a scenario that does not declare them.
_mexica = sim(civ="mexica_1500")
_contaminants = {
    "civ_glass_windows", "civ_iron_wrought", "civ_lead_pipes",
    "fin_coinage", "lnd_wheel_spoked", "mat_wrought_iron",
}
check("Mexica start does not inherit Old World ambient technologies",
      not (_contaminants & _mexica.done),
      sorted(_contaminants & _mexica.done))

_han = sim(civ="han_china_100ad")
check("Han starts with lodestone knowledge, not a navigational compass",
      "sea_lodestone" in _han.done and "sea_magnetic_compass" not in _han.done,
      sorted({"sea_lodestone", "sea_magnetic_compass"} & _han.done))

# Ownership must stay stable after time advances; zero-cost descendants are
# projects, not a delayed ambient gift.
_before = set(_mexica.granted)
_mexica.step()
check("advancing time does not infer additional starting ownership",
      _mexica.granted == _before, sorted(_mexica.granted - _before))
