"""The yearly arrival draw (Complaint 490), on the stand-in sim (`disease_stand_in.StandInSim`, no game): called with nothing
under way, the draw reaches the Mexica nation within four centuries in every seed once the outsiders bring ships, and never
without a carrier. It calls `DiseaseWorld.introductions` alone, so no epidemic is run."""

QUICK_TOPIC = True

import unittest

from sim.engine import disease_port
from sim.tests.disease_stand_in import SEEDS, StandInSim, mexica_with_source

YEARS = 400


def first_arrival_year(carrier_modes, seed):
    """The first of YEARS years in which the draw names a pathogen for a nation with none circulating, else None."""
    sim = StandInSim(mexica_with_source(carrier_modes), seed)
    world = disease_port.DiseaseWorld(sim)
    return next((year for year in range(sim.year, sim.year + YEARS) if world.introductions({}, year)), None)


class ArrivalDrawTest(unittest.TestCase):
    def test_the_same_source_reaches_the_nation_in_every_seed_once_the_outsiders_bring_ships(self):
        for seed in SEEDS:
            self.assertIsNotNone(first_arrival_year(["sail"], seed), "seed %d" % seed)

    def test_the_same_source_never_reaches_the_nation_without_a_carrier(self):
        for seed in SEEDS:
            self.assertIsNone(first_arrival_year([], seed), "seed %d" % seed)


if __name__ == "__main__":
    unittest.main()
