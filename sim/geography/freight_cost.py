"""What a tonne-km costs a carrier that must be paid for, kept, crewed and brought home empty.

A carrier's physical inputs (`FreightPhysicalInputs`: feed, crew hours, wear per tonne-km, the
ground covered per day) become money here: running costs (feed and crew at their prices), the
carrier's capital (interest at the market rate plus depreciation, spread over the tonne-km it
lifts in the days it works each year), the chance of losing the carrier, and the return leg
when flows are one-sided.

Standalone: prices, wages and the rate come in as numbers.
"""
from dataclasses import dataclass

from sim.constants import declare

from . import provisions

LAND_WORKING_DAYS_PER_YEAR = declare(
    "LAND_WORKING_DAYS_PER_YEAR", 250.0, kind="engineering_estimate",
    unit="days of travel per year for a cart or pack string",
    source="Draught animals rest on feast days, in the sowing and harvest peaks and in "
           "the mud season; carters and muleteers worked most of the rest of the year.",
    confidence="C",
    why="The days a land carrier earns in a year; its capital is spread over those days' "
        "tonne-km.")
ANIMAL_WORKING_LIFE_YEARS = declare(
    "ANIMAL_WORKING_LIFE_YEARS", 10.0, kind="engineering_estimate",
    unit="years", source="Draught oxen worked from about four years old to ten or twelve; "
    "mules longer.", confidence="C",
    why="An animal's price is written off over its working life.")


@dataclass(frozen=True)
class CarrierPrices:
    """Money prices of one carrier unit as `FreightPhysicalInputs` describes it: the vehicle
    (cart, barge, saddles, hull), the animals that move it and the animals' working life."""
    vehicle: float
    animals: float = 0.0


def return_leg_factor(imbalance: float) -> float:
    """Round-trip cost per loaded tonne-km relative to one loaded leg: 1 when flows balance, 2 when
    the carrier comes back empty. `imbalance` is |out - in| / (out + in), in [0, 1]."""
    return 1.0 + max(0.0, min(1.0, imbalance))


def imbalance_of_flows(tonnes_out: float, tonnes_in: float) -> float:
    """How one-sided a trade is; fully one-sided when nothing is known to flow back."""
    total = tonnes_out + tonnes_in
    return 1.0 if total <= 0.0 else abs(tonnes_out - tonnes_in) / total


def capital_money_per_tonne_km(inputs, prices: CarrierPrices, annual_rate: float,
                               working_days_per_year: float) -> float:
    """Interest on the carrier's price plus its depreciation, per loaded tonne-km."""
    tonne_km_per_year = inputs.tonne_km_per_day * working_days_per_year
    if tonne_km_per_year <= 0.0:
        raise ValueError("a carrier that never works has no freight rate")
    interest = (prices.vehicle + prices.animals) * annual_rate
    animal_depreciation = prices.animals / ANIMAL_WORKING_LIFE_YEARS
    return ((interest + animal_depreciation) / tonne_km_per_year
            + prices.vehicle * inputs.vehicle_wear_fraction_per_tonne_km)


def loss_money_per_tonne_km(inputs, prices: CarrierPrices, loss_per_thousand_km: float) -> float:
    """The carrier's expected replacement cost per loaded tonne-km at a given loss rate."""
    return (loss_per_thousand_km / 1000.0) * (prices.vehicle + prices.animals) / inputs.cargo_tonnes


def freight_money_per_tonne_km(inputs, feed_price_per_kg: float, wage_per_hour: float,
                               prices: CarrierPrices, annual_rate: float,
                               working_days_per_year: float, imbalance: float = 1.0,
                               loss_per_thousand_km: float = 0.0) -> float:
    """Money to move a tonne one km, the carrier's whole round trip charged to the loaded leg.

    Running and capital costs accrue over the round trip, so both scale with `return_leg_factor`.
    Losses accrue only on the loaded leg's hazard, counted once per loaded tonne-km."""
    running = (inputs.feed_kg_per_tonne_km * feed_price_per_kg
               + inputs.driver_hours_per_tonne_km * wage_per_hour)
    capital = capital_money_per_tonne_km(inputs, prices, annual_rate, working_days_per_year)
    losses = loss_money_per_tonne_km(inputs, prices, loss_per_thousand_km)
    return (running + capital) * return_leg_factor(imbalance) + losses


def leg_money_per_tonne(money_per_tonne_km: float, inputs, distance_km: float,
                        restock_days=None) -> float:
    """Money to deliver a tonne over a leg: the rate over the distance, divided by the share of the
    carrier's lift left for cargo once the crew and animals' food and water are carried between
    restocking places (`restock_days` of travel apart; the whole leg when None). Infinite where a
    stage is longer than the carrier can provision."""
    share = provisions.restocked_share(inputs, distance_km, restock_days)
    return float("inf") if share <= 0.0 else money_per_tonne_km * distance_km / share


def days_on_leg(distance_km: float, inputs) -> float:
    """Days of travel over a leg at the carrier's pace."""
    return distance_km / inputs.distance_per_day_km
