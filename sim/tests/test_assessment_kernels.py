"""The revenue assessment kernels over written-out rows: plain forms, forms on payers, labour, leakage, collection and receipts."""
QUICK_TOPIC = True

import unittest

from sim.agents import assessment_kernels as kernels
from sim.agents.assessment_kernels import FORMS, PAYERS, RevenueForms, RevenuePayers


def forms_table(rows):
    table = FORMS.new_table(RevenueForms, len(rows), len(rows))
    for row, figures in enumerate(rows):
        for column, value in figures.items():
            getattr(table, column)[row] = value
    return table


def payers_table(rows):
    table = PAYERS.new_table(RevenuePayers, len(rows), len(rows))
    for row, figures in enumerate(rows):
        for column, value in figures.items():
            getattr(table, column)[row] = value
    return table


class AssessFormsTests(unittest.TestCase):
    def test_a_plain_form_takes_reach_times_rate_times_base(self):
        forms = forms_table([{"kind": kernels.PLAIN, "base": 1000.0, "rate": 0.1, "collectible": 0.5}])
        kernels.assess_forms(forms, payers_table([]))
        self.assertEqual((forms.money[0], forms.tonnes[0], forms.assessed_base[0]), (0.5 * 0.1 * 1000.0, 0.0, 1000.0))

    def test_a_form_paid_in_kind_takes_the_same_share_of_the_tonnes(self):
        forms = forms_table([{"kind": kernels.PLAIN, "base": 1000.0, "base_tonnes": 40.0, "in_kind": 1, "rate": 0.1, "collectible": 0.5}])
        kernels.assess_forms(forms, payers_table([]))
        self.assertEqual(forms.tonnes[0], 0.5 * 0.1 * 40.0)

    def test_officials_keep_a_share_of_money_and_tonnes(self):
        forms = forms_table([{"kind": kernels.PLAIN, "base": 100.0, "base_tonnes": 10.0, "in_kind": 1, "rate": 0.5, "collectible": 1.0,
                              "kept": 0.2}])
        kernels.assess_forms(forms, payers_table([]))
        self.assertEqual((forms.money[0], forms.tonnes[0], forms.kept_by_officials[0]), (50.0 * 0.8, 5.0 * 0.8, 0.2))

    def test_labour_is_the_share_of_a_working_year_times_the_base(self):
        forms = forms_table([{"kind": kernels.LABOUR, "base": 2000.0, "rate": 0.05}])
        kernels.assess_forms(forms, payers_table([]))
        self.assertEqual((forms.money[0], forms.assessed_base[0]), (100.0, 2000.0))

    def test_a_payer_owes_no_more_than_its_purse_and_income_hidden_is_concealed(self):
        forms = forms_table([{"kind": kernels.HELD_BY_PAYERS, "rate": 0.5, "collectible": 0.5, "visible_share": 0.8,
                              "first_payer": 0, "payer_count": 2}])
        payers = payers_table([{"income": 100.0, "purse": 1000.0}, {"income": 100.0, "purse": 10.0}])
        kernels.assess_forms(forms, payers)
        self.assertEqual(payers.seen.tolist(), [80.0, 80.0])
        self.assertEqual(payers.owed.tolist(), [0.5 * 40.0, 0.5 * 10.0])
        self.assertEqual((forms.assessed_base[0], forms.money[0], forms.concealed[0]), (160.0, 25.0, 40.0))

    def test_leakage_cuts_the_payers_amounts_and_the_form_once(self):
        forms = forms_table([{"kind": kernels.HELD_BY_PAYERS, "rate": 0.5, "collectible": 1.0, "visible_share": 1.0, "kept": 0.5,
                              "first_payer": 0, "payer_count": 1}])
        payers = payers_table([{"income": 100.0, "purse": 1000.0}])
        kernels.assess_forms(forms, payers)
        self.assertEqual((payers.owed[0], forms.money[0]), (25.0, 25.0))


class CollectionTests(unittest.TestCase):
    def test_a_first_visit_pays_the_lesser_of_what_it_owes_and_holds(self):
        payers = payers_table([{"owed": 10.0, "first_visit": 1, "purse_now": 4.0}, {"owed": 10.0, "first_visit": 1, "purse_now": -3.0},
                               {"owed": 10.0, "first_visit": 0, "purse_now": 0.0}])
        kernels.plan_collection(payers)
        self.assertEqual(payers.decided.tolist(), [1, 1, 0])
        self.assertEqual(payers.collected.tolist(), [4.0, 0.0, 0.0])


class ReceiptsTests(unittest.TestCase):
    def test_coin_and_labour_received_by_kind_of_form(self):
        forms = forms_table([{"kind": kernels.PLAIN, "money": 10.0}, {"kind": kernels.PLAIN, "money": 20.0, "in_kind": 1},
                             {"kind": kernels.LABOUR, "money": 30.0, "commute": 0.25, "person_days": 100.0},
                             {"kind": kernels.HELD_BY_PAYERS, "money": 40.0}])
        kernels.receipts(forms, 10.0)
        self.assertEqual(forms.coin_money.tolist(), [10.0, 0.0, 7.5, 0.0])
        self.assertEqual(forms.labour_hours.tolist(), [0.0, 0.0, 750.0, 0.0])

    def test_collectors_are_the_bases_in_wage_years_over_what_one_handles(self):
        forms = forms_table([{"assessed_base": 100.0}, {"assessed_base": 300.0}])
        import numpy
        self.assertEqual(kernels.collectors_needed(forms, 10.0, numpy.array([5.0, 10.0])), 100.0 / 10.0 / 5.0 + 300.0 / 10.0 / 10.0)

    def test_accumulate_by_group_adds_in_row_order_onto_the_start(self):
        import numpy
        totals = numpy.array([1.0, 0.0])
        kernels.accumulate_by_group(totals, numpy.array([0, 1, 0]), numpy.array([2.0, 5.0, 3.0]), 3)
        self.assertEqual(totals.tolist(), [6.0, 5.0])


if __name__ == "__main__":
    unittest.main()
