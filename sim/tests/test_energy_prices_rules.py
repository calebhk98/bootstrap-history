"""EnergyPrices and pool_only on bands and pools written here: what an entry pays for a carrier, what a producer sells it for, and the
carrier-price ratio the market moves energy by. The graded prices of the shipped tree are test_node_energy_validation."""
from sim.prices import energy_prices
from sim.engine import node_revenue_market
from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

POOL = {"thermal_mj": 1.0, "mechanical_mj": 4.0, "electrical_mj": 6.0}
BANDS = {("thermal_mj", 300.0): 1.5, ("thermal_mj", 800.0): 2.5, ("thermal_mj", 1400.0): 7.0}
market = energy_prices.EnergyPrices(POOL, BANDS)

for carrier, price in POOL.items():
    check("an entry with no requirement pays the pool price of %s" % carrier, market.bought(carrier, {}) == price)
check("an entry pays the band of its own stated temperature",
      [market.bought("thermal_mj", {"temperature_needed_c": needed}) for needed in (300.0, 800.0, 1400.0)] == [1.5, 2.5, 7.0])
check("an entry whose stated temperature has no band pays the pool price", market.bought("thermal_mj", {"temperature_needed_c": 555.0}) == 1.0)
check("a carrier with no graded requirement pays the pool price whatever the entry states",
      market.bought("mechanical_mj", {"temperature_needed_c": 800.0}) == 4.0)
check("a producer sells at the highest band its stated reach clears", market.sold("thermal_mj", {"temperature_reached_c": 1100.0}) == 2.5)
check("a producer whose reach clears no band sells at the pool price", market.sold("thermal_mj", {"temperature_reached_c": 100.0}) == 1.0)
check("a producer of a carrier without grades sells at the pool price", market.sold("mechanical_mj", {}) == 4.0)

cheap = energy_prices.EnergyPrices({"mechanical_mj": 4.0}, {}, lambda entry: {"mechanical_mj": 0.5})
dear = energy_prices.EnergyPrices({"mechanical_mj": 4.0}, {}, lambda entry: {"mechanical_mj": 9.0})
check("a producer sells no dearer than its own technique costs", cheap.sold("mechanical_mj", {}) == 0.5 and dear.sold("mechanical_mj", {}) == 4.0)

unreachable = energy_prices.EnergyPrices(POOL, BANDS, unreachable=[("thermal_mj", 1700.0)])
check("an entry stating a grade no held technique supplies cannot run",
      unreachable.can_run({"thermal_mj": 5.0, "temperature_needed_c": 1700.0}) is False)
check("an entry stating a grade that is supplied, or none, can run",
      unreachable.can_run({"thermal_mj": 5.0, "temperature_needed_c": 800.0}) and unreachable.can_run({}))
check("pool_only gives every consumer the pool price whatever it states",
      energy_prices.pool_only({"thermal_mj": 3.0, "wheat_kg": 1.0}).bought("thermal_mj", {"temperature_needed_c": 1500.0}) == 3.0)
check("pool_only keeps the carriers and leaves out other goods", energy_prices.pool_only({"thermal_mj": 3.0, "wheat_kg": 1.0}).pool == {"thermal_mj": 3.0})

# --- the market moves energy by the carrier's price ratio.
node = {"_output_per_year": {"a": 10.0}, "_purchases_per_year": {},
        "_energy_bought_per_year": {"thermal_mj": {"quantity": 5.0, "value": 10.0}},
        "_energy_sold_per_year": {"electrical_mj": {"quantity": 2.0, "value": 20.0}}}
factor = node_revenue_market.market_factor(node, {"a": 4.0}, {"a": 4.0, "thermal_mj": 9.0, "electrical_mj": 4.0}.get)
check("a node's market factor scales the energy it buys and sells by each carrier's price over its long-run price", abs(factor - (40.0 + 40.0 - 30.0) / 50.0) < 1e-12, factor)
