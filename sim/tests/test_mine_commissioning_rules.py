"""Complaints 63 to 66 and 56: a sunk shaft commissions in the year it names and not before, a mine's capex is the
miner's wage over the works' build hours, and a quote charges its price level. Each test calls one method on a stand-in
carrying only what it reads (the deposit physics is test_mine_build_cost, the sizing test_mine_auto_and_capacity)."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine import purchase_rule  # noqa: F401  (first: the engine modules import each other in a fixed order)
from sim.engine.economy_mining import MiningMixin


class _Holder(MiningMixin):
    MINE_OPEX_MATERIALS = ("iron",)
    MINE_TRADE = "miner"

    def __init__(self, year, tranches, pending):
        self.state = types.SimpleNamespace(
            holdings=types.SimpleNamespace(mines=[], mine_tranches=list(tranches), mine_pending=dict(pending)),
            scenario=types.SimpleNamespace(year=year))
        self.household = self.state.holdings

    def _advance_mine_depletion(self):
        pass


class Commissioning(unittest.TestCase):
    TRANCHE = ["coal", 10.0, 105, 50.0]

    def test_the_year_before_the_named_year_commissions_nothing(self):
        holder = _Holder(104, [self.TRANCHE], {"coal": 10.0})
        holder.commission_mines()
        self.assertEqual(holder.state.holdings.mines, [])
        self.assertEqual(holder.state.holdings.mine_pending, {"coal": 10.0})

    def test_the_named_year_commissions_the_working_dated_that_year(self):
        holder = _Holder(105, [self.TRANCHE], {"coal": 10.0})
        holder.commission_mines()
        (working,) = holder.state.holdings.mines
        self.assertEqual((working["material"], working["capacity"], working["opened_year"], working["capex_paid"]),
                         ("coal", 10.0, 105, 50.0))
        self.assertEqual(holder.state.holdings.mine_pending, {})
        self.assertEqual(holder.state.holdings.mine_tranches, [])

    def test_a_late_resolution_still_dates_the_working_by_its_own_ready_year(self):
        holder = _Holder(110, [self.TRANCHE], {"coal": 10.0})
        holder.commission_mines()
        self.assertEqual(holder.state.holdings.mines[0]["opened_year"], 105)

    def test_two_tranches_of_one_material_stay_two_workings_and_only_the_ready_one_leaves_pending(self):
        holder = _Holder(105, [self.TRANCHE, ["coal", 4.0, 108, 0.0]], {"coal": 14.0})
        holder.commission_mines()
        self.assertEqual(len(holder.state.holdings.mines), 1)
        self.assertEqual(holder.state.holdings.mine_pending, {"coal": 4.0})


class Capex(unittest.TestCase):
    def holder(self, price):
        holder = _Holder(1, [], {})
        holder.labour = types.SimpleNamespace(wage_per_hour=lambda trade: 2.0 if trade == "miner" else 0.0)
        holder._mine_labour_hours_per_tonne = lambda material: (30.0, 5.0)
        holder._material_price_per_kg = lambda material: price
        return holder

    def test_capex_and_opex_are_the_works_hours_at_the_miners_wage(self):
        self.assertEqual(self.holder(1.0)._mine_capex_opex("coal"), (60.0, 10.0))

    def test_a_name_nothing_prices_has_no_capex_and_is_not_mineable(self):
        holder = self.holder(None)
        holder._normalize_material_name = lambda name: name
        self.assertEqual(holder._mine_capex_opex("typo"), (None, None))
        self.assertFalse(holder.mineable("typo"))

    def test_a_curated_mine_material_needs_no_price(self):
        self.assertEqual(self.holder(None)._mine_capex_opex("iron"), (60.0, 10.0))

    def test_a_free_mine_has_zero_capex_not_none(self):
        holder = self.holder(1.0)
        holder._mine_labour_hours_per_tonne = lambda material: (0.0, 5.0)
        self.assertEqual(holder._mine_capex("coal"), 0.0)


if __name__ == "__main__":
    unittest.main()
