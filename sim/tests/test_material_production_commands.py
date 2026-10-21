"""`build nitre` and the shortage remedies that point at commands like it (Complaint 640: rules on a stub founder,
no game; the whole-game wiring is test_material_production_commands_scenario)."""
import types
import unittest

from sim.engine import purchase_rule  # noqa: F401  (first: the engine modules import each other in a fixed order)
from sim.engine.economy_freight import FreightMixin

QUICK_TOPIC = True


class _Founder(FreightMixin):
    """The part of a Sim that laying beds and naming a remedy read: a purse, a price level, holdings and demands."""
    NITRE_COST_PER_M2 = 0.5
    CHARCOAL_PER_HA = 1.0
    FOREST_COST_PER_HA = 3.0
    MINE_OPEX_MATERIALS = ("iron",)
    price_index = 2.0
    civ = None

    def __init__(self, cash, demand=None, market_tonnes=0.0):
        self.cash = cash
        self.paid = []
        self.state = types.SimpleNamespace(holdings=types.SimpleNamespace(
            nitre_bed_m2=0.0, forest_ha=0.0, mine_tranches=[]))
        self.mine_capacity = {}
        self.labour = types.SimpleNamespace(money_per_labour_hour=lambda: 1.0)
        self._demand = demand or {}
        self._market_tonnes = market_tonnes

    def spending_power(self, kind):
        return self.cash

    def pay_edge(self, edge, cost, purpose):
        self.cash -= cost
        self.paid.append((edge, cost, purpose))

    def annual_material_demand(self):
        return self._demand

    def _material_market_tonnes(self, material):
        return self._market_tonnes

    def _material_stock(self):
        return {}

    def material_shortfall_t(self, material, by_tag=None):
        return 5.0

    def material_unsupplied_sentence(self, material):
        return ""


class LayingNitreBeds(unittest.TestCase):

    def test_beds_cost_the_area_times_the_unit_cost_at_the_price_level(self):
        founder = _Founder(cash=1000.0)
        self.assertEqual(founder.build_nitre(100), 100.0)
        self.assertAlmostEqual(founder.paid[0][1], 100 * 0.5 * 2.0)
        self.assertAlmostEqual(founder.cash, 1000.0 - 100.0)

    def test_the_beds_are_added_to_the_holdings(self):
        founder = _Founder(cash=1000.0)
        founder.build_nitre(40)
        founder.build_nitre(60)
        self.assertEqual(founder.state.holdings.nitre_bed_m2, 100.0)

    def test_a_bed_that_cannot_be_paid_for_changes_nothing(self):
        founder = _Founder(cash=10.0)
        self.assertEqual(founder.build_nitre(20000), 0.0)
        self.assertEqual((founder.state.holdings.nitre_bed_m2, founder.cash, founder.paid), (0.0, 10.0, []))

    def test_a_negative_or_zero_order_lays_nothing_and_credits_nothing(self):
        founder = _Founder(cash=10.0)
        for order in (-1, 0):
            self.assertEqual(founder.build_nitre(order), 0.0)
        self.assertEqual((founder.state.holdings.nitre_bed_m2, founder.cash), (0.0, 10.0))


class ShortageRemedies(unittest.TestCase):

    def test_charcoal_names_the_forest_commands(self):
        founder = _Founder(cash=0.0, demand={"charcoal_kg": 50000.0})
        commands = founder.shortage_remedy_plan("charcoal")["commands"]
        self.assertTrue(commands[0].startswith("quote forest ") and commands[1].startswith("buy forest "))

    def test_saltpetre_names_a_nitre_order_sized_to_the_deficit(self):
        small = _Founder(cash=0.0, demand={"saltpetre_kg": 20000.0}).shortage_remedy_plan("saltpetre", 20.0)["commands"]
        large = _Founder(cash=0.0, demand={"saltpetre_kg": 20000.0}).shortage_remedy_plan("saltpetre", 40.0)["commands"]
        self.assertTrue(small[0].startswith("buy nitre ") and len(small) == 1)
        self.assertGreater(int(large[0].split()[-1]), int(small[0].split()[-1]))

    def test_a_mined_material_names_the_quote_and_the_buy_of_a_mine(self):
        commands = _Founder(cash=0.0).shortage_remedy_plan("iron", 30.0)["commands"]
        self.assertEqual([command.split()[0] for command in commands], ["quote", "buy"])
        self.assertTrue(all(" mine iron " in command for command in commands))

    def test_no_binding_good_needs_no_remedy(self):
        self.assertEqual(_Founder(cash=0.0).shortage_remedy_plan(None), {"text": "", "commands": []})


if __name__ == "__main__":
    unittest.main()
