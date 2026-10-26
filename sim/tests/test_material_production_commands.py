"""`build nitre` and the shortage remedies that point at commands like it (Complaint 640: rules on a stub founder,
no game)."""
import unittest

from sim.refusal import Refusal
from sim.resources.api import LayNitreBeds
from sim.resources.constants import NITRE_LABOUR_HOURS_PER_M2
from sim.tests import resources_stand_in

QUICK_TOPIC = True


def _founder(cash, demand=None, market_tonnes=0.0):
    """The resources module with a purse of `cash`, a price level of two, a bed priced at half a coin a square metre before
    it, and the materials' figures written out."""
    module = resources_stand_in.build(budget=cash, views={
        "price_index": 2.0, "money_per_labour_hour": 0.5 / NITRE_LABOUR_HOURS_PER_M2, "charcoal_per_hectare": 1.0,
        "material_demand": demand or {}, "material_market_tonnes": lambda material: market_tonnes,
        "material_shortfall": lambda material, by_tag=None: 5.0, "material_unsupplied_sentence": lambda material: ""})
    module.works_materials = lambda: ("iron",)
    return module


def _lay(module, square_metres):
    answer = module.lay_nitre(LayNitreBeds(square_metres))
    return 0.0 if isinstance(answer, Refusal) else answer


class LayingNitreBeds(unittest.TestCase):

    def test_beds_cost_the_area_times_the_unit_cost_at_the_price_level(self):
        founder = _founder(cash=1000.0)
        self.assertEqual(_lay(founder, 100), 100.0)
        self.assertAlmostEqual(resources_stand_in.paid(founder)[0], 100 * 0.5 * 2.0)

    def test_the_beds_are_added_to_the_holdings(self):
        founder = _founder(cash=1000.0)
        _lay(founder, 40)
        _lay(founder, 60)
        self.assertEqual(founder.seat.nitre_bed_m2, 100.0)

    def test_a_bed_that_cannot_be_paid_for_changes_nothing(self):
        founder = _founder(cash=10.0)
        self.assertEqual(_lay(founder, 20000), 0.0)
        self.assertEqual((founder.seat.nitre_bed_m2, resources_stand_in.paid(founder)), (0.0, []))

    def test_a_negative_or_zero_order_lays_nothing_and_credits_nothing(self):
        founder = _founder(cash=10.0)
        for order in (-1, 0):
            self.assertEqual(_lay(founder, order), 0.0)
        self.assertEqual((founder.seat.nitre_bed_m2, resources_stand_in.paid(founder)), (0.0, []))


class ShortageRemedies(unittest.TestCase):

    def test_charcoal_names_the_forest_commands(self):
        founder = _founder(cash=0.0, demand={"charcoal_kg": 50000.0})
        commands = founder.shortage_remedy_plan("charcoal")["commands"]
        self.assertTrue(commands[0].startswith("quote forest ") and commands[1].startswith("buy forest "))

    def test_saltpetre_names_a_nitre_order_sized_to_the_deficit(self):
        small = _founder(cash=0.0, demand={"saltpetre_kg": 20000.0}).shortage_remedy_plan("saltpetre", 20.0)["commands"]
        large = _founder(cash=0.0, demand={"saltpetre_kg": 20000.0}).shortage_remedy_plan("saltpetre", 40.0)["commands"]
        self.assertTrue(small[0].startswith("buy nitre ") and len(small) == 1)
        self.assertGreater(int(large[0].split()[-1]), int(small[0].split()[-1]))

    def test_a_mined_material_names_the_quote_and_the_buy_of_a_mine(self):
        commands = _founder(cash=0.0).shortage_remedy_plan("iron", 30.0)["commands"]
        self.assertEqual([command.split()[0] for command in commands], ["quote", "buy"])
        self.assertTrue(all(" mine iron " in command for command in commands))

    def test_no_binding_good_needs_no_remedy(self):
        self.assertEqual(_founder(cash=0.0).shortage_remedy_plan(None), {"text": "", "commands": []})


class AutomaticPolicyTests(unittest.TestCase):
    def test_an_unset_automatic_policy_is_on_for_an_automatic_game_and_off_for_a_manual_one(self):
        from sim.resources.sizing import automatic_policy_on
        self.assertTrue(automatic_policy_on({}, "auto_mine", manual=False))
        self.assertFalse(automatic_policy_on({}, "auto_mine", manual=True))

    def test_what_the_actor_set_overrides_the_default(self):
        from sim.resources.sizing import automatic_policy_on
        self.assertFalse(automatic_policy_on({"auto_mine": False}, "auto_mine", manual=False))
        self.assertTrue(automatic_policy_on({"auto_mine": True}, "auto_mine", manual=True))


if __name__ == "__main__":
    unittest.main()
