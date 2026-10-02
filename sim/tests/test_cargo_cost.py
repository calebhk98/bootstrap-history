"""Freight prices the cargo as well as the carrier, for foreign and domestic routes alike
(Complaints/326, 340): interest on the cargo's value over the voyage, spoilage by duration,
expected loss at sea, and domestic freight that includes the carrier's capital and empty return."""
from .harness import *  # noqa: F401,F403

from sim.world import cargo_cost, freight_cost, sea_freight, trader_response, transport

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

# --- one freight function for foreign and domestic routes.
s = sim(civ="rome_100ad", capital=1e9)
cart_one_sided = s._freight_mode_costs(1.0)["cart"]
check("domestic freight per tonne-km is the cart's rate with its capital and the empty return",
      abs(s.land_freight_money_per_tonne_km() - cart_one_sided) < 1e-12, None)
inputs = s._land_freight_physical_inputs()
running = (inputs.feed_kg_per_tonne_km * s._material_price_per_kg(s.FREIGHT_FEED_PRICE_MATERIAL)
           + inputs.driver_hours_per_tonne_km * s.wage_per_hour(s.FREIGHT_DRIVER_WAGE_TRADE))
check("...which is more than twice its feed and driver, since oxen and cart are capital",
      s.land_freight_money_per_tonne_km() > 2.0 * running, (s.land_freight_money_per_tonne_km(), running))
check("domestic freight with balanced flows is cheaper than with a one-sided flow",
      s.land_freight_money_per_tonne_km(0.0) < s.land_freight_money_per_tonne_km(1.0), None)
_rate = s.market_rate
s.market_rate = lambda: 4.0 * _rate()
check("dearer money raises domestic freight",
      s.land_freight_money_per_tonne_km() > cart_one_sided, None)
s.market_rate = _rate

# --- the engine's cargo terms: spoilage by good, loss by sea leg, interest by the cycle.
route = s._foreign_route("han_china_100ad", 1.0)
check("a perishable good costs merchants more than a durable one on the same route",
      s._trader_cost_share(route, "milk_kg") > s._trader_cost_share(route, "iron_bar_kg"), None)
check("a durable good's cost share is unchanged by naming it",
      abs(s._trader_cost_share(route, "iron_bar_kg") - s._trader_cost_share(route)) < 1e-12, None)
check("domestic cargo cost share grows with the distance hauled",
      s.domestic_cargo_cost_share("wheat_kg", 2000.0) > s.domestic_cargo_cost_share("wheat_kg", 500.0) > 0.0,
      None)
