"""Policies, creditors and hazard value shifts: what a business review spares and closes, the log naming what a seat shed or
creditors took, the payroll a household lets go, the default policy, a switch that cannot act, the stall diagnosis, the fee to
bring a shut work back and a hazard's gradual values delta. Each rule runs on inputs or a stub the test builds. The start gates and
restoring a shut work are test_start_gate_rules, the staff a household cannot pay is test_payroll_shed. That knowledge categories are never abandoned is test_category_traits; the loss rule
and the seizure of a plant are test_business_review; the cap on work in hand is test_start_money_rule."""
QUICK_TOPIC = True

import unittest
from sim.tests import workforce_stand_in
from types import SimpleNamespace

from sim.agents import business_review
from sim.agents.api import Business
from sim.constants import REGISTRY
from sim.engine import data as engine_data
from sim.hazards.window import hazards_not_yet_past
from sim.workforce.payroll_trim import payroll_means, staff_to_let_go
from sim.projects.review import SeatReview
from sim.engine.seat_defaults import default_policy
from sim.tests import polity_host
from sim.polity.api import ShiftValueWeight
from sim.projects.api import ReviewVentures
from sim.reporting.api import RecordEvent
from sim.tests import hazards_host, module_harness, projects_host, ventures_host
from sim.ui.proto.dispatch_ventures import _cmd_policy
from sim.ui.proto.state_waiting import _staff_fraction_note
from sim.finance.state import FinanceSeat
from sim.tests import finance_host
from sim.tests.ui_stand_in import Game


class _Owner(business_review.Reviewable):
    """An owner whose books force losses to be cut and whose creditors press; `spared` are the plants it keeps whatever they lose."""

    def __init__(self, business, spared=(), margins=None, cuts=True, presses=True):
        self.business = business
        self.spared, self.margins, self.cuts, self.presses = set(spared), margins or {}, cuts, presses
        self.shut_plants, self.seized = [], []

    def cuts_losses_now(self, world):
        return self.cuts and bool([key for key in self.business.operating() if self.margins.get(key, 0.0) < 0.0])

    def spares_plant(self, entry_key, world):
        return entry_key in self.spared

    def standing_margin(self, entry_key, world):
        return self.margins.get(entry_key, 0.0)

    def creditors_press(self, world):
        return self.presses and bool([key for key in self.business.operating() if self.margins.get(key, 0.0) < 0.0])

    def shut(self, entry_key, reason, world):
        self.shut_plants.append((entry_key, reason))
        self.business.mothball(entry_key, 100, reason)

    def receive_seizure(self, entry_key, proceeds, world):
        self.seized.append(entry_key)


class BusinessReviewSparesAndLeavesAlone(unittest.TestCase):
    """A loss-maker is shut and a spared one (knowledge, or what the goal needs) is not; a shut plant is left alone."""

    def _review(self, rules, spared=(), shut=()):
        business = Business.running(["shop", "school", "theory"])
        for entry_key in shut:
            business.mothball(entry_key, 99, "by_choice")
        owner = _Owner(business, spared=spared, margins={"shop": -5.0, "school": -1.0, "theory": -9.0})
        closed = business.review(owner, None, rules)
        return business, owner, closed

    def test_a_loss_making_plant_that_is_not_spared_is_shut_and_a_spared_one_is_kept(self):
        business, owner, closed = self._review((business_review.LOSS_MAKING,), spared={"theory"})
        self.assertEqual({entry_key for entry_key, _reason in owner.shut_plants}, {"shop", "school"})
        self.assertEqual(business.state_of("theory"), "operating")

    def test_the_creditors_take_the_worst_loss_makers_but_not_what_is_spared(self):
        business, owner, closed = self._review((business_review.CREDITOR_SEIZURE,), spared={"theory"})
        self.assertNotIn("theory", owner.seized)
        self.assertEqual(business.state_of("theory"), "operating")
        self.assertEqual(owner.seized[0], "shop")
        self.assertTrue(all(reason == business_review.CREDITOR_SEIZURE for _key, reason in closed))

    def test_a_plant_already_shut_is_not_shut_again(self):
        _business, owner, closed = self._review((business_review.LOSS_MAKING,), shut={"shop"})
        self.assertNotIn("shop", [entry_key for entry_key, _reason in owner.shut_plants])
        self.assertNotIn("shop", [closure.entry_key for closure in closed])


class SeatSparesWhatItMustKeep(unittest.TestCase):
    """The founder's seat spares knowledge (never abandoned) and what the society granted; the rest it may shed."""

    def _seat(self, never_abandoned=(), granted=()):
        module = projects_host.build(projects_record=Game(granted=set(granted)), year=1,
                                     never_abandon=lambda node_id: node_id in never_abandoned)
        return SeatReview(module, Game())

    def test_knowledge_and_what_is_granted_are_spared(self):
        seat = self._seat(never_abandoned={"theory"}, granted={"road"})
        self.assertTrue(seat.spares_plant("theory"))
        self.assertTrue(seat.spares_plant("road"))

    def test_an_ordinary_concern_is_not(self):
        self.assertFalse(self._seat(never_abandoned={"theory"}).spares_plant("shop"))


class LogNamesWhatClosed(unittest.TestCase):
    """The log says which concerns a seat shed, so a player can see what was lost and that the knowledge is kept."""

    def _events(self, module):
        return [command for command in module_harness.sent(module) if isinstance(command, RecordEvent)]

    def _shed(self, closed, capital):
        module = finance_host.build(acting_balance=capital, answers={
            ReviewVentures: lambda command: [business_review.Closure(key, business_review.LOSS_MAKING) for key in closed]})
        module.shed_loss_makers(100)
        return self._events(module)

    def _owing(self, closures):
        household = Game(capital=-1000.0, slaves=0, freedmen=0, artisans=0, scholars=0)
        module = finance_host.build(
            household=household, answers={
                ReviewVentures: lambda command: [business_review.Closure(key, business_review.CREDITOR_SEIZURE) for key in closures]})
        module.credit_limit = lambda revenue=None, upkeep=None, capital=None: 0.0
        module.answer_exhausted_credit(100)
        return self._events(module)

    def test_a_shed_concern_is_named_in_the_log_with_a_coded_kind(self):
        events = self._shed(["md2_sand_filtration"], -5.0)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, "arrears_closed_concerns")
        self.assertEqual(events[0].facts["concerns"], ["md2_sand_filtration"])

    def test_nothing_shed_logs_nothing(self):
        self.assertEqual(self._shed([], -5.0), [])

    def test_the_log_says_when_it_was_arrears_that_forced_it(self):
        in_arrears = self._shed(["a"], -5.0)[0].text
        solvent = self._shed(["a"], 5.0)[0].text
        # presentation: the line says the closure was forced by arrears only when it was
        self.assertIn("in arrears", in_arrears)
        self.assertNotIn("in arrears", solvent)

    def test_creditors_taking_concerns_are_named_in_the_log(self):
        taken = [event for event in self._owing(["shop"]) if event.kind == "creditors_took"]
        self.assertEqual(len(taken), 1)
        # presentation: the line names the concern and promises the knowledge is kept
        self.assertIn("shop", taken[0].text)
        self.assertIn("knowledge", taken[0].text)

    def test_creditors_who_took_nothing_say_nothing(self):
        self.assertEqual(self._owing([]), [])


class PayrollLetGo(unittest.TestCase):
    """A household that cannot pay its people lets go only the part of the payroll its means do not cover."""

    WAGES = {"smith": 100.0, "labourer": 20.0}

    def _cuts(self, payroll, means, employees):
        return staff_to_let_go(payroll, means, employees, lambda trade: self.WAGES.get(trade, 0.0))

    def test_the_means_are_the_takings_after_other_costs_plus_what_a_lender_will_still_advance(self):
        self.assertEqual(payroll_means(1000.0, 800.0, 50.0, 300.0), 200.0 + 350.0)
        self.assertEqual(payroll_means(1000.0, 800.0, -100.0, 300.0), 200.0 + 200.0)       # arrears use up the line
        self.assertEqual(payroll_means(1000.0, 800.0, -900.0, 300.0), 200.0)                # past the line adds nothing

    def test_nobody_goes_while_the_means_cover_the_payroll(self):
        self.assertEqual(self._cuts(500.0, 500.0, {"smith": 5.0}), {})
        self.assertEqual(self._cuts(500.0, 900.0, {"smith": 5.0}), {})

    def test_an_unaffordable_payroll_is_trimmed_to_what_can_be_paid_not_emptied(self):
        cuts = self._cuts(500.0, 300.0, {"smith": 5.0})
        self.assertEqual(cuts, {"smith": 2})          # 200 short is two smiths
        self.assertLess(sum(cuts.values()), 5.0)

    def test_the_dearest_trade_goes_first_and_whole_people_are_let_go(self):
        cuts = self._cuts(1000.0, 880.0, {"smith": 5.0, "labourer": 20.0})
        self.assertEqual(cuts, {"smith": 2})          # 120 short: two smiths (200) rather than six labourers
        short_by_a_little = self._cuts(1000.0, 999.0, {"smith": 5.0, "labourer": 20.0})
        self.assertEqual(short_by_a_little, {"smith": 1})   # rounded up to a whole person

    def test_with_no_money_left_to_borrow_the_whole_staff_can_go(self):
        cuts = self._cuts(600.0, 0.0, {"smith": 5.0, "labourer": 5.0})
        self.assertEqual(cuts, {"smith": 5.0, "labourer": 5.0})

    def test_nobody_is_cut_beyond_the_staff_held(self):
        self.assertEqual(self._cuts(1000.0, 0.0, {"smith": 2.0}), {"smith": 2.0})

    def test_a_trade_with_no_wage_is_skipped(self):
        self.assertEqual(self._cuts(100.0, 0.0, {"ghost": 3.0, "labourer": 5.0}), {"labourer": 5.0})


class PolicyDefaults(unittest.TestCase):
    def test_nothing_that_deletes_your_work_is_on_by_default_for_a_player(self):
        self.assertIs(default_policy(True)["auto_shed"], False)
        self.assertIs(default_policy(False)["auto_shed"], True)

    def test_a_player_plays_by_hand_and_the_optimizer_automates(self):
        player, optimizer = default_policy(True), default_policy(False)
        for name in ("auto_hire", "auto_buy_people", "auto_train", "auto_open"):
            self.assertIs(player[name], False, name)
            self.assertIs(optimizer[name], True, name)


class SwitchThatCannotAct(unittest.TestCase):
    """`policy` says which switches are on but cannot act today."""

    def _policy_reply(self, capital, frozen_until=0, year=100):
        household = Game(reserve_craftsmen=0, reserve_scholars=0)
        game = Game(policy={"auto_hire": True, "auto_open": True}, capital=capital, year=year,
                               credit_frozen_until=frozen_until, workforce=household, view=workforce_stand_in.view_of(household, exclusions=set, keep_staffed=set), state=Game(household=household,
                                                                                     projects=Game(excluded=set())))
        return _cmd_policy(game, {}, {"cmd": "policy"}, None)

    def test_in_arrears_hiring_and_opening_say_they_cannot_act(self):
        stopped = self._policy_reply(-500.0)["switched_on_but_cannot_act_right_now"]
        self.assertGreaterEqual(set(stopped), {"auto_hire", "auto_open"})

    def test_a_solvent_household_has_nothing_stopped(self):
        self.assertNotIn("switched_on_but_cannot_act_right_now", self._policy_reply(50000.0))

    def test_a_credit_freeze_is_said(self):
        self.assertIn("credit", self._policy_reply(50000.0, frozen_until=130)["switched_on_but_cannot_act_right_now"])


class StallDiagnosis(unittest.TestCase):
    """A run that has effectively stopped says so and what would restart it; a solvent one is not told it is stuck."""

    def _host(self, capital=-900.0, insolvent_years=12, revenue=0.0, standing_pay=0.0, would_earn=500.0, hours=2000.0):
        module = finance_host.build(seat=FinanceSeat(insolvent_years=insolvent_years), acting_balance=capital, revenue_capacity=revenue,
                                    upkeep=100.0, hours_for_sale=hours, best_wage_trade="scribe",
                                    work_for_wages_dry_run=lambda trade, hours: (would_earn, None),
                                    standing_job_pay=lambda trade: standing_pay)
        module.debt_interest_rate = lambda: 0.05
        module.living_cost = lambda revenue=0, upkeep=0, capital=None: 200.0
        return module

    def test_a_long_arrears_run_that_loses_money_says_it_is_stuck_and_what_would_change_it(self):
        diagnosis = self._host().stall_diagnosis()
        self.assertTrue(diagnosis)
        self.assertTrue(any(reason.startswith("work as a ") for reason in diagnosis["what_would_change_it"]))

    def test_wage_work_is_advised_only_when_it_pays_more_than_the_standing_job(self):
        better = self._host(standing_pay=100.0, would_earn=500.0).stall_diagnosis()
        worse = self._host(standing_pay=900.0, would_earn=500.0).stall_diagnosis()
        self.assertTrue(any(reason.startswith("work as a ") for reason in better["what_would_change_it"]))
        self.assertFalse(any(reason.startswith("work as a ") for reason in worse["what_would_change_it"]))

    def test_a_solvent_run_is_not_told_it_is_stuck(self):
        self.assertIsNone(self._host(capital=500.0).stall_diagnosis())

    def test_a_short_spell_in_arrears_is_not_a_stall(self):
        self.assertIsNone(self._host(insolvent_years=3).stall_diagnosis())

    def test_a_run_that_earns_more_than_it_costs_is_not_stuck(self):
        self.assertIsNone(self._host(revenue=1.0e6).stall_diagnosis())


class StaffFractions(unittest.TestCase):
    def _staff(self, scholars, artisans, employees=None):
        return Game(view=lambda name: (lambda: {"scholars": scholars, "artisans": artisans, "employees": employees or {}}))

    def test_a_fractional_staff_count_comes_with_an_explanation(self):
        self.assertTrue(_staff_fraction_note(self._staff(1.32, 3.0)))
        self.assertTrue(_staff_fraction_note(self._staff(2.0, 3.0, {"smith": 0.4})))

    def test_a_whole_number_staff_carries_no_footnote(self):
        self.assertIsNone(_staff_fraction_note(self._staff(2.0, 3.0, {"smith": 4.0})))


class ReopeningIsNeverFree(unittest.TestCase):
    """Shutting a work down and bringing it back costs at least some years of its upkeep, however cheap it was to build."""

    def _host(self, upkeep, build_cost, venture=False):
        return ventures_host.build(
            tree_nodes={"w": {"up": upkeep}}, is_venture=lambda node_id: venture, project_cost=lambda node_id: build_cost,
            staff_closure_age=lambda node_id: None)

    def test_the_floor_is_the_declared_years_of_upkeep(self):
        self.assertGreaterEqual(REGISTRY["RESTORE_COST_MIN_UPKEEP_YEARS"]["value"], 1.0)
        self.assertEqual(self._host(upkeep=20.0, build_cost=1.0).reopen_fee("w"),
                         20.0 * REGISTRY["RESTORE_COST_MIN_UPKEEP_YEARS"]["value"])

    def test_a_costly_build_costs_its_share_to_restore(self):
        self.assertEqual(self._host(upkeep=1.0, build_cost=1000.0).reopen_fee("w"),
                         1000.0 * REGISTRY["RESTORE_COST_SHARE_OF_BUILD"]["value"])

    def test_a_round_trip_costs_at_least_a_year_of_upkeep(self):
        self.assertGreaterEqual(self._host(upkeep=20.0, build_cost=0.0).reopen_fee("w"), 20.0)


class HazardValuesLandGradually(unittest.TestCase):
    """A hazard's `values` delta lands evenly across its own window and is logged while it runs (Christianisation)."""

    START, END = 995, 1100

    def _host(self, weights):
        game = Game(value_weights=dict(weights))
        module = hazards_host.build(answers={ShiftValueWeight: polity_host.shifting(game.value_weights)})
        return game, module

    def _run(self, hazard, weights, years):
        game, module = self._host(weights)
        log = []
        for year in years:
            before = len(module_harness.sent(module))
            module.values_seats({"seat": hazard}, year, hazard["years"][0], hazard["years"][1])
            log += [(year, command) for command in module_harness.sent(module)[before:] if isinstance(command, RecordEvent)]
        return game, log

    def test_one_year_moves_a_fraction_of_the_total_not_the_whole_amount(self):
        hazard = {"name": "Christianisation", "years": [self.START, self.END], "values": {"w_religious_rigidity": 1.06}}
        host, _log = self._run(hazard, {"w_religious_rigidity": 0.0}, [self.START])
        self.assertGreater(host.value_weights["w_religious_rigidity"], 0.0)
        self.assertLess(host.value_weights["w_religious_rigidity"], 0.5 * 1.06)

    def test_the_full_delta_has_landed_by_the_last_year(self):
        hazard = {"name": "Christianisation", "years": [self.START, self.END], "values": {"w_religious_rigidity": 1.06}}
        host, _log = self._run(hazard, {"w_religious_rigidity": 0.0}, range(self.START, self.END + 1))
        self.assertAlmostEqual(host.value_weights["w_religious_rigidity"], 1.06, places=6)

    def test_it_is_logged_at_the_start_every_ten_years_and_at_the_end_not_only_once(self):
        hazard = {"name": "Christianisation", "years": [self.START, self.END], "values": {"w_religious_rigidity": 1.06}}
        _host, log = self._run(hazard, {"w_religious_rigidity": 0.0}, range(self.START, self.END + 1))
        years = [year for year, _command in log]
        self.assertIn(self.START, years)
        self.assertIn(self.END, years)
        self.assertTrue(any(self.START < year < self.END for year in years))
        self.assertGreaterEqual(len(years), 3)
        self.assertTrue(all(command.kind == "hazard_values_shift" for _year, command in log))

    def test_a_hazard_that_carries_only_a_values_delta_still_moves_the_society(self):
        hazard = {"name": "values-only test hazard", "values": {"w_novelty": -0.2}, "years": [900, 909]}
        host, _log = self._run(hazard, {"w_novelty": 0.5}, range(900, 910))
        self.assertAlmostEqual(host.value_weights["w_novelty"], 0.3, places=6)

    def test_a_field_the_society_does_not_have_is_ignored(self):
        hazard = {"name": "x", "values": {"w_unknown": 1.0}, "years": [900, 909]}
        host, log = self._run(hazard, {"w_novelty": 0.5}, range(900, 910))
        self.assertEqual(host.value_weights, {"w_novelty": 0.5})
        self.assertEqual(log, [])


class ChristianisationIsData(unittest.TestCase):
    """Norse Christianisation carries a values delta in the civilisation file, is listed ahead before it starts, and sacks nothing."""

    def setUp(self):
        self.civ = engine_data.load_civ("norse_900ad")
        self.hazard = next(hazard for hazard in self.civ["hazards"] if hazard["name"].startswith("Christianisation"))

    def test_it_carries_a_values_delta_not_just_a_note(self):
        self.assertTrue(self.hazard.get("values"))

    def test_it_is_listed_among_the_hazards_ahead_at_the_start_of_the_game(self):
        ahead = [(hazard["name"], in_progress) for hazard, _start, _end, in_progress in hazards_not_yet_past(self.civ, self.civ["year"])]
        self.assertIn((self.hazard["name"], False), ahead)

    def test_the_note_says_what_it_does_to_the_society(self):
        self.assertIn("values", self.hazard.get("note", "").lower())

    def test_a_values_shift_is_not_a_sacking(self):
        self.assertNotIn("sack_chance", self.hazard)


if __name__ == "__main__":
    unittest.main()
