"""A real year (the labour year, the population following, the trim at the end of the spin-up) leaves the cached
people by trade equal to a fresh sum."""
import math
import unittest

from sim.tests import harness


def _fresh(economy):
    setup = economy.setup
    tiles = set(setup.tiles_of(setup.civ_id)) if len(setup.countries()) > 1 else set(setup.tiles)
    totals = {}
    for area, by_trade in economy.record.workforce.workers.items():
        if area.split("@", 1)[1] not in tiles:
            continue
        for trade, bands in by_trade.items():
            totals.setdefault(trade, []).extend(bands)
    return {trade: math.fsum(bands) for trade, bands in sorted(totals.items())}


class PeopleByTradeAcrossAYearTests(unittest.TestCase):
    def test_the_cache_matches_a_fresh_sum_after_each_year(self):
        game = harness.sim()
        agent = game.economy.agent
        for _year in range(2):
            agent.people_by_trade()   # primed before the year writes the workforce
            game.step()
            cached = agent.people_by_trade()
            fresh = _fresh(agent.economy())
            self.assertEqual(sorted(cached), sorted(fresh))
            for trade in fresh:
                self.assertAlmostEqual(cached[trade], fresh[trade], places=6)


if __name__ == "__main__":
    unittest.main()
