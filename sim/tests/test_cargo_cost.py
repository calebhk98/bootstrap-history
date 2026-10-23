"""Freight prices the cargo as well as the carrier, for foreign and domestic routes alike
(Complaints/326, 340): interest on the cargo's value over the voyage, spoilage by duration,
expected loss at sea, and domestic freight that includes the carrier's capital and empty return."""

QUICK_TOPIC = True
from .harness import *  # noqa: F401,F403

from sim.world import trader_response
from sim.geography import cargo_cost, freight_cost, transport
from sim.engine.haul_route import Leg, Route, domestic_cargo_cost_share

RATE = 0.1
check("a longer voyage charges more interest on the same cargo value",
      cargo_cost.interest_money(1000.0, RATE, 0.5) > cargo_cost.interest_money(1000.0, RATE, 0.1) > 0.0
      and abs(cargo_cost.interest_money(1000.0, RATE, 0.5) - 50.0) < 1e-9, None)
check("a dearer cargo pays proportionally more interest over the same voyage",
      abs(cargo_cost.interest_money(2000.0, RATE, 0.3) - 2.0 * cargo_cost.interest_money(1000.0, RATE, 0.3)) < 1e-9,
      None)
check("a perishable cargo loses a share that grows with the days; an imperishable one loses none",
      0.0 < cargo_cost.spoilage_share(5.0, 0.01) < cargo_cost.spoilage_share(5.0, 0.2) < 1.0
      and cargo_cost.spoilage_share(0.0, 5.0) == 0.0, None)
rates = cargo_cost.spoilage_rates()
check("spoilage rates are data: milk spoils far faster than grain, metal not at all",
      rates["milk_kg"] > 50.0 * rates["wheat_kg"] > 0.0 and rates.get("iron_bar_kg", 0.0) == 0.0, rates)
check("sea legs charge expected cargo loss by the distance sailed; land legs none",
      cargo_cost.sea_loss_share(0.01, 4000.0) > cargo_cost.sea_loss_share(0.01, 1000.0) > 0.0
      and cargo_cost.sea_loss_share(0.01, 0.0) == 0.0, None)
check("the merchants' share of price rises with spoilage over the same voyage",
      trader_response.cost_share_of_price(0.03, cargo_cost.lost_share(0.3, 0.0), RATE, 0.5)
      > trader_response.cost_share_of_price(0.03, 0.0, RATE, 0.5), None)
check("a durable good's lost share is unchanged by naming it: no spoilage leaves only the route's loss",
      abs(cargo_cost.lost_share(0.07, cargo_cost.spoilage_share(0.0, 3.0)) - 0.07) < 1e-12, None)

# --- the carrier's freight rate, on a cart built from physics and stated prices (no game).
CART_INPUTS = transport.draught_freight_physical_inputs(transport.OX, 2, transport.CART, transport.DIRT_TRACK)
CART_PRICES = freight_cost.CarrierPrices(vehicle=50.0, animals=200.0)
FEED_PRICE, WAGE = 0.02, 0.05
WORKING_DAYS = freight_cost.LAND_WORKING_DAYS_PER_YEAR


def cart_rate(annual_rate=RATE, imbalance=1.0):
    return freight_cost.freight_money_per_tonne_km(
        CART_INPUTS, FEED_PRICE, WAGE, CART_PRICES, annual_rate, WORKING_DAYS, imbalance)


running = CART_INPUTS.feed_kg_per_tonne_km * FEED_PRICE + CART_INPUTS.driver_hours_per_tonne_km * WAGE
capital = freight_cost.capital_money_per_tonne_km(CART_INPUTS, CART_PRICES, RATE, WORKING_DAYS)
check("freight per tonne-km is the round trip of running cost and carrier capital when the carrier returns empty",
      abs(cart_rate() - 2.0 * (running + capital)) < 1e-12 and capital > 0.0, (cart_rate(), running, capital))
check("...which is more than twice its feed and driver, since oxen and cart are capital",
      cart_rate() > 2.0 * running, (cart_rate(), running))
check("freight with balanced flows is cheaper than with a one-sided flow",
      abs(cart_rate(imbalance=0.0) - (running + capital)) < 1e-12 and cart_rate(imbalance=0.0) < cart_rate(imbalance=1.0),
      None)
check("dearer money raises the carrier's capital cost and so the freight rate",
      cart_rate(annual_rate=4.0 * RATE) > cart_rate()
      and freight_cost.capital_money_per_tonne_km(CART_INPUTS, CART_PRICES, 4.0 * RATE, WORKING_DAYS) > capital, None)


# --- the domestic cargo terms: spoilage by good, loss by leg mode, interest by the haul's days.
def cart_haul(distance_km):
    return Route((Leg("a", "b", "cart", distance_km, 0.0, distance_km / CART_INPUTS.distance_per_day_km),))


check("domestic cargo cost share grows with the distance hauled",
      domestic_cargo_cost_share(0.1, {}, cart_haul(2000.0), RATE)
      > domestic_cargo_cost_share(0.1, {}, cart_haul(500.0), RATE) > 0.0, None)
check("a perishable good costs more over the same haul than a durable one, which pays interest only",
      domestic_cargo_cost_share(5.0, {}, cart_haul(1000.0), RATE) > domestic_cargo_cost_share(0.0, {}, cart_haul(1000.0), RATE)
      and abs(domestic_cargo_cost_share(0.0, {}, cart_haul(1000.0), RATE) - RATE * cart_haul(1000.0).travel_days / 365.0) < 1e-12,
      None)
check("a mode with a daily loss (a herd on the road) adds to the haul's cost share",
      domestic_cargo_cost_share(0.0, {"cart": 0.01}, cart_haul(1000.0), RATE)
      > domestic_cargo_cost_share(0.0, {}, cart_haul(1000.0), RATE), None)
