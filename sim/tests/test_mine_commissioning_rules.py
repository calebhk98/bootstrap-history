"""Complaints 63 to 66 and 56: a sunk shaft commissions in the year it names and not before (`rules.commission_due`), and a
mine's capex is the miner's wage over the works' build hours (`MineCosts.capex_opex`, on the module with plain views for
what it reads; the deposit physics is test_mine_build_cost, the sizing test_mine_auto_and_capacity)."""
QUICK_TOPIC = True
UNDER_TEST = {"commission_due", "capex_opex"}

import unittest

from sim.resources import rules
from sim.tests import resources_stand_in


class Commissioning(unittest.TestCase):
    TRANCHE = ["coal", 10.0, 105, 50.0]

    def test_the_year_before_the_named_year_commissions_nothing(self):
        commissioned, still, pending = rules.commission_due([self.TRANCHE], {"coal": 10.0}, 104)
        self.assertEqual((commissioned, still, pending), ([], [self.TRANCHE], {"coal": 10.0}))

    def test_the_named_year_commissions_the_working_dated_that_year(self):
        commissioned, still, pending = rules.commission_due([self.TRANCHE], {"coal": 10.0}, 105)
        (working,) = commissioned
        self.assertEqual((working["material"], working["capacity"], working["opened_year"], working["capex_paid"]),
                         ("coal", 10.0, 105, 50.0))
        self.assertEqual((pending, still), ({}, []))

    def test_a_late_resolution_still_dates_the_working_by_its_own_ready_year(self):
        commissioned, _still, _pending = rules.commission_due([self.TRANCHE], {"coal": 10.0}, 110)
        self.assertEqual(commissioned[0]["opened_year"], 105)

    def test_two_tranches_of_one_material_stay_two_workings_and_only_the_ready_one_leaves_pending(self):
        commissioned, still, pending = rules.commission_due([self.TRANCHE, ["coal", 4.0, 108, 0.0]], {"coal": 14.0}, 105)
        self.assertEqual((len(commissioned), len(still), pending), (1, 1, {"coal": 4.0}))

    def test_a_tranche_from_a_save_without_its_cost_or_deposit_gets_the_unknown_values(self):
        (working,), _still, _pending = rules.commission_due([["coal", 1.0, 100]], {"coal": 1.0}, 100)
        self.assertEqual((working["capex_paid"], working["order"], working["deposit"]), (0.0, "", None))


class Capex(unittest.TestCase):
    def module(self, price):
        module = resources_stand_in.build(views={"wage": lambda trade: 2.0 if trade == "miner" else 0.0,
                                                 "material_price": lambda material: price,
                                                 "normalized_material": lambda material: material})
        module.mine_trade = lambda: "miner"
        module.labour_hours_per_tonne = lambda material: (30.0, 5.0)
        return module

    def test_capex_and_opex_are_the_works_hours_at_the_miners_wage(self):
        self.assertEqual(self.module(1.0).capex_opex("coal"), (60.0, 10.0))

    def test_a_name_nothing_prices_has_no_capex_and_is_not_mineable(self):
        module = self.module(None)
        self.assertEqual(module.capex_opex("typo"), (None, None))
        self.assertFalse(module.mineable("typo"))

    def test_a_curated_mine_material_needs_no_price(self):
        module = self.module(None)
        module.works_materials = lambda: ("iron",)
        self.assertEqual(module.capex_opex("iron"), (60.0, 10.0))

    def test_a_free_mine_has_zero_capex_not_none(self):
        module = self.module(1.0)
        module.labour_hours_per_tonne = lambda material: (0.0, 5.0)
        self.assertEqual(module.mine_capex("coal"), 0.0)


if __name__ == "__main__":
    unittest.main()
