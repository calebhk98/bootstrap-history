"""Licensing and disclosure of an invention: which terms are refused, how visible a disclosure mode leaves it, how
the state's military holdings are counted, and what choosing a licence records. Stand-ins carry what each reads."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.agents.licence import terms_problem
from sim.diffusion import disclosure
from sim.diffusion.adoption_share import held_share
from sim.diffusion.module import Diffusion
from sim.diffusion.state import DiffusionSeat
from sim.seats.api import base_visibility
from sim.tests import module_harness

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
        class Armed(Diffusion):
            def diffusible_ids(self, category):
                return ["a", "b", "c"]
        module = module_harness.build(Armed, views={"state_knowledge": lambda: {"a", "c"},
                                                    "built_by_any_seat": lambda among: among})
        self.assertEqual(module.state_military_weapons_held(), 2)


def licensing():
    """The diffusion module of seat "me" in year 120, with one firm to license to."""
    registry = types.SimpleNamespace(get=lambda identity: types.SimpleNamespace(kind="firm"))
    module = module_harness.build(Diffusion, seat=DiffusionSeat(), views={
        "cast": lambda: registry, "seat_list": lambda: {"joined": ["me"], "playing": ["me"]},
        "seat_party": lambda seat_id: "party", "year": 120, "actor_world": lambda: None})
    module.clock.act_as("me")
    return module


class ChoosingALicence(unittest.TestCase):

    def license(self, problem="", granted=True):
        game = licensing()
        with mock.patch.object(disclosure.licence, "terms_problem", lambda *args: problem), \
                mock.patch.object(disclosure.licence, "grant", lambda *args: granted):
            return game, game._license("x", "firm:a", 1000.0, 0.1)

    def test_an_accepted_licence_is_recorded_with_its_terms_and_moves_the_invention_off_the_default(self):
        game, reply = self.license()
        self.assertTrue(reply["ok"])
        record = game.seat.disclosures["x"]
        self.assertEqual(record["mode"], "license")
        self.assertEqual(record["licensees"]["firm:a"], {"fee": 1000.0, "royalty": 0.1, "year": 120})

    def test_refused_terms_record_nothing_and_carry_the_refusals_cause(self):
        from sim.refusal import Refusal
        game, reply = self.license(problem=Refusal("fee_above_value", "no"))
        self.assertFalse(reply["ok"])
        self.assertEqual(reply["cause"], "fee_above_value")
        self.assertEqual(game.seat.disclosures, {})

    def test_a_licensee_that_can_already_make_it_is_refused_and_nothing_is_recorded(self):
        game, reply = self.license(granted=False)
        self.assertFalse(reply["ok"])
        self.assertEqual(game.seat.disclosures, {})


if __name__ == "__main__":
    unittest.main()
