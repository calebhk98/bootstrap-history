"""The demography module's commands and views, each called on the module over plain values (sim/tests/module_harness.py): who dies and
what the event says, the opening, the settlers, the figures other modules read, and the seat's farm holding."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.actors.api import ScaleStrata
from sim.demography import rules
from sim.demography.api import (ChangeFarmland, CutPopulation, DEFAULT_POPULATION_100AD, KillPeople, NotePopulationChange,
                                OpenPopulation, POP_SCALE_FLOOR, SendSettlers, SetClearedFarmland, SetFarmHoursNeeded,
                                TakeFromGranary)
from sim.demography.module import Demography
from sim.demography.state import DemographySeat, DemographyWorld
from sim.hazards.api import RecordWorldEvent
from sim.refusal import Refusal
from sim.tests import module_harness
from sim.world import demography


def built(children=300.0, working_age=600.0, elderly=100.0, views=None, answers=None, seat=None):
    plain = {"civilisation": {"id": "home", "population": 1000.0}}
    plain.update(views or {})
    return module_harness.build(Demography, views=plain, answers=answers,
                                world=DemographyWorld(pop_children=children, pop_working_age=working_age, pop_elderly=elderly),
                                seat=seat if seat is not None else DemographySeat())


class TheOpening(unittest.TestCase):
    def test_the_people_open_at_the_age_structure_their_size_settles_into(self):
        module = built(0.0, 0.0, 0.0)
        module.open_population(OpenPopulation())
        stationary = demography.Population.stationary(1000.0, seed=rules.population_seed("home"))
        self.assertEqual((module.world.pop_children, module.world.pop_working_age, module.world.pop_elderly),
                         (stationary.children, stationary.working_age, stationary.elderly))

    def test_a_civilisation_that_gives_no_size_opens_at_the_reference_population(self):
        module = built(0.0, 0.0, 0.0, views={"civilisation": {"id": "home"}})
        module.open_population(OpenPopulation())
        self.assertAlmostEqual(module.population_total(), DEFAULT_POPULATION_100AD, delta=1.0)


class TheFigures(unittest.TestCase):
    def test_the_bands_total_and_their_adult_equivalents_are_the_cohort_models(self):
        people = built().population()
        self.assertEqual((people.total, people.working_age), (1000.0, 600.0))
        self.assertEqual(people.adult_equivalents, rules.adult_equivalents(demography.Population(300.0, 600.0, 100.0)))

    def test_the_scale_is_the_people_over_the_reference_and_never_below_the_floor(self):
        self.assertEqual(built(0.0, DEFAULT_POPULATION_100AD, 0.0).pop_scale(), 1.0)
        self.assertEqual(built(1.0, 1.0, 1.0).pop_scale(), POP_SCALE_FLOOR)

    def test_a_reading_of_the_bands_changes_nothing(self):
        module = built()
        module.population().working_age = 1.0
        self.assertEqual(module.working_age(), 600.0)


class TheCuts(unittest.TestCase):
    def test_a_shock_takes_its_share_of_the_whole_and_more_of_the_young_and_old(self):
        module = built()
        module.cut_population(CutPopulation(0.28))
        world = module.world
        self.assertAlmostEqual(world.pop_children + world.pop_working_age + world.pop_elderly, 720.0, places=6)
        self.assertGreater(1.0 - world.pop_children / 300.0, 0.28)
        self.assertLess(1.0 - world.pop_working_age / 600.0, 0.28)

    def test_settlers_leave_the_working_age_alone(self):
        module = built()
        module.send_settlers(SendSettlers(20.0))
        self.assertEqual((module.world.pop_children, module.world.pop_working_age, module.world.pop_elderly), (300.0, 580.0, 100.0))

    def test_the_home_people_die_by_their_cohorts_and_the_event_says_how_many(self):
        module = built(answers={RecordWorldEvent: lambda command: command})
        event = module.kill_people(KillPeople("home", 0.1, "a plague", kind="deaths", tiles=("t1",), facts={"wave": 2}))
        self.assertAlmostEqual(event.facts["died"], 100.0, places=6)
        self.assertEqual((event.kind, event.actors, event.tiles, event.cause), ("deaths", ("home",), ("t1",), "a plague"))
        self.assertEqual(event.facts["wave"], 2)
        self.assertEqual([type(command) for command in module_harness.sent(module)], [RecordWorldEvent])

    def test_a_partners_people_die_by_its_strata_and_the_cohorts_are_left_alone(self):
        strata = {"partner": [{"members": 400.0}, {"members": 100.0}]}

        def scale(command):
            for stratum in strata[command.country]:
                stratum["members"] *= 1.0 - command.share
        module = built(views={"country_strata": lambda country: strata[country]},
                       answers={ScaleStrata: scale, RecordWorldEvent: lambda command: command})
        event = module.kill_people(KillPeople("partner", 0.25, "a curse", kind="acme:deaths"))
        self.assertAlmostEqual(event.facts["died"], 125.0, places=9)
        self.assertEqual((module.world.pop_children, module.world.pop_working_age, module.world.pop_elderly), (300.0, 600.0, 100.0))
        self.assertEqual(module_harness.sent(module)[0], ScaleStrata("partner", 0.25))

    def test_a_share_beyond_one_is_refused_and_nobody_dies(self):
        module = built()
        answer = module.kill_people(KillPeople("home", 1.5, "too many"))
        self.assertTrue(isinstance(answer, Refusal) and answer.cause == "bad_share")
        self.assertEqual(module.population_total(), 1000.0)
        self.assertEqual(module_harness.sent(module), [])


class TheRecord(unittest.TestCase):
    def test_the_screens_change_in_the_last_year_is_kept(self):
        module = built()
        module.note_population_change(NotePopulationChange(-0.05))
        self.assertEqual(module.population_change_last_year(), -0.05)


class TheFarmHolding(unittest.TestCase):
    def test_a_new_seat_holds_no_farm_and_an_empty_granary(self):
        self.assertEqual(built().farm_holdings(), {
            "hectares": None, "stock_kg": 0.0, "cleared_hectares": None, "last_shortfall_kg": None, "last_harvest_kg": 0.0,
            "last_marginal_product": None, "hours_needed": None})

    def test_the_land_changes_by_what_is_bought_and_sold_and_the_answer_is_what_is_held(self):
        module = built()
        self.assertEqual(module.change_farmland(ChangeFarmland(5.0)), 5.0)
        self.assertEqual(module.change_farmland(ChangeFarmland(-2.0)), 3.0)
        self.assertEqual(module.farm_holdings()["hectares"], 3.0)

    def test_the_farm_workforce_records_the_cleared_area_and_the_hours_it_needs(self):
        module = built()
        module.set_cleared_farmland(SetClearedFarmland(120.0))
        module.set_farm_hours_needed(SetFarmHoursNeeded(5.0e5))
        self.assertEqual((module.farm_holdings()["cleared_hectares"], module.farm_holdings()["hours_needed"]), (120.0, 5.0e5))

    def test_thieves_take_grain_from_the_granary_never_below_nothing(self):
        module = built(seat=DemographySeat(farm_stock_kg=1000.0))
        module.take_from_granary(TakeFromGranary(400.0))
        self.assertEqual(module.farm_holdings()["stock_kg"], 600.0)
        module.take_from_granary(TakeFromGranary(5000.0))
        self.assertEqual(module.farm_holdings()["stock_kg"], 0.0)


class PopulationScaleFor(unittest.TestCase):
    def test_a_country_of_the_reference_size_scales_one(self):
        self.assertEqual(built().pop_scale_for(DEFAULT_POPULATION_100AD), 1.0)

    def test_a_tiny_country_is_scaled_to_the_floor(self):
        self.assertEqual(built().pop_scale_for(1.0), POP_SCALE_FLOOR)


class TheLastYearsNutrition(unittest.TestCase):
    def test_no_year_stepped_has_no_ratio(self):
        self.assertIsNone(rules.nutrition_ratio_of(None))

    def test_the_ratio_is_the_flows_nutrition_ratio_as_a_float(self):
        self.assertEqual(rules.nutrition_ratio_of(SimpleNamespace(nutrition_ratio=1)), 1.0)
        self.assertEqual(rules.nutrition_ratio_of(SimpleNamespace(nutrition_ratio=0.75)), 0.75)

    def test_the_view_answers_none_before_the_first_step(self):
        self.assertIsNone(built().nutrition_ratio_last_year())


if __name__ == "__main__":
    unittest.main()
