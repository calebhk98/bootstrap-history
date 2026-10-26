"""Joining a seat from data: what a template may ask for and what it costs."""
from typing import Any, Callable, Iterable, List, Mapping, Optional

from sim.refusal import Refusal

COUNTRY_SEAT = "country"   # a seat holding a country's government, with no household or founder of its own


def unknown_starting_techs(template: Mapping[str, Any], tree: Iterable[str]) -> List[str]:
    """The starting technologies the template lists that the tree lacks, sorted."""
    known = set(tree)
    return sorted(tech_id for tech_id in template.get("starting_techs") or () if tech_id not in known)


def unknown_techs_refusal(seat_id: str, missing: List[str]) -> Refusal:
    return Refusal("unknown_starting_techs", "seat %r lists unknown starting technologies: %s" % (seat_id, ", ".join(missing)),
                   seat=seat_id, technologies=missing)


def capital_of(template: Mapping[str, Any], price_index: float, kit_capital: Callable[[str], float]) -> float:
    """The seat's opening purse at this society's prices: a stated `capital`, else a kit's, else none."""
    if template.get("capital") is not None:
        return float(template["capital"]) * price_index
    if template.get("kit"):
        return kit_capital(template["kit"]) * price_index
    return 0.0


def country_of(template: Mapping[str, Any], home_country: str) -> str:
    """The country a country seat holds: the one named, else the game's own."""
    return template.get("country") or home_country


def no_government_refusal(seat_id: str, country: str) -> Refusal:
    return Refusal("no_government", "seat %r: no government of %r to hold" % (seat_id, country), seat=seat_id, country=country)


def country_seat_template(template: Mapping[str, Any], country: str, home_country: str) -> dict:
    """The template with its country stated as the seat keeps it: None for the game's own country."""
    return dict(template, country=None if country == home_country else country)


def founder_years(immortal: bool, minimum: float, mean: float, spread: float, draw: Callable[[float, float], float]) -> float:
    """Years a new founder has left: effectively unlimited in an immortal run, else drawn like the first."""
    if immortal:
        return 1e9
    return max(minimum, draw(mean, spread))


def cast_templates(cast: Optional[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    """The seats a civilisation's cast lists for the start of the game."""
    return list((cast or {}).get("seats") or ())
