"""A provider's deaths reach the population step: the year's epidemic deaths handed to the step add what the externality providers
say, band by band. `DiseaseForwardsMixin.epidemic_year` hands the epidemics' deaths to the demography view `externality_deaths`;
that view answers through the module's own point. The arithmetic is test_externalities; the yield factor reaching land-bound
producers is test_externality_pooled_harvest. Stand-ins carry only what each function reads."""
QUICK_TOPIC = True

import unittest

from sim.demography.module import Demography
from sim.demography import rules
from sim.disease.api import HitSeatsWithEpidemic, RunEpidemicYear
from sim.engine.forward_disease import DiseaseForwardsMixin
from sim.tests import module_harness


class Epidemics(DiseaseForwardsMixin):
    """A game whose own epidemics killed a fixed number, and which records the deaths its seats were cut by."""

    def __init__(self, deaths, answers=()):
        self.deaths = deaths
        self.answers = list(answers)
        self.cut_seats_by = None

    def send(self, command):
        if isinstance(command, RunEpidemicYear):
            return dict(self.deaths)
        assert isinstance(command, HitSeatsWithEpidemic)
        self.cut_seats_by = dict(command.deaths_by_band)

    def view(self, name):
        return {"disease_burden": lambda: 1.0, "endemic_death_rates": lambda: {"children": 0.0},
                "externality_deaths": lambda deaths, year: rules.deaths_with_externalities(deaths, self.answers)}[name]


class ExternalityDeathsTests(unittest.TestCase):
    def test_with_no_provider_the_year_hands_over_the_epidemics_own_deaths(self):
        deaths, burden, rates = Epidemics({"working_age": 40.0}).epidemic_year(1e12, 1300)
        self.assertEqual(deaths, {"working_age": 40.0})
        self.assertEqual((burden, rates), (1.0, {"children": 0.0}))

    def test_provided_deaths_are_deaths_in_the_step_beside_the_epidemics(self):
        game = Epidemics({"working_age": 40.0}, [{"deaths_by_band": {"working_age": 1000.0, "children": 5.0}}])
        deaths, _burden, _rates = game.epidemic_year(1e12, 1300)
        self.assertEqual(deaths["working_age"], 1040.0)
        self.assertEqual(deaths["children"], 5.0)

    def test_the_seats_are_cut_by_the_provided_deaths_too(self):
        game = Epidemics({"working_age": 40.0}, [{"deaths_by_band": {"working_age": 1000.0}}])
        deaths, _burden, _rates = game.epidemic_year(1e12, 1300)
        self.assertEqual(game.cut_seats_by, deaths)

    def test_the_demography_view_asks_the_point_with_the_game_and_the_year(self):
        asked = []
        module = module_harness.build(Demography, views={
            "legacy_game": "the game", "externality": lambda game, year: asked.append((game, year)) or [{"deaths_by_band": {"children": 7.0}}]})
        self.assertEqual(module.externality_deaths({"children": 1.0}, 1300), {"children": 8.0})
        self.assertEqual(asked, [("the game", 1300)])


if __name__ == "__main__":
    unittest.main()
