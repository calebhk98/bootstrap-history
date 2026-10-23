"""Moving the household's base (`SettlementMixin.move_base`): which moves are refused and why, and what a move pays and drops.
Called on a stand-in carrying only what the method reads."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour_settlement import SettlementMixin

HOME, TOWN, EMPTY, CUT_OFF = "home_tile", "far_town", "empty_tile", "cut_off_tile"


class _Mover(SettlementMixin):
    def __init__(self, capital=1000.0, quote=(10.0, 80.0, 50.0)):
        self.household = types.SimpleNamespace(capital=capital, total_spend=0.0, relocation_hours_this_year=0.0,
                                               commissioned={"smith": 400.0}, contract_hours={"smith": 400.0},
                                               familiarity=0.5, protection=0.4, base_tile=HOME)
        self.paid, self.pressure_cleared, self.pools_resynced = [], 0, 0
        self.quote = quote
        self._world = types.SimpleNamespace(
            state=types.SimpleNamespace(household=self.household), EDGE_WORKERS="workers",
            money_text=lambda amount, grouped=False: "%.0f" % amount, plain_number=lambda value: "%.0f" % value,
            pay_edge=lambda edge, amount, reason: self.paid.append((edge, amount, reason)))
        self.labour_market = types.SimpleNamespace(clear_pressure=self._clear)

    def _clear(self):
        self.pressure_cleared += 1

    def settlement_tiles(self):
        return {HOME: 900.0, TOWN: 200.0, EMPTY: 0.5, CUT_OFF: 300.0}

    def base_tile(self):
        return self.household.base_tile

    def relocation_quote(self, tile):
        return None if tile == CUT_OFF else self.quote

    def _resync_pools(self):
        self.pools_resynced += 1

    def home_town_population_estimate(self):
        return 200.0


class MoveBaseRefusalsTest(unittest.TestCase):
    def _refused(self, tile, **kwargs):
        mover = _Mover(**kwargs)
        ok, _message = mover.move_base(tile)
        self.assertFalse(ok, tile)
        self.assertEqual(mover.household.base_tile, HOME)
        self.assertEqual(mover.paid, [])
        return mover

    def test_an_unknown_tile_the_current_tile_an_empty_tile_and_an_unreachable_tile_are_refused(self):
        for tile in ("atlantis_01", "", None, HOME, EMPTY, CUT_OFF):
            self._refused(tile)

    def test_a_household_that_cannot_pay_the_wages_does_not_move(self):
        mover = self._refused(TOWN, capital=10.0)
        self.assertEqual(mover.household.commissioned, {"smith": 400.0})


class MoveBaseEffectsTest(unittest.TestCase):
    def test_a_move_pays_the_quoted_money_and_hours_and_drops_local_contracts_and_most_standing(self):
        mover = _Mover(quote=(10.0, 80.0, 50.0))
        ok, _message = mover.move_base(TOWN)
        self.assertTrue(ok)
        household = mover.household
        self.assertEqual(mover.paid, [("workers", 50.0, "relocation")])
        self.assertEqual(household.total_spend, 50.0)
        self.assertEqual(household.relocation_hours_this_year, 80.0)
        self.assertEqual((household.commissioned, household.contract_hours), ({}, {}))
        self.assertEqual(mover.pressure_cleared, 1)
        self.assertAlmostEqual(household.familiarity, 0.5 * SettlementMixin.RELOCATION_STANDING_RETAINED)
        self.assertAlmostEqual(household.protection, 0.4 * SettlementMixin.RELOCATION_STANDING_RETAINED)
        self.assertEqual(household.base_tile, TOWN)
        self.assertEqual(mover.pools_resynced, 1)

    def test_hours_moving_add_to_those_already_spent_this_year(self):
        mover = _Mover()
        mover.household.relocation_hours_this_year = 15.0
        mover.move_base(TOWN)
        self.assertEqual(mover.household.relocation_hours_this_year, 95.0)


if __name__ == "__main__":
    unittest.main()
