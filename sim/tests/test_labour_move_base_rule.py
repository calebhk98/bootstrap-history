"""Moving the household's base (`Relocation.move_base`): which moves are refused and why, and what a move pays and drops.
Called on a stand-in carrying only what the method reads."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour_relocation import Relocation
from sim.workforce.api import ONCE_COMMISSION
from sim.ledger.api import NoteSpend, PayEdge
from sim.polity.api import ScaleFamiliarity, ScaleProtection

HOME, TOWN, EMPTY, CUT_OFF = "home_tile", "far_town", "empty_tile", "cut_off_tile"


class _World(types.SimpleNamespace):
    @property
    def finance(self):
        return types.SimpleNamespace(balance=self.workforce.capital)


class _Mover:
    def __init__(self, capital=1000.0, quote=(10.0, 80.0, 50.0)):
        self.household = types.SimpleNamespace(capital=capital, total_spend=0.0, relocation_hours_this_year=0.0,
                                               commissioned={"smith": 400.0}, contract_hours={"smith": 400.0},
                                               hours_wanted_once={ONCE_COMMISSION: {"smith": 400.0}}, base_tile=HOME)
        self.paid, self.pressure_cleared, self.pools_resynced, self.sent = [], 0, 0, []
        self.quote = quote
        self._world = _World(
            workforce=self.household, EDGE_WORKERS="workers",
            money_text=lambda amount, grouped=False: "%.0f" % amount, plain_number=lambda value: "%.0f" % value,
            send=self._send)
        self.relocation = Relocation(self._world, book=None, hours=None, market=None, pools=self, settlement=self)
        self.relocation.relocation_quote = self.relocation_quote

    def move_base(self, tile):
        return self.relocation.move_base(tile)

    def _send(self, command):
        if isinstance(command, PayEdge):
            self.paid.append((command.edge, command.amount, command.purpose))
        else:
            self.sent.append(command)

    def _clear(self):
        self.pressure_cleared += 1

    def settlement_tiles(self):
        return {HOME: 900.0, TOWN: 200.0, EMPTY: 0.5, CUT_OFF: 300.0}

    def base_tile(self):
        return self.household.base_tile

    def relocation_quote(self, tile):
        return None if tile == CUT_OFF else self.quote

    def resync_pools(self):
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
        self.assertEqual(household.relocation_hours_this_year, 80.0)
        self.assertEqual((household.commissioned, household.contract_hours, household.hours_wanted_once), ({}, {}, {}))
        self.assertEqual(mover.sent, [NoteSpend(50.0), ScaleFamiliarity(Relocation.RELOCATION_STANDING_RETAINED),
                                      ScaleProtection(Relocation.RELOCATION_STANDING_RETAINED)])
        self.assertEqual(household.base_tile, TOWN)
        self.assertEqual(mover.pools_resynced, 1)

    def test_hours_moving_add_to_those_already_spent_this_year(self):
        mover = _Mover()
        mover.household.relocation_hours_this_year = 15.0
        mover.move_base(TOWN)
        self.assertEqual(mover.household.relocation_hours_this_year, 95.0)


if __name__ == "__main__":
    unittest.main()
