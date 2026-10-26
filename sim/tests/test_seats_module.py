"""The seats module: joining a seat, the lists of who plays, goals and win conditions. The module is built with plain values
for the views it reads and the seat registry a plain dict; no game."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim.refusal import Refusal
from sim.seats import join_rules
from sim.seats.api import (JoinCastSeats, JoinSeat, RecordGoalReached, RegisterSeat, SeatsSeat, SetGoal, ForgetGoalCaches)
from sim.seats.module import Seats
from sim.tests import module_harness

TREE = {"a": {"name": "A"}, "b": {"name": "B"}}


def seat(kind="household", country=None, goal=None, dead_reason=None, goal_year=None):
    return SimpleNamespace(kind=kind, country=country, goal=goal, holds_household=kind != "country",
                           modules={"seats": SeatsSeat(goal_year=goal_year, dead_reason=dead_reason)})


def seats_over(registry, acting="founder", civilisation=None, answers=None, **views):
    module = module_harness.build(
        Seats, seat=registry[acting].modules["seats"] if acting in registry else SeatsSeat(), answers=answers or {},
        views=dict({"legacy_seats": registry, "civilisation": civilisation or {"id": "home"}, "tree_nodes": TREE, "price_index": 2.0,
                    "kit_capital": lambda kit: {"poor": 10.0}[kit],
                    "founder_life_terms": {"immortal": False, "minimum": 5, "mean": 40.0, "spread": 0.0},
                    "legacy_dice": random.Random(3)}, **views))
    module.clock.act_as(acting)
    return module


class WhoIsPlaying(unittest.TestCase):

    def test_a_country_seat_and_an_ended_seat_are_not_playing(self):
        module = seats_over({"founder": seat(), "gone": seat(dead_reason="denounced"), "realm": seat("country")})
        self.assertEqual(module.seat_list(), {"joined": ["founder", "gone", "realm"], "playing": ["founder"]})
        self.assertEqual(module.ended_seats(), ["gone"])

    def test_the_run_is_over_when_every_household_seat_ended_or_reached_its_goal(self):
        module = seats_over({"founder": seat(goal_year=150), "gone": seat(dead_reason="ran out of money")})
        self.assertTrue(module.run_over())

    def test_a_seat_with_no_goal_reached_keeps_the_run_going(self):
        self.assertFalse(seats_over({"founder": seat()}).run_over())

    def test_the_countries_a_country_seat_plays_are_listed_once_with_the_games_own_for_none(self):
        module = seats_over({"founder": seat(), "a": seat("country", "north"), "b": seat("country", "north"), "c": seat("country")})
        self.assertEqual(module.played_countries(), ["home", "north"])

    def test_the_acting_country_is_none_for_the_games_own_and_the_partner_otherwise(self):
        registry = {"founder": seat(), "envoy": seat(country="north")}
        self.assertIsNone(seats_over(registry).acting_country())
        self.assertEqual(seats_over(registry, acting="envoy").acting_country(), "north")


class Joining(unittest.TestCase):

    def test_a_seat_is_registered_with_capital_at_the_societys_prices_and_a_drawn_lifespan(self):
        module = seats_over({"founder": seat()})
        module.join_seat(JoinSeat("second", {"capital": 100.0, "starting_techs": ["a"]}))
        (sent,) = module_harness.sent(module)
        self.assertEqual((sent.seat_id, sent.capital, sent.founder_years), ("second", 200.0, 40.0))

    def test_a_kit_is_priced_by_the_kit_view(self):
        module = seats_over({"founder": seat()})
        module.join_seat(JoinSeat("second", {"kit": "poor"}))
        self.assertEqual(module_harness.sent(module)[0].capital, 20.0)

    def test_no_capital_and_no_kit_is_an_empty_purse(self):
        module = seats_over({"founder": seat()})
        module.join_seat(JoinSeat("second", {}))
        self.assertEqual(module_harness.sent(module)[0].capital, 0.0)

    def test_an_immortal_run_gives_a_founder_no_end_and_draws_nothing(self):
        dice = random.Random(3)
        module = seats_over({"founder": seat()}, founder_life_terms={"immortal": True, "minimum": 5, "mean": 40.0, "spread": 9.0},
                            legacy_dice=dice)
        module.join_seat(JoinSeat("second", {}))
        self.assertEqual(module_harness.sent(module)[0].founder_years, 1e9)
        self.assertEqual(dice.getstate(), random.Random(3).getstate())

    def test_a_template_naming_a_technology_the_tree_lacks_is_refused_and_nothing_is_sent(self):
        module = seats_over({"founder": seat()})
        answer = module.join_seat(JoinSeat("third", {"starting_techs": ["nowhere"]}))
        self.assertIsInstance(answer, Refusal)
        self.assertEqual(answer.cause, "unknown_starting_techs")
        self.assertEqual(module_harness.sent(module), [])

    def test_a_country_seat_needs_a_government_to_hold(self):
        registry = SimpleNamespace(state=SimpleNamespace(countries={"north": 1}), government_of=lambda name: "gov" if name == "home" else None)
        module = seats_over({"founder": seat()}, seeded_actor_registry=registry)
        answer = module.join_seat(JoinSeat("realm", {"kind": "country", "country": "north"}))
        self.assertIsInstance(answer, Refusal)
        self.assertEqual(answer.cause, "no_government")

    def test_a_country_seat_of_the_games_own_country_is_registered_with_no_country(self):
        registry = SimpleNamespace(state=SimpleNamespace(countries={"home": 1}), government_of=lambda name: "gov")
        module = seats_over({"founder": seat()}, seeded_actor_registry=registry)
        module.join_seat(JoinSeat("realm", {"kind": "country"}))
        self.assertIsNone(module_harness.sent(module)[0].template["country"])

    def test_a_country_seat_still_draws_its_founders_lifespan(self):
        registry = SimpleNamespace(state=SimpleNamespace(countries={"home": 1}), government_of=lambda name: "gov")
        dice = random.Random(3)
        module = seats_over({"founder": seat()}, seeded_actor_registry=registry, legacy_dice=dice)
        module.join_seat(JoinSeat("realm", {"kind": "country"}))
        fresh = random.Random(3)
        fresh.gauss(40.0, 0.0)
        self.assertEqual(dice.getstate(), fresh.getstate())

    def test_the_cast_seats_join_in_order_and_a_seat_already_there_is_left(self):
        civilisation = {"id": "home", "cast": {"seats": [{"id": "rival", "capital": 10.0}, {"id": "founder"}, {"id": "ally"}]}}
        module = seats_over({"founder": seat()}, civilisation=civilisation)
        self.assertEqual(module.join_cast_seats(JoinCastSeats()), ["rival", "ally"])
        self.assertEqual([type(command) for command in module_harness.sent(module)], [RegisterSeat, RegisterSeat])

    def test_a_refusal_in_the_cast_stops_the_join_and_is_the_answer(self):
        civilisation = {"id": "home", "cast": {"seats": [{"id": "rival", "starting_techs": ["nowhere"]}]}}
        answer = seats_over({"founder": seat()}, civilisation=civilisation).join_cast_seats(JoinCastSeats())
        self.assertIsInstance(answer, Refusal)


class JoinRules(unittest.TestCase):

    def test_a_stated_capital_wins_over_a_kit(self):
        self.assertEqual(join_rules.capital_of({"capital": 5.0, "kit": "poor"}, 3.0, lambda kit: 99.0), 15.0)

    def test_a_mortal_founders_years_never_fall_below_the_minimum(self):
        self.assertEqual(join_rules.founder_years(False, 5, 2.0, 0.0, lambda mean, spread: mean), 5)


class Goals(unittest.TestCase):

    def goals_over(self, goal="c", goal_year=None, goal_years=None):
        registry = {"founder": seat(goal=goal)}
        registry["founder"].modules["seats"].goal_years = dict(goal_years or {})
        registry["founder"].modules["seats"].goal_year = goal_year
        module = seats_over(registry, answers={ForgetGoalCaches: None})
        return module, registry["founder"]

    def test_the_goal_view_names_the_goal_and_the_years(self):
        module, _ = self.goals_over(goal_year=1000, goal_years={"c": 1000})
        self.assertEqual(module.goal(), {"node": "c", "year": 1000, "years": {"c": 1000}})

    def test_the_formal_goal_records_its_year_when_reached(self):
        module, _ = self.goals_over()
        module.record_goal_reached(RecordGoalReached("c", 1000))
        self.assertEqual((module.seat.goal_years, module.seat.goal_year), ({"c": 1000}, 1000))

    def test_a_node_that_is_not_the_goal_records_nothing(self):
        module, _ = self.goals_over()
        module.record_goal_reached(RecordGoalReached("a", 1000))
        self.assertEqual((module.seat.goal_years, module.seat.goal_year), ({}, None))

    def test_a_new_goal_starts_with_no_year_drops_the_caches_and_each_goal_keeps_its_own(self):
        module, held = self.goals_over(goal_year=1000, goal_years={"c": 1000})
        module.set_goal(SetGoal("d"))
        self.assertEqual((held.goal, module.seat.goal_year), ("d", None))
        self.assertEqual(module_harness.sent(module), [ForgetGoalCaches()])
        module.record_goal_reached(RecordGoalReached("d", 1007))
        self.assertEqual(module.seat.goal_years, {"c": 1000, "d": 1007})

    def test_returning_to_a_reached_goal_restores_its_year(self):
        module, _ = self.goals_over(goal_year=None, goal_years={"c": 1000})
        module.set_goal(SetGoal("c"))
        self.assertEqual(module.seat.goal_year, 1000)

    def test_an_attribute_goal_reads_the_games_number_and_refuses_a_private_path(self):
        module, _ = self.goals_over()
        module.needs.game_attribute = lambda path: 7
        self.assertEqual(module.win_condition_value({"source": "attribute", "path": "slaves"}), 7.0)
        with self.assertRaises(ValueError):
            module.win_condition_value({"source": "attribute", "path": "_x"})

    def test_a_generation_goal_is_one_sources_share(self):
        module, _ = self.goals_over()
        module.needs.generation_breakdown = lambda: {"total_kw": 8.0, "sources_kw": {"coal": 2.0}}
        self.assertEqual(module.win_condition_value({"source": "generation_share", "key": "coal"}), 0.25)

    def test_a_metric_the_engine_does_not_know_raises(self):
        module, _ = self.goals_over()
        with self.assertRaises(ValueError):
            module.win_condition_value({"metric": "nonsense"})


if __name__ == "__main__":
    unittest.main()
