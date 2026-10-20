"""The cached sum of working people by trade is dropped by every writer of the workforce: after each writer
mutates it, `people_by_trade` equals a fresh sum."""
QUICK_TOPIC = True

import math
import types
import unittest

from sim.economy import api, labour_state, workforce_settle, workforce_version
from sim.economy.setup import labour_area
from sim.labour.market.records import MarketState

HOURS_PER_YEAR = 100.0


def _economy():
    state = MarketState()
    state.workers = {labour_area("a"): {"smith": [10.0, 10.0], "labourer": [100.0, 100.0]},
                     labour_area("b"): {"smith": [4.0, 4.0], "labourer": [50.0, 50.0]}}
    state.trainees = {labour_area("a"): {"smith": [[2.0, [3.0, 3.0]]]}}
    setup = types.SimpleNamespace(tiles=["a", "b"], civ_id="home", countries=lambda: ["home", "other"],
                                  tiles_of=lambda country: ["a"] if country == "home" else ["b"])
    return types.SimpleNamespace(record=types.SimpleNamespace(workforce=state), setup=setup)


def _fresh(economy, area="a"):
    """The sum done from scratch for one tile's people (the home country's, which is the default scope)."""
    totals = {}
    for trade, bands in economy.record.workforce.workers[labour_area(area)].items():
        totals[trade] = math.fsum(bands)
    return dict(sorted(totals.items()))


class PeopleByTradeCacheTests(unittest.TestCase):
    def _check_after(self, write):
        economy = _economy()
        before = api.people_by_trade(economy)
        api.people_by_trade(economy, "other")
        write(economy.record.workforce)
        after = api.people_by_trade(economy)
        self.assertEqual(after, _fresh(economy))
        self.assertNotEqual(after, before)
        self.assertEqual(api.people_by_trade(economy, "other"), _fresh(economy, "b"))

    def test_the_cache_serves_an_unchanged_workforce(self):
        economy = _economy()
        first = api.people_by_trade(economy)
        self.assertEqual(first, _fresh(economy))
        first["smith"] = -1.0   # a caller's edit does not reach the cache
        self.assertEqual(api.people_by_trade(economy), _fresh(economy))

    def test_scale_people_drops_it(self):
        self._check_after(lambda state: labour_state.scale_people(state, labour_area("a"), 1.5))

    def test_hold_back_drops_it(self):
        self._check_after(lambda state: labour_state.hold_back(state, {labour_area("a"): 0.25}))

    def test_give_back_drops_it(self):
        economy = _economy()
        _seen, held = labour_state.hold_back(economy.record.workforce, {labour_area("a"): 0.25})
        away = api.people_by_trade(economy)   # primed while the held people are away
        labour_state.give_back(economy.record.workforce, held)
        self.assertEqual(api.people_by_trade(economy), _fresh(economy))
        self.assertNotEqual(api.people_by_trade(economy), away)

    def test_trim_people_drops_it(self):
        wanted = {(labour_area("a"), "smith"): 5 * HOURS_PER_YEAR}
        self._check_after(lambda state: workforce_settle.trim_people(state, wanted, "labourer", HOURS_PER_YEAR))

    def test_send_idle_to_plots_drops_it(self):
        wanted = {(labour_area("a"), "labourer"): 10 * HOURS_PER_YEAR}
        self._check_after(lambda state: workforce_settle.send_idle_to_plots(
            state, wanted, "labourer", "smith", HOURS_PER_YEAR))

    def test_a_bump_drops_it(self):
        def write(state):
            state.workers[labour_area("a")]["smith"][0] += 7.0
            workforce_version.bump(state)
        self._check_after(write)

    def test_a_replaced_workforce_is_summed_afresh(self):
        economy = _economy()
        api.people_by_trade(economy)
        replaced = MarketState()
        replaced.workers = {labour_area("a"): {"smith": [1.0]}}
        economy.record.workforce = replaced
        self.assertEqual(api.people_by_trade(economy), {"smith": 1.0})


if __name__ == "__main__":
    unittest.main()
