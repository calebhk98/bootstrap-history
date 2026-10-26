"""What `state` says of scandal and succession, what a patron's death does to the scandal marks, and how a tech's
effect on the society is logged. Each rule is called on a stand-in carrying only what it reads."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.diffusion.api import ApplyTechEffects
from sim.diffusion.module import Diffusion
from sim.engine import bridge_diffusion
from sim.engine.society_hazards import HazardsMixin
from sim.polity.api import ShiftValueWeight
from sim.refusal import cause_of
from sim.reporting.api import RecordEvent
from sim.tests import module_harness
from sim.ui.proto.scandal_trend import years_until_scandal_crosses_the_line
from sim.ui.proto.state_succession import succession_block
from sim.tests import event_stand_in


class ScandalTrend(unittest.TestCase):

    def test_a_scandal_rising_toward_the_line_names_the_years_left_at_that_pace(self):
        self.assertEqual(years_until_scandal_crosses_the_line(40.0, 30.0, 70.0), 4)

    def test_a_scandal_not_rising_by_more_than_a_trace_has_no_crossing(self):
        self.assertIsNone(years_until_scandal_crosses_the_line(40.0, 39.97, 70.0))
        self.assertIsNone(years_until_scandal_crosses_the_line(40.0, 45.0, 70.0))

    def test_a_scandal_already_over_the_line_or_with_no_earlier_reading_has_none(self):
        self.assertIsNone(years_until_scandal_crosses_the_line(80.0, 60.0, 70.0))
        self.assertIsNone(years_until_scandal_crosses_the_line(40.0, None, 70.0))


class Rolls:
    """The first draw is low (the patron dies); every later draw is high."""

    def __init__(self):
        self.calls = 0

    def random(self):
        self.calls += 1
        return 0.0 if self.calls == 1 else 0.99


class PatronDeath(HazardsMixin):
    send = event_stand_in.send

    def __init__(self, scandal_last_year):
        self.rng = Rolls()
        self.civ = {}
        self.manual = False
        self.price_index = 1.0
        self.labour = types.SimpleNamespace(money_per_labour_hour=lambda: 1.0)
        self.policy = {"auto_court_heir": False}
        self.state = types.SimpleNamespace(
            founder=types.SimpleNamespace(last_patron_death=None),
            household=types.SimpleNamespace(scandal=10.0, scandal_last_year=scandal_last_year, protection=0.9, log=[]),
            scenario=types.SimpleNamespace(year=100))

    def running_with_mechanic(self, name):
        return True


class PatronDies(unittest.TestCase):

    def test_the_scandal_jumps_and_last_years_mark_moves_with_it_so_the_jump_is_no_trend(self):
        game = PatronDeath(scandal_last_year=10.0)
        game._random_events_for_seat(100)
        household = game.state.household
        self.assertEqual(household.scandal, 10.0 + game.PATRON_DEATH_SCANDAL)
        self.assertEqual(household.scandal - household.scandal_last_year, 0.0)

    def test_with_no_mark_to_move_the_scandal_still_jumps(self):
        game = PatronDeath(scandal_last_year=None)
        game._random_events_for_seat(100)
        self.assertEqual(game.state.household.scandal, 10.0 + game.PATRON_DEATH_SCANDAL)
        self.assertIsNone(game.state.household.scandal_last_year)

    def test_protection_falls_by_the_retention_share_and_the_death_is_logged_with_its_kind(self):
        game = PatronDeath(scandal_last_year=10.0)
        game._random_events_for_seat(100)
        self.assertAlmostEqual(game.state.household.protection, 0.9 * game.PATRON_DEATH_PROTECTION_RETENTION)
        self.assertEqual(cause_of(game.state.household.log[0][1]), "patron_dies")


class Succession(unittest.TestCase):

    def game(self, carry, deputies):
        return types.SimpleNamespace(
            state=types.SimpleNamespace(household=types.SimpleNamespace(directors_extra=deputies)),
            DEPUTIES_CARRY_THE_WORK_FROM=1.0, deputies_carry_the_work=lambda: carry, deputy_hours=lambda: 400.0,
            STAFF_CAPACITY_SOURCES=[], nodes={}, has=lambda node_id: False)

    def test_deputies_short_of_the_threshold_are_reported_as_not_carrying_the_work(self):
        block = succession_block(self.game(False, 0.2))
        self.assertEqual((block["deputies"], block["deputies_carry_the_work"], block["deputy_hours_a_year"]), (0.2, False, 400.0))
        self.assertEqual(block["deputies_needed_to_carry_the_work"], 1.0)

    def test_deputies_at_the_threshold_are_reported_as_carrying_it(self):
        self.assertTrue(succession_block(self.game(True, 5.0))["deputies_carry_the_work"])


class Reading:
    """A country's reading shares that records what it is taught."""

    def __init__(self):
        self.values = {"literacy_general": 0.1, "literacy_elite": 0.5}
        self.taught = []

    def get(self, field):
        return self.values[field]

    def teach(self, field, target, ceiling):
        self.taught.append((field, target, ceiling))
        self.values[field] = target


class Society:
    """The diffusion module over a tree of one node, a society with one value weight and a country that reads."""

    def __init__(self, effects):
        self.value_weights = {"w_novelty": 0.0}
        self.reading = Reading()
        ceilings = {"literacy_general": 0.9, "literacy_elite": 0.97, "common": 0.9}

        class Taught(Diffusion):
            def literacy_ceiling(self, field):
                return ceilings[field]
        weights_world = types.SimpleNamespace(value_weights=self.value_weights)
        self.module = module_harness.build(Taught, views={
            "tech_effects": {"press": effects}.get, "legacy_country_literacy": lambda country: self.reading,
            "tree": {"press": {"name": "Press"}}.get, "coverage": lambda: set()},
            answers={ShiftValueWeight: lambda command: bridge_diffusion.shift_value_weight(weights_world, command)})

    def events(self):
        return [command for command in module_harness.sent(self.module) if isinstance(command, RecordEvent)]


class TechEffects(unittest.TestCase):

    def apply(self, effects):
        game = Society(effects)
        game.module.apply_tech_effects(ApplyTechEffects("press"))
        return game

    def test_a_literacy_effect_logs_the_old_and_new_value_as_a_field(self):
        game = self.apply({"literacy_general": 0.2})
        (event,) = game.events()
        self.assertEqual(event.kind, "society_changed")
        before, after = event.facts["changes"]["literacy_general"]
        self.assertEqual(before, 0.1)
        self.assertEqual(after, game.reading.values["literacy_general"])
        self.assertGreater(after, before)

    def test_a_value_effect_shifts_the_weight_and_logs_before_and_after(self):
        game = self.apply({"w_novelty": 0.3})
        (event,) = game.events()
        before, after = event.facts["changes"]["w_novelty"]
        self.assertEqual(before, 0.0)
        self.assertEqual(after, game.value_weights["w_novelty"])
        self.assertNotEqual(after, before)

    def test_a_tech_with_no_effect_logs_nothing(self):
        game = Society(None)
        game.module.apply_tech_effects(ApplyTechEffects("press"))
        self.assertEqual(game.events(), [])


if __name__ == "__main__":
    unittest.main()
