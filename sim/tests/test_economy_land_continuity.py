"""The clearing rent of a tile moves smoothly with the land in use, and the fixture's rents never drop to nothing."""
import unittest

from sim.economy import land_market
from sim.economy.land_market import LandDemand, clear_land
from sim.tests import economy_fixture

VALUE, COST, SUPPLY = 100.0, 40.0, 1000.0


def rent_at(hectares_in_use):
    demand = LandDemand("p1", "t", hectares_in_use, VALUE, COST)
    return clear_land({"t": SUPPLY}, [demand]).rent_per_hectare_by_tile["t"]


class ContinuityTests(unittest.TestCase):
    def test_rent_does_not_jump_where_use_spills_into_the_next_band(self):
        edge = SUPPLY * land_market.LAND_BAND_AREA_SHARES[0]
        below, above = rent_at(edge * (1.0 - 1e-6)), rent_at(edge * (1.0 + 1e-6))
        self.assertAlmostEqual(below, above, delta=0.01 * VALUE)

    def test_total_rent_never_falls_as_more_land_is_used(self):
        totals = [rent_at(SUPPLY * step / 100.0) * SUPPLY * step / 100.0 for step in range(1, 101)]
        for before, after in zip(totals, totals[1:]):
            self.assertGreaterEqual(after, before - 1e-9)

    def test_a_tile_worked_in_its_best_land_alone_pays_nothing(self):
        self.assertAlmostEqual(rent_at(SUPPLY * 0.01), 0.0)


class FixtureFlickerTests(unittest.TestCase):
    def test_posted_rent_on_a_land_binding_tile_never_drops_to_nothing(self):
        # with stepped bands the rent flipped between nothing and a share of the output value
        setup = economy_fixture.small_setup(land_per_run={economy_fixture.FARM: 5.0})
        economy = economy_fixture.Economy(setup)
        posted = []
        for _year in range(30):
            economy.step(economy_fixture.quiet_year(setup))
            posted.append(economy.record.land_rent.get(economy_fixture.HILLS, 0.0))
        self.assertTrue(all(rent > 0.0 for rent in posted))


if __name__ == "__main__":
    unittest.main()
