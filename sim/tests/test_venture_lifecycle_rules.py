"""Complaint 640: the rules of a concern's life, each called on a stand-in or on inputs written out here. A net-loss concern is
flagged at opening unless it is a capability institution; the shut concerns' yearly value is the sum of what the profitable ones
would clear; a capability that is done and not operating is named with the benefit it is not collecting, unless another open one
covers it; reopening costs the grace fee after a staffing closure and the whole fee otherwise; mothball frees a concern held
by staff time alone and refuses one with nothing to save; a ramp counts from the year the concern opened."""
QUICK_TOPIC = True
UNDER_TEST = {"open_venture"}   # called on the stand-in `Opening`, for the refusals before any money moves

import types
import unittest
from unittest import mock

from sim.production import revenue as production_revenue
from sim.tests import production_host, projects_host, ventures_host
from sim.ventures.net_loss import flags_net_loss
from sim.refusal import cause_of
from sim.ui.proto.shut_concerns import shut_concerns_yearly_value


class NetLossFlag(unittest.TestCase):
    def test_a_concern_costing_more_than_it_earns_fully_ramped_is_flagged(self):
        self.assertTrue(flags_net_loss(120.0, 100.0, False))

    def test_a_concern_earning_more_than_it_costs_is_not(self):
        self.assertFalse(flags_net_loss(80.0, 100.0, False))

    def test_a_concern_earning_exactly_what_it_costs_is_not(self):
        self.assertFalse(flags_net_loss(100.0, 100.0, False))

    def test_a_capability_institution_losing_money_is_never_flagged(self):
        self.assertFalse(flags_net_loss(500.0, 0.0, True))


class ShutConcernsValue(unittest.TestCase):
    def test_the_profitable_shut_concerns_add_up_what_they_would_clear(self):
        self.assertEqual(shut_concerns_yearly_value([(1000.0, 400.0), (300.0, 100.0)]), 800.0)

    def test_a_concern_that_would_lose_money_is_left_out(self):
        self.assertEqual(shut_concerns_yearly_value([(1000.0, 400.0), (100.0, 900.0)]), 600.0)

    def test_nothing_shut_or_nothing_profitable_gives_none_not_zero(self):
        self.assertIsNone(shut_concerns_yearly_value([]))
        self.assertIsNone(shut_concerns_yearly_value([(100.0, 900.0)]))


def Capabilities(known, running):
    """The tree, what is known and what runs."""
    benefits = {"patron": "your protection", "university": "your protection", "school": "literacy"}
    module = production_host.build(
        tree_nodes={name: {} for name in benefits}, capability_sets=(set(), set(), benefits),
        techniques_held=set(known),
        mechanic=lambda kind: {"patron": {}, "school": {}, "university": {"redundant_with": ("school",)}})
    module.running = lambda node_id: node_id in set(running)
    return module


class CapabilityGaps(unittest.TestCase):
    def ids(self, known, running):
        return [gap["id"] for gap in Capabilities(known, running).capability_gaps()]

    def test_a_capability_done_and_not_operating_is_named_with_the_benefit_it_is_not_collecting(self):
        gaps = Capabilities({"patron"}, set()).capability_gaps()
        self.assertEqual([(gap["id"], gap["benefit_switched_off"]) for gap in gaps], [("patron", "your protection")])

    def test_it_stops_being_named_the_moment_it_runs(self):
        self.assertEqual(self.ids({"patron"}, {"patron"}), [])

    def test_a_capability_not_yet_done_is_not_named(self):
        self.assertEqual(self.ids(set(), set()), [])

    def test_a_capability_whose_only_benefit_another_running_one_covers_is_not_named(self):
        self.assertEqual(self.ids({"university", "school"}, {"school"}), [])

    def test_it_is_named_while_both_are_closed(self):
        self.assertEqual(self.ids({"university", "school"}, set()), ["school", "university"])


def Reopening(venture=True, closure_age=None, up=50.0):
    """The ventures module over a one-concern tree: a concern's opening fee is 1000 and building it again cost 2000."""
    module = ventures_host.build(
        tree_nodes={"shop": {"up": up}}, is_venture=lambda node_id: venture, project_cost=lambda node_id: 2000.0,
        staff_closure_age=lambda node_id: closure_age)
    module.venture_capex = lambda node_id: 1000.0
    return module


class ReopenFee(unittest.TestCase):
    def test_a_concern_shut_for_want_of_staff_soon_ago_costs_the_discounted_share(self):
        self.assertAlmostEqual(Reopening(closure_age=2).reopen_fee("shop"), 100.0)

    def test_the_same_concern_after_the_grace_years_costs_the_whole_opening_fee(self):
        self.assertEqual(Reopening(closure_age=7).reopen_fee("shop"), 1000.0)

    def test_a_concern_not_shut_for_staff_costs_the_whole_opening_fee(self):
        self.assertEqual(Reopening(closure_age=None).reopen_fee("shop"), 1000.0)

    def test_a_scalable_institutions_fee_is_per_unit(self):
        self.assertEqual(Reopening(closure_age=None).reopen_fee("shop", 2.5), 2500.0)

    def test_a_work_that_is_not_a_concern_costs_a_share_of_building_it_again(self):
        self.assertEqual(Reopening(venture=False).reopen_fee("shop"), 2000.0 * 0.3)

    def test_that_share_is_never_less_than_some_years_of_its_upkeep(self):
        self.assertEqual(Reopening(venture=False, up=1000.0).reopen_fee("shop"), 2000.0)


def Mothballing(upkeep=0.0, hands=(0.0, 0.0), running=True, granted=False, done=True):
    """The projects module over a one-concern tree, with what closing it asks recorded in `.closed`."""
    projects = types.SimpleNamespace(done={"shop"} if done else set(), granted={"shop"} if granted else set(),
                                     operating={"shop"} if running else set())
    module = projects_host.build(
        projects_record=projects, tree={"shop": {"up": upkeep, "rev": 0.0, "cat": "craft"}}, venture_hands=lambda node_id: hands,
        never_abandon=lambda node_id: False, venture_real_earnings=lambda node_id: 0.0, venture_real_upkeep=lambda node_id: 0.0,
        reopen_fee=lambda node_id: 10.0, money_text=lambda amount, grouped=False, short=False: "%g" % amount)
    module.closed = []
    module.CLOSED_BY_CHOICE = "choice"
    module.close_work = lambda node_id, reason: module.closed.append((node_id, reason))
    return module


class Mothball(unittest.TestCase):
    def mothball(self, **kwargs):
        game = Mothballing(**kwargs)
        ok, note = game.mothball_work("shop")
        return game, ok, note

    def test_a_concern_with_no_money_upkeep_but_staff_tied_up_is_released(self):
        game, ok, _note = self.mothball(upkeep=0.0, hands=(0.0, 0.75))
        self.assertTrue(ok)
        self.assertEqual(game.closed, [("shop", "choice")])

    def test_a_concern_with_money_upkeep_and_no_staff_is_released(self):
        game, ok, _note = self.mothball(upkeep=40.0)
        self.assertTrue(ok)
        self.assertEqual(game.closed, [("shop", "choice")])

    def test_a_concern_with_nothing_to_save_is_refused_with_its_cause_and_nothing_closes(self):
        game, ok, note = self.mothball(upkeep=0.0, hands=(0.0, 0.0))
        self.assertFalse(ok)
        self.assertEqual(cause_of(note), "nothing_to_save")
        self.assertEqual(game.closed, [])

    def test_staff_held_only_counts_while_the_concern_runs(self):
        _game, ok, _note = self.mothball(upkeep=0.0, hands=(0.0, 0.75), running=False)
        self.assertFalse(ok)

    def test_something_the_society_has_is_not_the_players_to_stop(self):
        game, ok, _note = self.mothball(upkeep=40.0, granted=True)
        self.assertFalse(ok)
        self.assertEqual(game.closed, [])

    def test_something_not_built_is_refused(self):
        _game, ok, _note = self.mothball(upkeep=40.0, done=False)
        self.assertFalse(ok)


def Ramp(opened=None, done_year=None, year=130):
    module = production_host.build(
        year=year, game_setting={"revenue_ramp_years": 3}, done_year={"shop": done_year} if done_year is not None else {},
        venture_opened_year=lambda node_id, default: opened if opened is not None else default)
    module.industry_depth = lambda node_id: 0.0
    return module


def Opening(done=True, granted=False, practisable=False, venture=True, operating=False):
    """The ventures module over the tree and what is known, granted and running, for the refusals that come before any money moves."""
    return ventures_host.build(
        tree_nodes={"shop": {}}, is_venture=lambda node_id: venture, practisable=lambda node_id: practisable,
        projects_record=ventures_host.projects_record(
            done={"shop"} if done else set(), granted={"shop"} if granted else set(), operating={"shop"} if operating else set()))


class OpenRefusals(unittest.TestCase):
    def refused(self, **kwargs):
        ok, why = Opening(**kwargs).open_venture("shop")
        self.assertFalse(ok)
        return why

    def test_an_unknown_node_is_refused(self):
        self.assertEqual(Opening().open_venture("nowhere"), (False, "no such node"))

    def test_something_not_yet_worked_out_is_refused(self):
        self.refused(done=False)

    def test_your_own_practice_is_refused_as_already_yours(self):
        self.assertEqual(cause_of(self.refused(granted=True, practisable=True)), "already_your_practice")

    def test_a_skill_the_society_has_that_is_not_your_practice_is_refused_without_that_cause(self):
        self.assertIsNone(cause_of(self.refused(granted=True, practisable=False)))

    def test_knowledge_that_is_not_a_going_concern_is_refused(self):
        self.refused(venture=False)

    def test_a_concern_already_running_is_refused(self):
        self.refused(operating=True)


class VentureRamp(unittest.TestCase):
    def age_used(self, **kwargs):
        with mock.patch.object(production_revenue.plant_figures, "ramp", return_value=0.5) as ramp:
            Ramp(**kwargs).venture_ramp("shop")
        return ramp.call_args.args[0]

    def test_the_ramp_counts_from_the_year_the_concern_opened_not_the_year_it_was_worked_out(self):
        self.assertEqual(self.age_used(opened=130, done_year=100, year=130), 0)

    def test_a_reopened_concern_keeps_its_first_opening_year(self):
        self.assertEqual(self.age_used(opened=130, done_year=100, year=140), 10)

    def test_a_concern_with_no_recorded_opening_counts_from_the_year_it_was_worked_out(self):
        self.assertEqual(self.age_used(opened=None, done_year=100, year=104), 4)

    def test_the_ramp_is_the_plant_figures_over_the_configured_years(self):
        with mock.patch.object(production_revenue.plant_figures, "ramp", return_value=0.5) as ramp:
            result = Ramp(opened=130, year=131).venture_ramp("shop")
        self.assertEqual(result, 0.5)
        self.assertEqual(ramp.call_args.args[:3], (1, 3, 0.0))


class OperatingWorks(unittest.TestCase):
    def test_the_open_works_are_the_live_set_of_the_seats_plants(self):
        module = ventures_host.build(operating={"shop"})
        self.assertEqual(set(module.operating()), {"shop"})
        module.seat.business.open_plant("mill", 100)
        self.assertEqual(set(module.operating()), {"shop", "mill"})


if __name__ == "__main__":
    unittest.main()
