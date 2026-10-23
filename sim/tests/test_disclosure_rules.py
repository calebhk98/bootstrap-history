"""Licensing and disclosure of an invention: which terms are refused, how visible a disclosure mode leaves it, how
the state's military holdings are counted, and what choosing a licence records. Stand-ins carry what each reads."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.agents.licence import terms_problem
from sim.engine import society_disclosure, society_diffusion
from sim.engine.adoption_share import held_share
from sim.engine.society_diffusion import DiffusionMixin
from sim.engine.society_disclosure import DisclosureMixin
from sim.engine.visibility import base_visibility

SECRET_EXPOSURE = 0.2


def licensee(kind="firm", money=1000.0, worth=500.0):
    return types.SimpleNamespace(kind=kind, money=money, imitation_worth=lambda node_id, world: worth)


WORLD = types.SimpleNamespace(entry_gross=lambda node_id, a, b: 100.0)


class Terms(unittest.TestCase):

    def test_acceptable_terms_have_no_problem(self):
        self.assertEqual(terms_problem(licensee(), 100.0, 0.0, "x", WORLD), "")

    def test_a_negative_fee_or_a_royalty_of_one_is_invalid(self):
        self.assertEqual(terms_problem(licensee(), -1.0, 0.0).cause, "terms_invalid")
        self.assertEqual(terms_problem(licensee(), 1.0, 1.0).cause, "terms_invalid")

    def test_only_a_firm_has_takings_to_pay_a_royalty_from(self):
        self.assertEqual(terms_problem(licensee(kind="government"), 1.0, 0.1).cause, "royalty_needs_takings")

    def test_a_licensee_that_cannot_pay_the_fee_is_refused(self):
        self.assertEqual(terms_problem(licensee(money=5.0), 10.0, 0.0).cause, "licensee_cannot_pay")

    def test_a_fee_above_the_licensees_valuation_is_refused_whatever_its_treasury_holds(self):
        problem = terms_problem(licensee(money=1.0e9, worth=500.0), 1000.0, 0.0, "x", WORLD)
        self.assertEqual(problem.cause, "fee_above_value")

    def test_a_royalty_stream_above_the_valuation_is_refused_too(self):
        self.assertEqual(terms_problem(licensee(worth=10.0), 0.0, 0.9, "x", WORLD).cause, "fee_above_value")


class Visibility(unittest.TestCase):

    def test_a_published_invention_shows_in_full(self):
        self.assertEqual(base_visibility("publish", False, 5.0, SECRET_EXPOSURE), 1.0)

    def test_a_default_invention_in_public_use_shows_the_reciprocal_of_its_difficulty(self):
        self.assertEqual(base_visibility("default", True, 4.0, SECRET_EXPOSURE), 0.25)

    def test_a_secret_shows_less_than_the_same_invention_on_the_default(self):
        self.assertLess(base_visibility("secret", True, 4.0, SECRET_EXPOSURE), base_visibility("default", True, 4.0, SECRET_EXPOSURE))

    def test_a_harder_secret_shows_less(self):
        self.assertLess(base_visibility("secret", True, 8.0, SECRET_EXPOSURE), base_visibility("secret", True, 2.0, SECRET_EXPOSURE))

    def test_a_licensed_or_not_yet_public_invention_is_kept_as_shut_as_a_secret(self):
        self.assertEqual(base_visibility("license", True, 4.0, SECRET_EXPOSURE), SECRET_EXPOSURE / 4.0)
        self.assertEqual(base_visibility("default", False, 4.0, SECRET_EXPOSURE), SECRET_EXPOSURE / 4.0)


class Holdings(unittest.TestCase):

    def test_the_share_held_is_the_fraction_found_and_nothing_with_nothing_to_hold(self):
        self.assertEqual(held_share(["a", "b", "c", "d"], {"a", "c"}), 0.5)
        self.assertEqual(held_share([], {"a"}), 0.0)

    def test_the_weapons_the_state_holds_are_the_founders_military_inventions_in_its_knowledge(self):
        game = types.SimpleNamespace(
            state=types.SimpleNamespace(seats={}), state_treasury=lambda: types.SimpleNamespace(knowledge={"a", "c"}),
            _diffusible_ids=lambda trait: ["a", "b", "c"])
        with mock.patch.object(society_diffusion.seat_builds, "built_by_any", lambda seats, ids: ids):
            self.assertEqual(DiffusionMixin.state_military_weapons_held(game), 2)


class Licensing(DisclosureMixin):
    def __init__(self):
        self.actors = types.SimpleNamespace(get=lambda identity: types.SimpleNamespace(kind="firm"))
        self.state = types.SimpleNamespace(
            seats={}, acting_seat="me", scenario=types.SimpleNamespace(year=120),
            projects=types.SimpleNamespace(disclosures={}))

    def seat_party(self, seat_id):
        return "party"


class ChoosingALicence(unittest.TestCase):

    def license(self, problem="", granted=True):
        game = Licensing()
        with mock.patch.object(society_disclosure, "SimWorld", lambda sim: None), \
                mock.patch.object(society_disclosure.licence, "terms_problem", lambda *args: problem), \
                mock.patch.object(society_disclosure.licence, "grant", lambda *args: granted):
            return game, game._license("x", "firm:a", 1000.0, 0.1)

    def test_an_accepted_licence_is_recorded_with_its_terms_and_moves_the_invention_off_the_default(self):
        game, reply = self.license()
        self.assertTrue(reply["ok"])
        record = game.state.projects.disclosures["x"]
        self.assertEqual(record["mode"], "license")
        self.assertEqual(record["licensees"]["firm:a"], {"fee": 1000.0, "royalty": 0.1, "year": 120})

    def test_refused_terms_record_nothing_and_carry_the_refusals_cause(self):
        from sim.refusal import Refusal
        game, reply = self.license(problem=Refusal("fee_above_value", "no"))
        self.assertFalse(reply["ok"])
        self.assertEqual(reply["cause"], "fee_above_value")
        self.assertEqual(game.state.projects.disclosures, {})

    def test_a_licensee_that_can_already_make_it_is_refused_and_nothing_is_recorded(self):
        game, reply = self.license(granted=False)
        self.assertFalse(reply["ok"])
        self.assertEqual(game.state.projects.disclosures, {})


if __name__ == "__main__":
    unittest.main()
