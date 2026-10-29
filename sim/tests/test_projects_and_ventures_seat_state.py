"""The state the projects, ventures and seats modules own, one function at a time: each view answers a value that was set, each
command changes the seat state it names, and each seat state survives a save and a load. No game is built."""
QUICK_TOPIC = True

import json
import unittest

from sim.agents.api import Business, Plant
from sim.engine.state import deserialize_state, serialize_state
from sim.invalidating import ActiveProjectState
from sim.production.api import RefreshOperatingCaches
from sim.projects.commands import CloseSpendYear, NoteYearSpend
from sim.projects.state import ProjectsSeat
from sim.seats.state import SeatsSeat
from sim.tests import module_harness, projects_host, ventures_host
from sim.ventures.api import (CloseConcern, ForgetClosureReason, MothballConcern, NoteConcernYear, RestoreConcern, ReviewConcerns, ReviewReopening, StopOperating,
                              VenturesSeat, WatchBusiness)


def round_trip(state, kind):
    return deserialize_state(json.loads(json.dumps(serialize_state(state))), kind)


class ProjectsViews(unittest.TestCase):
    def module(self, **fields):
        return projects_host.build(seat=ProjectsSeat(**fields))

    def test_the_bountied_nodes_are_the_seats_set(self):
        self.assertEqual(self.module(bountied={"a", "b"}).bountied_nodes(), {"a", "b"})

    def test_the_failed_attempts_are_the_seats_counts(self):
        self.assertEqual(dict(self.module(failed_attempts={"a": 2}).failed_attempt_counts()), {"a": 2})

    def test_the_credit_paid_towards_projects_is_the_seats_record(self):
        self.assertEqual(self.module(paid_towards={"a": 12.5}).paid_towards_projects(), {"a": 12.5})

    def test_the_bounties_paid_are_the_seats_count(self):
        self.assertEqual(self.module(bounties_paid=3).bounties_paid_total(), 3)

    def test_last_years_spending_is_none_until_a_year_has_closed_and_then_the_seats_figure(self):
        self.assertIsNone(self.module().spend_last_year())
        self.assertEqual(self.module(spend_last_year=40.0).spend_last_year(), 40.0)

    def test_the_active_projects_are_the_seats_in_the_order_started_and_their_ids_are_sorted(self):
        module = self.module(active={"b": {"ph_left": 1.0}, "a": {"ph_left": 2.0}})
        self.assertEqual((list(module.active_projects()), module.active_project_ids()), (["b", "a"], ["a", "b"]))


class ProjectsCommands(unittest.TestCase):
    def test_a_year_spend_is_counted_and_the_close_makes_it_last_years_and_starts_again(self):
        module = projects_host.build()
        module.apply_note_year_spend(NoteYearSpend(30.0))
        module.apply_note_year_spend(NoteYearSpend(12.5))
        module.apply_close_spend_year(CloseSpendYear())
        self.assertEqual(module.seat.spend_last_year, 42.5)
        module.apply_close_spend_year(CloseSpendYear())
        self.assertEqual(module.seat.spend_last_year, 0.0)


class ProjectsSeatSaves(unittest.TestCase):
    def test_every_field_survives_a_save_and_a_load_in_its_order(self):
        seat = ProjectsSeat(active={"z": ActiveProjectState(ph_left=5.0, cost_left=9.0), "a": ActiveProjectState(ph_left=1.0, cost_left=2.0)},
                            failed_attempts={"printing": 3}, bountied={"a"}, paid_towards={"z": 7.0}, spend_last_year=11.0, bounties_paid=2,
                            excluded={"category:war"})
        loaded = round_trip(seat, ProjectsSeat)
        self.assertEqual((list(loaded.active), loaded.active["z"].ph_left, dict(loaded.failed_attempts), loaded.failed_attempts["never"], loaded.bountied,
                          loaded.paid_towards, loaded.spend_last_year, loaded.bounties_paid, loaded.excluded),
                         (["z", "a"], 5.0, {"printing": 3}, 0, {"a"}, {"z": 7.0}, 11.0, 2, {"category:war"}))

    def test_a_year_not_yet_spent_stays_none(self):
        self.assertIsNone(round_trip(ProjectsSeat(), ProjectsSeat).spend_last_year)


class VenturesViews(unittest.TestCase):
    def module(self):
        seat = VenturesSeat(businesses=[Business(plants=[Plant(entry_key="mill", size=2.0, opened_year=90),
                                                         Plant(entry_key="forge", state="mothballed", reason="staff", since_year=95)])])
        return ventures_host.build(seat=seat)

    def test_the_operating_works_are_those_with_a_running_plant(self):
        self.assertEqual(set(self.module().operating()), {"mill"})

    def test_the_mothballed_works_are_those_with_a_shut_plant(self):
        self.assertEqual(set(self.module().mothballed()), {"forge"})

    def test_a_shut_work_that_records_why_has_its_reason_and_year(self):
        self.assertEqual(dict(self.module().closure_records()), {"forge": {"reason": "staff", "year": 95}})

    def test_a_plants_size_and_opening_year_are_the_seats_record_and_a_work_without_one_has_the_default(self):
        module = self.module()
        self.assertEqual((module.venture_size("mill"), module.venture_opened_year("mill", 0), module.venture_size("none"),
                          module.venture_opened_year("none", 7)), (2.0, 90, 1.0, 7))

    def test_every_seats_operating_works_are_answered_by_seat(self):
        module = self.module()
        module.needs.seat_list = lambda: {"joined": ["founder", "second"]}
        module.seat_slot_of = lambda seat_id: module.seat if seat_id == "founder" else VenturesSeat()
        answered = module.operating_by_seat()
        self.assertEqual({seat_id: set(held) for seat_id, held in answered.items()}, {"founder": {"mill"}, "second": set()})


class VenturesCommands(unittest.TestCase):
    def module(self):
        module = ventures_host.build(operating={"mill", "forge"})
        module.seat_slot_of = lambda seat_id: module.seat
        return module

    def test_mothballing_a_concern_keeps_its_plant_switched_off_with_the_reason_and_year(self):
        module = self.module()
        module.apply_mothball_concern(MothballConcern("mill", 120, "by_choice"))
        self.assertEqual((set(module.operating()), dict(module.closure_records())), ({"forge"}, {"mill": {"reason": "by_choice", "year": 120}}))

    def test_restoring_a_concern_switches_its_plant_back_on_and_forgets_why_it_was_shut(self):
        module = self.module()
        module.apply_mothball_concern(MothballConcern("mill", 120, "staff"))
        module.apply_restore_concern(RestoreConcern("mill"))
        self.assertEqual((set(module.operating()), dict(module.closure_records())), ({"mill", "forge"}, {}))

    def test_closing_a_concern_forgets_its_plant_whatever_its_state(self):
        module = self.module()
        module.apply_close_concern(CloseConcern("mill"))
        self.assertEqual(module.seat.business.plant_of("mill"), None)

    def test_forgetting_a_closure_reason_answers_whether_one_was_dropped(self):
        module = self.module()
        module.apply_mothball_concern(MothballConcern("mill", 120, "staff"))
        self.assertEqual((module.apply_forget_closure_reason(ForgetClosureReason("mill", "by_choice")),
                          module.apply_forget_closure_reason(ForgetClosureReason("mill", "staff"))), (False, True))

    def test_stopping_operating_closes_the_running_plants_named_and_leaves_a_shut_one(self):
        module = self.module()
        module.apply_mothball_concern(MothballConcern("forge", 120, "staff"))
        module.apply_stop_operating(StopOperating(("mill", "forge")))
        self.assertEqual((module.seat.business.plant_of("mill"), module.seat.business.state_of("forge")), (None, "mothballed"))

    def test_a_concerns_year_tallies_its_margin_and_counts_its_losing_years(self):
        module = self.module()
        module.apply_note_concern_year(NoteConcernYear("mill", -3.0))
        module.apply_note_concern_year(NoteConcernYear("mill", -1.0))
        plant = module.seat.business.plant_of("mill")
        self.assertEqual((plant.margin, plant.loss_years), (-1.0, 2))

    def test_the_review_is_run_on_the_seats_business_for_its_household_and_the_actors_world_under_the_rules_named(self):
        module = ventures_host.build(legacy_household_actor="household", actor_world="world")
        module.seat.business.review = lambda owner, world, rules: (owner, world, rules)
        self.assertEqual(module.apply_review_concerns(ReviewConcerns(("staff",))), ("household", "world", ("staff",)))

    def test_the_reopening_review_is_run_on_the_seats_business_for_its_household_and_the_actors_world(self):
        module = ventures_host.build(legacy_household_actor="household", actor_world="world")
        module.seat.business.review_reopening = lambda owner, world: [owner, world]
        self.assertEqual(module.apply_review_reopening(ReviewReopening()), ["household", "world"])

    def test_a_watched_business_tells_production_and_moves_the_operating_version_when_a_plant_opens(self):
        module = self.module()
        module.apply_watch_business(WatchBusiness("founder"))
        before = module.operating_version()
        module.seat.business.open_plant("kiln", 100)
        self.assertNotEqual(module.operating_version(), before)
        self.assertIn(RefreshOperatingCaches(), module_harness.sent(module))


class VenturesSeatSaves(unittest.TestCase):
    def test_the_businesses_and_their_plants_survive_a_save_and_a_load(self):
        seat = VenturesSeat(businesses=[Business(business_id="founder", plants=[
            Plant(entry_key="mill", size=2.0, opened_year=90, margin=4.5, loss_years=1),
            Plant(entry_key="forge", state="mothballed", reason="staff", since_year=95)])])
        loaded = round_trip(seat, VenturesSeat)
        self.assertEqual((loaded.businesses, loaded.business.closures()["forge"]), (seat.businesses, {"reason": "staff", "year": 95}))


class DissolutionCountSaves(unittest.TestCase):
    def test_the_years_without_a_director_survive_a_save_and_a_load(self):
        self.assertEqual(round_trip(SeatsSeat(stalled=4), SeatsSeat).stalled, 4)


if __name__ == "__main__":
    unittest.main()
