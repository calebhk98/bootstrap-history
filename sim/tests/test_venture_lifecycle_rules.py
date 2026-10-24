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

from sim.engine import economy_production, projects_staffing
from sim.engine.economy_production import ProductionMixin
from sim.engine.projects_capability import CapabilityMixin
from sim.engine.projects_staffing import StaffingMixin
from sim.engine.projects_venture_quotes import VentureQuotesMixin
from sim.engine.projects_ventures import VenturesMixin
from sim.engine.venture_net_loss import flags_net_loss
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


class Capabilities(CapabilityMixin):
    """The tree, what is known and what runs."""
    NOT_OPERATING_BENEFIT = {"patron": "your protection", "university": "your protection", "school": "literacy"}

    def __init__(self, known, running):
        self.nodes = {name: {} for name in ("patron", "university", "school")}
        self.known, self.open = set(known), set(running)

    def has(self, node_id):
        return node_id in self.known

    def running(self, node_id):
        return node_id in self.open

    def mechanic(self, node_id, kind):
        return {"redundant_with": ("school",)} if node_id == "university" else {}


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


class Reopening(VentureQuotesMixin):
    SCALABLE_INSTITUTIONS = frozenset()
    STAFF_CLOSURE_GRACE = 6
    STAFF_CLOSURE_DISCOUNT = 0.1
    RESTORE_COST_SHARE_OF_BUILD = 0.3
    RESTORE_COST_MIN_UPKEEP_YEARS = 2.0

    def __init__(self, venture=True, closure_age=None, capex=1000.0):
        self.venture, self.age, self.capex = venture, closure_age, capex
        self.nodes = {"shop": {"up": 50.0}}

    def is_venture(self, node_id):
        return self.venture

    def venture_capex(self, node_id):
        return self.capex

    def project_cost(self, node_id):
        return 2000.0

    def staff_closure_age(self, node_id):
        return self.age


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
        game = Reopening(venture=False)
        game.nodes["shop"]["up"] = 1000.0
        self.assertEqual(game.reopen_fee("shop"), 2000.0)


class Mothballing(StaffingMixin):
    CLOSED_BY_CHOICE = "choice"

    def __init__(self, upkeep=0.0, hands=(0.0, 0.0), running=True, granted=False, done=True):
        self.closed = []
        self.hands = hands
        self.state = types.SimpleNamespace(projects=types.SimpleNamespace(
            done={"shop"} if done else set(), granted={"shop"} if granted else set(),
            operating={"shop"} if running else set()))
        self.nodes = {"shop": {"up": upkeep, "rev": 0.0, "cat": "craft"}}

    def venture_hands(self, node_id):
        return self.hands

    def never_abandon(self, node_id):
        return False

    def venture_real_earnings(self, node_id):
        return 0.0

    def venture_real_upkeep(self, node_id):
        return 0.0

    def close_work(self, node_id, reason):
        self.closed.append((node_id, reason))

    def reopen_fee(self, node_id, units):
        return 10.0

    def reopen_units(self, node_id):
        return 1.0


class Mothball(unittest.TestCase):
    def mothball(self, **kwargs):
        game = Mothballing(**kwargs)
        with mock.patch.object(projects_staffing, "money_text", lambda money, sim, grouped=False: "%g" % money):
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


class Ramp(ProductionMixin):
    def __init__(self, opened=None, done_year=None, year=130):
        self.opened, self.done_year_value = opened, done_year
        business = types.SimpleNamespace(opened_year_of=lambda node_id, default: opened if opened is not None else default)
        self.state = types.SimpleNamespace(
            projects=types.SimpleNamespace(business=business, done_year={"shop": done_year} if done_year is not None else {}),
            scenario=types.SimpleNamespace(year=year))
        self.cfg = {"revenue_ramp_years": 3}

    def industry_depth(self, node_id):
        return 0.0


class Opening(VenturesMixin):
    """The tree and what is known, granted and running, for the refusals that come before any money moves."""
    SCALABLE_INSTITUTIONS = frozenset()

    def __init__(self, done=True, granted=False, practisable=False, venture=True, operating=False):
        self.nodes = {"shop": {}}
        self.state = types.SimpleNamespace(projects=types.SimpleNamespace(
            done={"shop"} if done else set(), granted={"shop"} if granted else set(),
            operating={"shop"} if operating else set()))
        self.practisable, self.venture = practisable, venture

    def _practisable(self, node_id):
        return self.practisable

    def is_venture(self, node_id):
        return self.venture


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
        with mock.patch.object(economy_production.plant_figures, "ramp", return_value=0.5) as ramp:
            Ramp(**kwargs).venture_ramp("shop")
        return ramp.call_args.args[0]

    def test_the_ramp_counts_from_the_year_the_concern_opened_not_the_year_it_was_worked_out(self):
        self.assertEqual(self.age_used(opened=130, done_year=100, year=130), 0)

    def test_a_reopened_concern_keeps_its_first_opening_year(self):
        self.assertEqual(self.age_used(opened=130, done_year=100, year=140), 10)

    def test_a_concern_with_no_recorded_opening_counts_from_the_year_it_was_worked_out(self):
        self.assertEqual(self.age_used(opened=None, done_year=100, year=104), 4)

    def test_the_ramp_is_the_plant_figures_over_the_configured_years(self):
        with mock.patch.object(economy_production.plant_figures, "ramp", return_value=0.5) as ramp:
            result = Ramp(opened=130, year=131).venture_ramp("shop")
        self.assertEqual(result, 0.5)
        self.assertEqual(ramp.call_args.args[:3], (1, 3, 0.0))


if __name__ == "__main__":
    unittest.main()
