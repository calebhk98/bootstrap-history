"""A provider's deaths reach the population step: `DiseaseForwardsMixin.epidemic_year`, the year's epidemic deaths handed to the
step, adds what the registered externality providers say, band by band. The registry's own arithmetic is test_externalities;
the yield factor reaching land-bound producers is test_externality_pooled_harvest. A stand-in carries only what the method
reads."""
QUICK_TOPIC = True

import unittest

from sim.disease.api import HitSeatsWithEpidemic, RunEpidemicYear
from sim.engine import externalities
from sim.engine.forward_disease import DiseaseForwardsMixin


class Epidemics(DiseaseForwardsMixin):
    """A game whose own epidemics killed a fixed number, and which records the deaths its seats were cut by."""

    def __init__(self, deaths):
        self.deaths = deaths
        self.cut_seats_by = None

    def send(self, command):
        if isinstance(command, RunEpidemicYear):
            return dict(self.deaths)
        assert isinstance(command, HitSeatsWithEpidemic)
        self.cut_seats_by = dict(command.deaths_by_band)

    def view(self, name):
        return {"disease_burden": lambda: 1.0, "endemic_death_rates": lambda: {"children": 0.0}}[name]


class ExternalityDeathsTests(unittest.TestCase):
    def setUp(self):
        externalities.PROVIDERS.clear()
        self.addCleanup(externalities.PROVIDERS.clear)

    def test_with_no_provider_the_year_hands_over_the_epidemics_own_deaths(self):
        deaths, burden, rates = Epidemics({"working_age": 40.0}).epidemic_year(1e12, 1300)
        self.assertEqual(deaths, {"working_age": 40.0})
        self.assertEqual((burden, rates), (1.0, {"children": 0.0}))

    def test_provided_deaths_are_deaths_in_the_step_beside_the_epidemics(self):
        externalities.PROVIDERS.append(lambda sim, year: {"deaths_by_band": {"working_age": 1000.0, "children": 5.0}})
        deaths, _burden, _rates = Epidemics({"working_age": 40.0}).epidemic_year(1e12, 1300)
        self.assertEqual(deaths["working_age"], 1040.0)
        self.assertEqual(deaths["children"], 5.0)

    def test_the_seats_are_cut_by_the_provided_deaths_too(self):
        externalities.PROVIDERS.append(lambda sim, year: {"deaths_by_band": {"working_age": 1000.0}})
        game = Epidemics({"working_age": 40.0})
        deaths, _burden, _rates = game.epidemic_year(1e12, 1300)
        self.assertEqual(game.cut_seats_by, deaths)


if __name__ == "__main__":
    unittest.main()
