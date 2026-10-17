"""The coin's backing-good margin (sim/engine/economy_port_coin.py) is read from the opened economy of a setup,
which costs a whole opening; it is kept on disk under the setup's digest, so a game built twice on the same
setup opens the economy once. The kept answer must be the one a fresh opening gives, and a different setup must
not read it."""
import dataclasses
import tempfile
import unittest
from unittest import mock

from sim.economy import api as economy_api
from sim.engine import economy_port_coin
from sim.engine.economy_port_setup import build_setup, opening_values

from .harness import unopened_sim


@dataclasses.dataclass
class _Setup:
    prices: dict
    coin_per_unit: float = 1.0


class BackingMarginCacheTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="backing_margin_")
        patch = mock.patch.object(economy_port_coin, "MARGIN_CACHE_DIRECTORY", self.directory)
        patch.start()
        self.addCleanup(patch.stop)
        self.opened = []

    def _margin(self, setup, found):
        def blank(given):
            self.opened.append(given)
            return given
        with mock.patch.object(economy_api, "blank_economy", blank), \
                mock.patch.object(economy_api, "backing_marginal_cost", lambda economy: found):
            return economy_port_coin._backing_margin(setup)

    def test_the_same_setup_opens_the_economy_once(self):
        setup = _Setup({"silver": 2.0})
        self.assertEqual(self._margin(setup, (1.5, 2.0)), (1.5, 2.0))
        self.assertEqual(self._margin(_Setup({"silver": 2.0}), (9.0, 9.0)), (1.5, 2.0))
        self.assertEqual(len(self.opened), 1)

    def test_a_different_setup_opens_its_own(self):
        self.assertEqual(self._margin(_Setup({"silver": 2.0}), (1.5, 2.0)), (1.5, 2.0))
        self.assertEqual(self._margin(_Setup({"silver": 3.0}), (2.5, 3.0)), (2.5, 3.0))
        self.assertEqual(len(self.opened), 2)

    def test_money_with_no_good_behind_it_is_kept_too(self):
        self.assertIsNone(self._margin(_Setup({}), None))
        self.assertIsNone(self._margin(_Setup({}), (1.0, 1.0)))
        self.assertEqual(len(self.opened), 1)

    def test_the_kept_margin_is_what_a_fresh_opening_gives(self):
        game = unopened_sim()
        setup = build_setup(game, opening_values(game))
        fresh = economy_api.backing_marginal_cost(economy_api.blank_economy(setup))
        kept = economy_port_coin._backing_margin(setup)
        self.assertEqual(kept, None if fresh is None else tuple(fresh))
        self.assertEqual(economy_port_coin._backing_margin(setup), kept)


if __name__ == "__main__":
    unittest.main()
