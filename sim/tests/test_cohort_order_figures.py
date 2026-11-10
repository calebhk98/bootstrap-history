"""The rules the year's goods orders, the household work plans and the household loans run on a cohort's figures read from the columns
(`cohort_order_figures.order_figures`, `CohortStore.milled_of`, `CohortStore.figures`) give what the same rules gave over a `Cohort`."""

QUICK_TOPIC = True

import types
import unittest

import numpy as np

from sim.economy import household_work_year, titles_worked
from sim.economy.cohort_order_figures import order_figures
from sim.economy.cohort_store import CohortStore
from sim.economy.households_cohort import Cohort
from sim.tests.test_economy_household_work_year import View, record, setup
from sim.economy.setup import labour_area


def _cohorts():
    return [Cohort("household:b", "tile:x", 1, 30.0, 12.0, 0.6, expected_inflation=0.02, cash_target=7.0, last_year_income=5.0,
                   expected_spending=3.0, expected_floor_cost=2.0, hired_work_per_person=4.0, milled_grains=("wheat_kg", "barley_kg")),
            Cohort("household:a", "tile:y", 0, 20.0, 8.0, 0.5, expected_inflation=np.float64(0.03), cash_target=np.float64(1.5),
                   share_wealth=np.float64(9.0), last_year_income=3.0)]


def _store():
    return CohortStore({each.agent_id: each for each in _cohorts()})


class OrderFiguresTests(unittest.TestCase):
    def test_every_field_the_orders_read_equals_the_cohorts_and_keeps_its_scalar_type(self):
        store = _store()
        rows = store.rows_of(["household:a", "household:b"])
        for figures, cohort in zip(order_figures(store, rows), (store["household:a"], store["household:b"])):
            for name in figures._fields:
                self.assertEqual(getattr(figures, name), getattr(cohort, name), name)
                self.assertIs(type(getattr(figures, name)), type(getattr(cohort, name)), name)

    def test_a_cohort_with_no_close_has_no_share_wealth(self):
        store = _store()
        found = order_figures(store, store.rows_of(["household:b"]))[0]
        self.assertIsNone(found.share_wealth)

    def test_the_rows_come_in_the_order_asked(self):
        store = _store()
        self.assertEqual([each.agent_id for each in order_figures(store, np.array([1, 0], dtype=np.int64))], ["household:a", "household:b"])


class MilledOfTests(unittest.TestCase):
    def test_the_grains_are_read_back_in_the_order_written(self):
        store = _store()
        self.assertEqual(store.milled_of(store.row_of["household:b"]), ("wheat_kg", "barley_kg"))
        self.assertEqual(store.milled_of(store.row_of["household:a"]), ())

    def test_a_block_write_of_grains_replaces_what_was_read_before(self):
        store = _store()
        row = store.row_of["household:b"]
        store.milled_of(row)
        store.write_milled(np.array([row], dtype=np.int64), [("rye_kg",)])
        self.assertEqual(store.milled_of(row), ("rye_kg",))

    def test_a_single_field_write_of_grains_replaces_what_was_read_before(self):
        store = _store()
        row = store.row_of["household:a"]
        store.milled_of(row)
        store.set_fields("household:a", milled_grains=("rye_kg", "wheat_kg"))
        self.assertEqual(store.milled_of(row), ("rye_kg", "wheat_kg"))

    def test_a_record_put_over_a_row_replaces_its_grains(self):
        store = _store()
        row = store.row_of["household:b"]
        store.milled_of(row)
        store.put(Cohort("household:b", "tile:x", 1, 30.0, 12.0, 0.6, milled_grains=()))
        self.assertEqual(store.milled_of(row), ())


class WorkTermsTests(unittest.TestCase):
    def test_work_terms_at_equals_over_the_figures_what_it_is_over_the_cohort(self):
        area = labour_area("t1")
        landholder = Cohort(agent_id="rich", tile="t1", income_class=0, people=100.0, working_people=50.0, ownership_share=0.0)
        rec = record({"t1": {"rich": 1.0}}, cohorts=[landholder])
        view = View({("smith", area): 3.0, ("servant", area): 1.0}, {"domestic_service_hour": 2.0})
        store = CohortStore({"rich": landholder})
        figures = store.figures(store.order())[0]
        self.assertEqual(household_work_year.work_terms_at(setup(), rec, view, figures, 2.0),
                         household_work_year.work_terms_at(setup(), rec, view, landholder, 2.0))

    def test_basket_signature_equals_over_the_order_figures_what_it_is_over_the_cohort(self):
        store = _store()
        rec = record({"tile:x": {"household:b": 1.0}}, cohorts=[])
        for figures in order_figures(store, store.order()):
            self.assertEqual(household_work_year.basket_signature(rec, figures), household_work_year.basket_signature(rec, store[figures.agent_id]))

    def test_signatures_of_figures_equals_basket_signature_of_each_cohort(self):
        store = _store()
        rec = record({"tile:x": {"household:b": 1.0}}, cohorts=[])
        for buying in (True, False):
            found = household_work_year.signatures_of_figures(rec, order_figures(store, store.order()), buying)
            self.assertEqual(found, [household_work_year.basket_signature(rec, store[each], buying) for each in ("household:a", "household:b")])


class WorkedSharesTests(unittest.TestCase):
    def _record(self):
        tenancies = {"t1": [{"lessor": "a", "tenant": "b", "share": 0.2}, {"lessor": "a", "tenant": "c", "share": 0.1},
                            {"lessor": "c", "tenant": "b", "share": 0.05}]}
        return types.SimpleNamespace(land=types.SimpleNamespace(titles={"t1": {"a": 0.6, "c": 0.3}, "t2": {"d": 1.0}}, tenancies=tenancies))

    def test_worked_shares_equals_worked_share_for_each_pair(self):
        record = self._record()
        pairs = [("t1", "a"), ("t1", "b"), ("t1", "c"), ("t2", "d"), ("t2", "e"), ("t1", "a")]
        found = titles_worked.worked_shares(record, [tile for tile, _holder in pairs], [holder for _tile, holder in pairs])
        self.assertEqual(found, [titles_worked.worked_share(record, tile, holder) for tile, holder in pairs])

    def test_hearths_of_equals_hearth_of_for_each_pair(self):
        record = self._record()
        pairs = [("t1", "a"), ("t1", "b"), ("t1", "z"), ("t2", "d")]
        found = household_work_year.hearths_of(record, [tile for tile, _holder in pairs], [holder for _tile, holder in pairs])
        self.assertEqual(found, [household_work_year.hearth_of(record, tile, holder) for tile, holder in pairs])
        self.assertEqual(found, [True, True, False, True])


if __name__ == "__main__":
    unittest.main()
