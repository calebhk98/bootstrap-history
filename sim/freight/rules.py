"""The freight module's rules as plain functions of plain values: what a leg costs once the carrier's food rides on it,
how one-sided the flows are, who is owed the dues of a haul, and the markup a haul adds to a book price."""
import dataclasses
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from sim.geography.api import cargo_cost, freight_cost, provisions, sea_freight
from sim.unit_conversions import KILOGRAMS_PER_TONNE

from .constants import SEA_MODE
from .route import Route


def freight_markup(book_price_per_kg: Optional[float], haul_cost_per_tonne: Optional[float], cargo_cost_share: float) -> float:
    """Multiplier on a material's book price for carrying it here: one plus the haul per kilogram over the price
    plus the cargo's own interest and spoilage share. One for a material with no price or no haul."""
    if not book_price_per_kg or book_price_per_kg <= 0:
        return 1.0
    freight_per_kg = (haul_cost_per_tonne or 0.0) / KILOGRAMS_PER_TONNE
    if freight_per_kg <= 0:
        return 1.0
    return 1.0 + freight_per_kg / book_price_per_kg + cargo_cost_share


def dues_money_per_tonne(dues_hours: Mapping[str, float], wage: float) -> Dict[str, float]:
    """{mode: money per tonne} of the modes that levy dues, the hours per tonne paid at the carrier's wage."""
    return {mode: hours * wage for mode, hours in dues_hours.items() if hours > 0.0}


def handling_money_per_tonne(dues_hours: Mapping[str, float], wage: float, port_mode: str, port_handling_hours: float) -> Dict[str, float]:
    """{mode: money per tonne} charged once per leg: each mode's dues, and port handling on top at `port_mode`."""
    costs = dues_money_per_tonne(dues_hours, wage)
    costs[port_mode] = costs.get(port_mode, 0.0) + port_handling_hours * wage
    return costs


def dues_payments(owed: Mapping[Any, float], limit: Optional[float]) -> List[Tuple[Any, float]]:
    """[(holder, money)] the payer pays, holders in sorted order, scaled down so the total never exceeds `limit`;
    a holder owed nothing is left out."""
    total = sum(owed.values())
    scale = 1.0 if limit is None or total <= limit else max(0.0, limit) / total
    payments = []
    for holder in sorted(owed):
        amount = owed[holder] * scale
        if amount > 0.0:
            payments.append((holder, amount))
    return payments


def foreign_flow_imbalance(book_entries: Iterable[Mapping[str, float]]) -> float:
    """How one-sided last year's trade with a partner was, from its book entries: 1 when nothing flowed back (or
    nothing is known), 0 when tonnes in and out match."""
    entries = list(book_entries)
    tonnes_out = sum(max(0.0, entry.get("trade_tonnes", 0.0)) for entry in entries)
    tonnes_in = sum(max(0.0, -entry.get("trade_tonnes", 0.0)) for entry in entries)
    return freight_cost.imbalance_of_flows(tonnes_out, tonnes_in)


def restock_days(mode: str) -> Optional[float]:
    """Days of travel between places a mode's carrier restocks; none for a hull at sea."""
    return None if mode == SEA_MODE else provisions.RESTOCK_INTERVAL_DAYS


def share_in_rate(mode: str, base_rates: Optional[Mapping[str, float]], searched_rates: Optional[Mapping[str, float]]) -> float:
    """Share of lift a searched rate already divides a mode's base rate by (1 when it carries none)."""
    if not base_rates or not searched_rates:
        return 1.0
    base, searched = base_rates.get(mode, 0.0), searched_rates.get(mode, 0.0)
    return base / searched if 0.0 < base and 0.0 < searched < float("inf") else 1.0


def delivered_share(models: Mapping[str, tuple], mode: str, route: Optional[Route]) -> float:
    """Share of a mode's lift that arrives as cargo on the legs of `route` in that mode (the mean leg; with no route
    yet, a land carrier's stage and a hull's none): what the route search divides the mode's rate by."""
    if mode not in models:
        return 1.0
    days = restock_days(mode)
    legs = [leg.distance_km for leg in (route.legs if route else ()) if leg.mode == mode]
    if legs:
        distance = sum(legs) / len(legs)
    else:
        distance = 0.0 if days is None else float("inf")
    return provisions.restocked_share(models[mode][0], distance, days)


def route_with_provisions(route: Route, models: Mapping[str, tuple], handling: Mapping[str, float],
                          base_rates: Optional[Mapping[str, float]] = None, searched_rates: Optional[Mapping[str, float]] = None) -> Route:
    """The route with each leg priced per tonne delivered: the crew's and animals' food and water ride on the carrier
    and take lift from the cargo (`provisions.restocked_share`), a land carrier restocking every few days and a hull
    at the leg's ends. Handling is not scaled; a stage the carrier cannot provision makes the leg impassable. A leg
    found on `searched_rates` (the `base_rates` already over the mean leg's share) is re-priced at its own share, so
    the food is counted once."""
    legs = []
    for leg in route.legs:
        if leg.mode not in models:
            legs.append(leg)
            continue
        fee = handling.get(leg.mode, 0.0)
        share = provisions.restocked_share(models[leg.mode][0], leg.distance_km, restock_days(leg.mode))
        counted = share_in_rate(leg.mode, base_rates, searched_rates)
        legs.append(dataclasses.replace(
            leg, cost_per_tonne=fee + max(0.0, leg.cost_per_tonne - fee) * counted / share
            if share > 0.0 else float("inf")))
    return Route(tuple(legs))


def cargo_loss_share(route: Optional[Route], daily_loss_by_mode: Mapping[str, float], hull_loss_per_thousand_km: float) -> float:
    """Share of cargo lost on the route: the hull loss rate over its sea legs, and the daily loss of a herd over its
    legs on the road."""
    if route is None:
        return 0.0
    sailed_km = sum(leg.distance_km for leg in route.legs if leg.mode == SEA_MODE)
    on_the_road = [cargo_cost.daily_loss_share(daily_loss_by_mode[leg.mode], leg.travel_days)
                   for leg in route.legs if leg.mode in daily_loss_by_mode]
    at_sea = cargo_cost.sea_loss_share(hull_loss_per_thousand_km, sailed_km)
    return cargo_cost.lost_share(at_sea, *on_the_road) if on_the_road else at_sea


def sea_crew_hands(sea_wage: float, grain_price: float, wood_price: float) -> float:
    """Hands a merchant hull sails with: what its rig needs, and the defenders worth their keep against the expected
    loss of the hull and a cargo of the cheapest grain (the grain price stands in for the cargo, which a carrier's
    rate does not name)."""
    hull_inputs = sea_freight.sailing_freight_physical_inputs()
    rig = sea_freight.crew_to_sail(hull_inputs.cargo_tonnes)
    hull_value = hull_inputs.cargo_tonnes * sea_freight.HULL_TIMBER_KG_PER_CARGO_TONNE * wood_price
    cargo_value = hull_inputs.cargo_tonnes * KILOGRAMS_PER_TONNE * grain_price
    defender_cost_per_day = (sea_freight.CREW_HOURS_AT_SEA_PER_DAY * sea_wage
                             + provisions.PERSON_GRAIN_RATION_KG_PER_DAY * grain_price)
    return rig + sea_freight.defenders_to_hire(rig, defender_cost_per_day, hull_value + cargo_value)
