"""Labour price pressure and the commodity framework (Complaint 640 audit: rules on a stub market and a ledger built
here, no game; the literate ceiling and the material price factor are test_literacy_and_material_price_rules)."""
import types
import unittest

from sim.labour.labour_market_api import LabourMarket

from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True


class _Market(LabourMarket):
    """The market over a stub world: a pressure record book, a year, and the supply of each trade."""

    def __init__(self, supply, year=1):
        self._records_book = {}
        self._supply = supply
        self._world = types.SimpleNamespace(
            state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=year)))
        self._labour = types.SimpleNamespace(market_supply=lambda trade: self._supply)

    def _records(self):
        return self._records_book

    def standing_draw(self, trade):
        return 0.0


class PricePressure(unittest.TestCase):

    def test_an_unleaned_on_trade_costs_the_wage_table(self):
        self.assertEqual(_Market(supply=100.0).price_factor("millwright"), 1.0)

    def test_leaning_hard_on_a_scarce_trade_raises_what_it_costs(self):
        market = _Market(supply=10.0)
        market.press("millwright", 8.0)
        self.assertGreater(market.price_factor("millwright"), 1.5)

    def test_the_premium_is_the_coefficient_times_the_share_squared(self):
        market = _Market(supply=10.0)
        market.press("millwright", 5.0)
        self.assertAlmostEqual(market.price_factor("millwright"), 1.0 + market.LABOUR_PRICE_PRESSURE_COEFFICIENT * 0.25)

    def test_the_share_is_capped(self):
        market = _Market(supply=1.0)
        market.press("millwright", 1000.0)
        self.assertAlmostEqual(
            market.price_factor("millwright"),
            1.0 + market.LABOUR_PRICE_PRESSURE_COEFFICIENT * market.LABOUR_PRESSURE_SHARE_CAP ** 2)

    def test_recent_pressure_decays_with_the_years(self):
        market = _Market(supply=10.0)
        market.press("millwright", 8.0)
        before = market.price_factor("millwright")
        market._world.state.scenario.year += 5
        after = market.price_factor("millwright")
        self.assertLess(after, before)
        self.assertAlmostEqual(market.recent_pressure("millwright"), 8.0 * market.LABOUR_PRESSURE_DECAY_RATE ** 5)

    def test_the_same_demand_costs_less_where_the_trade_is_bigger(self):
        thin, thick = _Market(supply=10.0), _Market(supply=60.0)
        for market in (thin, thick):
            market.press("millwright", 6.0)
        self.assertLess(thick.price_factor("millwright"), thin.price_factor("millwright"))

    def test_pressure_adds_up_and_never_goes_negative(self):
        market = _Market(supply=10.0)
        market.press("millwright", 2.0)
        market.press("millwright", 3.0)
        market.press("millwright", -9.0)
        self.assertAlmostEqual(market.recent_pressure("millwright"), 5.0)

    def test_clearing_the_pressure_restores_the_wage_table_price(self):
        market = _Market(supply=10.0)
        market.press("millwright", 8.0)
        market.clear_pressure()
        self.assertEqual(market.price_factor("millwright"), 1.0)


# --- COMMODITY FRAMEWORK (data/world/COMMODITIES.md,
# sim/prices/commodities.py). Standalone from Sim, so these checks
# build a CommodityLedger directly off commodities.json and the tech tree's
# NODES rather than going through `sim()`/`proto()`. See the design doc for
# what each claim below is meant to prove and why.

# A fixture price table (labour hours per kg): the ledger's base price is the solved price of
# the material each commodity names, so a test states its own.
FIXTURE_PRICES_HOURS_PER_KG = {"iron_bar_kg": 20.0, "copper_kg": 80.0, "copper_wire_kg": 120.0,
                               "coal_kg": 0.4, "gold_kg": 70000.0, "wool_kg": 40.0,
                               "cloth_kg": 60.0, "cotton_kg": 80.0}
LED = COMMOD.CommodityLedger(nodes=NODES, price_hours_per_kg=FIXTURE_PRICES_HOURS_PER_KG)

check("commodities.json defines the nine commodities the design doc promises",
      set(LED.commodities) == {"iron", "copper", "copper_wire", "coal", "gold",
                                "wool", "cloth", "cotton", "coffee"},
      sorted(LED.commodities))

# --- gold: a water pump and chemical extraction should compound, not just
# pick the better of the two, because they are independent improvements
# stacked on the same mine (COMMODITIES.md section 3, "multiplier" entries).
mult_none = LED.best_multiplier("gold", built=[])
mult_pump = LED.best_multiplier("gold", built=["met_mine_pumping"])
mult_both = LED.best_multiplier("gold", built=["met_mine_pumping", "mt2_cyanidation"])
check("a mine with a water pump and chemical extraction multiplies gold "
      "output by roughly the brief's own '20x' figure",
      19.0 <= mult_both <= 23.0, mult_both)
check("the two gold technologies compound rather than the model just taking "
      "the better of the two",
      mult_both > mult_pump > mult_none == 1.0,
      "none=%.1f pump=%.1f both=%.1f" % (mult_none, mult_pump, mult_both))

# --- cloth: automated looms make cloth more available, which drops its
# price, which makes a hot air balloon (400 kg of linen_kg) cheaper to build.
CLOTH_DEMAND_T = 20000.0
price_hand = LED.price("cloth", CLOTH_DEMAND_T, LED.market_available("cloth", built=[]))
price_power = LED.price("cloth", CLOTH_DEMAND_T, LED.market_available("cloth", built=["tex_power_loom"]))
check("a power loom makes cloth more available (higher national output) "
      "than the baseline loom, at the same demand",
      LED.country_output("cloth", ["tex_power_loom"]) > LED.country_output("cloth", []))
check("...which drops the market price of cloth, not just a premium on top "
      "of a flat floor (the thing economy.py's material_price_factor cannot do)",
      price_power < price_hand * 0.5,
      "hand loom=%.2f power loom=%.2f h/kg" % (price_hand, price_power))
balloon_linen_kg = NODES["hot_air_balloon"]["mat"]["linen_kg"]
cost_hand = balloon_linen_kg * price_hand
cost_power = balloon_linen_kg * price_power
check("...which makes the real hot_air_balloon node's linen bill cheaper "
      "to buy once the power loom exists",
      cost_power < cost_hand, "hand=%.0f power=%.0f labour hours" % (cost_hand, cost_power))

# --- copper wire: the real test. A modest order is fully met; an industrial
# order of 'kilometres of copper wire' is not, and the shortfall is
# attributed to copper (the ore), not to copper_wire (the smiths' craft),
# even though copper_wire also comes up short -- this is the distinction a
# flat resource_throttle() cannot draw at all.
modest = LED.propagate_demand("copper_wire", 5.0, built=[])
check("a modest order of copper wire (5 t/yr) is fully met by the ordinary "
      "market for copper",
      modest["met_fraction"] > 0.999, modest["met_fraction"])

big = LED.propagate_demand("copper_wire", 500.0, built=[])
check("an industrial order for copper wire is NOT fully met: there is not "
      "enough copper being mined to meet the demand",
      big["met_fraction"] < 0.95, big["met_fraction"])
check("the shortfall is attributed to copper specifically, not to copper_wire "
      "-- the smiths' wire-drawing bench is not the bottleneck",
      LED.bottlenecks(big) == ["copper"], LED.bottlenecks(big))
check("copper_wire itself is NOT flagged as its own bottleneck: it only "
      "inherited the shortage from its input",
      big["bottleneck"] is None, big["bottleneck"])
check("copper_wire's own wire-drawing capacity is not, in fact, the "
      "constraint (it is far above what was asked)",
      big["own_capacity_t"] > big["requested_t"], big["own_capacity_t"])

fixed = LED.propagate_demand("copper_wire", 500.0, built=[],
                             own_production={"copper": 100.0})
check("opening your own copper mine (Sim.open_mine's real-world analogue) "
      "relieves the same industrial order",
      fixed["met_fraction"] > 0.999, fixed["met_fraction"])

# --- monopoly: you know where coffee grows and how to process it, so you
# sell it at a margin nobody can undercut, bounded by what a buyer's next
# best alternative would cost them.
sole = LED.monopoly_price("coffee", marginal_cost=2.0, alternative_price=None)
competitive = LED.monopoly_price("coffee", marginal_cost=2.0, alternative_price=2.4)
check("a sole supplier with no rival prices well above what a competitive "
      "market (many sellers, price near marginal cost) would charge",
      sole > competitive * 2, "sole=%.1f competitive=%.1f" % (sole, competitive))
undercut = LED.monopoly_price("coffee", marginal_cost=2.0, alternative_price=9.0)
check("...but never above what a buyer's next-best alternative would cost "
      "them, once one exists",
      undercut == 9.0, undercut)

# --- price never runs away in either direction, however extreme the ratio
# (price_floor_factor / price_ceiling_factor, COMMODITIES.md section 2).
c = LED.commodities["iron"]
base = LED.base_price_hours_per_kg("iron")
lo = LED.price("iron", demand_t=0.0001, supply_t=1e9)
hi = LED.price("iron", demand_t=1e9, supply_t=0.0001)
check("a total glut never prices a commodity below its floor",
      abs(lo - base * c["price_floor_factor"]) < 1e-6, lo)
check("a total shortage never prices a commodity above its ceiling",
      abs(hi - base * c["price_ceiling_factor"]) < 1e-6, hi)

rng = random.Random(3)
noisy = [LED.price_with_noise("iron", 2000.0, 2475.0, rng) for _ in range(200)]
check("fluctuation stays within the same floor/ceiling bounds over many draws",
      all(base * c["price_floor_factor"] - 1e-9 <= price <= base * c["price_ceiling_factor"] + 1e-9
          for price in noisy),
      (min(noisy), max(noisy)))
check("fluctuation actually varies year to year rather than being decorative",
      len(set(round(price, 4) for price in noisy)) > 50, len(set(noisy)))

# --- 'how much you have' is a stock, tracked separately from the flows
# above (COMMODITIES.md section 8): a minimal Ledger proves the distinction
# is representable even though Sim itself has no inventory today.
ledger = COMMOD.Ledger()
ledger.add("copper", 500.0)
taken = ledger.remove("copper", 800.0)
check("a stock ledger cannot be overdrawn: taking more than is on hand "
      "returns only what was actually there",
      taken == 500.0 and ledger.remove("copper", 1.0) == 0.0,
      taken)


if __name__ == "__main__":
    unittest.main()
