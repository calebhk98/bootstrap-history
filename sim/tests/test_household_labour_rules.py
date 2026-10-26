"""The household's labour: the standing job and the trade it sells in, selling hours on request, the two channels
that supply a trade, apprentices joining the staff, when a lost trade is taught again, and the hire command with no
founder left. Each rule is called on a stand-in carrying only what it reads."""

QUICK_TOPIC = True

import types
import unittest

from sim.engine import data
from sim.engine.core_step_phases import StepPhasesMixin
from sim.engine.economy_production import ProductionMixin
from sim.engine.reteach_rules import PROJECT_IN_HAND_SCORE, past_cooldown, teaching_budget, trade_is_gone
from sim.labour.labour_job import StandingJobMixin
from sim.labour.labour_training import TrainingMixin
from sim.labour.labour_wages import WagesMixin
from sim.refusal import cause_of
from sim.ui.proto.dispatch_labour import _cmd_hire
from sim.tests import event_stand_in


class HeldTrade(ProductionMixin):
    def __init__(self, held):
        self.nodes = {node_id: {"sch": scholars} for node_id, scholars in held.items()}
        self._held = set(held)

    def _practice_set(self):
        return self._held


class HeldTradeRule(unittest.TestCase):

    def test_a_founder_who_holds_a_skill_asking_for_scholars_sells_hours_as_a_scholar(self):
        self.assertEqual(HeldTrade({"a": 0, "b": 2}).held_trade(), "scholar")

    def test_a_founder_who_holds_only_hand_skills_sells_hours_as_an_artisan(self):
        self.assertEqual(HeldTrade({"a": 0}).held_trade(), "artisan")

    def test_a_founder_who_holds_no_skill_sells_in_no_trade(self):
        self.assertIsNone(HeldTrade({}).held_trade())

    def test_an_engineer_is_a_scholar_and_a_smith_a_craftsman(self):
        self.assertEqual(data.trade_family("engineer"), "scholar")
        self.assertEqual(data.trade_family("smith"), "craft")


class Job(StandingJobMixin):
    def __init__(self, alive=True, pool=2000.0, committed=500.0, rate=2.0):
        self._world = types.SimpleNamespace(state=types.SimpleNamespace(founder=types.SimpleNamespace(founder_alive=alive)))
        self.pool, self.committed, self.rate = pool, committed, rate

    def director_pool(self):
        return self.pool

    def director_hours_committed(self):
        return self.committed

    def wage_for_hours(self, trade, hours):
        return hours * self.rate


class StandingJob(unittest.TestCase):

    def test_the_hours_not_spoken_for_are_sold_at_the_trades_wage(self):
        job = Job()
        self.assertEqual(job.hours_for_sale(), 1500.0)
        self.assertEqual(job.standing_job_pay("artisan"), 3000.0)

    def test_a_dead_founder_sells_no_hours_and_earns_nothing(self):
        job = Job(alive=False)
        self.assertEqual(job.hours_for_sale(), 0.0)
        self.assertEqual(job.standing_job_pay("artisan"), 0.0)

    def test_no_trade_no_pay(self):
        self.assertEqual(Job().standing_job_pay(None), 0.0)

    def test_hours_sold_on_request_leave_the_standing_job(self):
        job = Job()
        before = job.standing_job_pay("artisan")
        job.committed += 500.0
        self.assertAlmostEqual(before - job.standing_job_pay("artisan"), 500.0 * job.rate)


class Seller(WagesMixin):
    """The part of Labour that sells the founder's own hours."""

    def __init__(self, committed=0.0, pool=2000.0):
        household = types.SimpleNamespace(wage_hours_this_year=0.0, wages_earned=0.0, wage_income_this_year=0.0, reputation=0.0)
        self.household = household
        self.received = []
        self.logged = []
        self._world = types.SimpleNamespace(
            state=types.SimpleNamespace(founder=types.SimpleNamespace(founder_alive=True), household=household),
            wages={"scribe": 1}, EDGE_EMPLOYERS="employers", revenue=lambda: 1000.0, active_hours_still_wanted=lambda: 0.0,
            money_text=lambda amount, grouped=False: "%d" % amount,
            receive_from_edge=lambda edge, pay, text: self.received.append(pay))
        self.pool, self.committed = pool, committed

    def trade_available(self, trade):
        return True

    def director_pool(self):
        return self.pool

    def director_hours_committed(self):
        return self.committed + self.household.wage_hours_this_year

    def wage_for_hours(self, trade, hours):
        return 3.0 * hours

    def log_wage_work(self, trade, hours, pay):
        self.logged.append((trade, hours, pay))


class SellingHours(unittest.TestCase):

    def test_selling_hours_pays_the_trades_wage_and_counts_the_hours_against_the_year(self):
        seller = Seller()
        pay, warning = seller.work_for_wages("scribe", 500)
        self.assertEqual(pay, 1500.0)
        self.assertEqual(seller.received, [1500.0])
        self.assertEqual(seller.household.wage_hours_this_year, 500.0)
        self.assertEqual(seller.director_hours_committed(), 500.0)
        self.assertEqual(seller.logged, [("scribe", 500.0, 1500.0)])

    def test_more_hours_than_the_year_has_left_are_refused_and_pay_nothing(self):
        seller = Seller(committed=1800.0)
        pay, refusal = seller.work_for_wages("scribe", 500)
        self.assertEqual(pay, 0.0)
        self.assertEqual(seller.received, [])
        self.assertEqual(seller.household.wage_hours_this_year, 0.0)


class Channels(TrainingMixin):
    """The town's pool of a trade and the hours bought from an outside shop."""

    def __init__(self, supply=1000.0, contracted=0.0, productivity=1.0, employed=0.0):
        self.contract_hours = {"scribe": contracted}
        self._world = types.SimpleNamespace(
            state=types.SimpleNamespace(household=types.SimpleNamespace(contract_hours=self.contract_hours)),
            HOURS_PER_PERSON_YEAR=2000.0, trades_absent=set())
        self.supply, self.productivity, self._employed = supply, productivity, employed

    def market_supply(self, trade):
        return self.supply

    def labour_productivity(self, trade):
        return self.productivity

    def employed(self, trade):
        return self._employed


class SupplyChannels(unittest.TestCase):

    def test_commissioned_hours_add_to_what_can_be_called_on(self):
        self.assertEqual(Channels(contracted=0.0).hours_you_can_call_on("scribe"), 1000.0)
        self.assertEqual(Channels(contracted=400.0).hours_you_can_call_on("scribe"), 1400.0)

    def test_commissioning_does_not_change_how_many_of_the_trade_live_here(self):
        before = Channels(contracted=0.0).market_supply_split("scribe")
        after = Channels(contracted=400.0).market_supply_split("scribe")
        self.assertEqual(before, after)

    def test_productivity_multiplies_the_hours_called_on_and_not_the_supply(self):
        channels = Channels(contracted=400.0, productivity=1.5)
        self.assertEqual(channels.hours_you_can_call_on("scribe"), 1400.0 * 1.5)
        self.assertEqual(channels.market_supply("scribe"), 1000.0)

    def test_the_town_and_your_own_people_are_reported_apart_and_add_to_the_total(self):
        town, mine = Channels(supply=5000.0, employed=2.0).market_supply_split("scribe")
        self.assertEqual((town, mine), (1000.0, 4000.0))
        self.assertEqual(town + mine, 5000.0)

    def test_the_hours_bought_are_reported_by_trade(self):
        self.assertEqual(Channels(contracted=400.0).hours_reserved("scribe"), 400.0)


class Apprentices(StepPhasesMixin):
    send = event_stand_in.send

    def __init__(self, rows):
        self.joined = []
        self.state = types.SimpleNamespace(
            household=types.SimpleNamespace(training=rows, log=[]), scenario=types.SimpleNamespace(year=102))
        self.labour = types.SimpleNamespace(add_employed=lambda trade, count: self.joined.append((trade, count)),
                                            resync_pools=lambda: None)


class ApprenticesJoin(unittest.TestCase):

    def test_a_cohort_promised_for_a_year_is_on_the_books_in_that_year(self):
        game = Apprentices([[0.0, 102, "machinist", 2.0], [0.0, 103, "machinist", 1.0]])
        game._step_apprenticeships()
        self.assertEqual(game.joined, [("machinist", 2.0)])
        self.assertEqual(game.state.household.training, [[0.0, 103, "machinist", 1.0]])

    def test_a_joining_is_logged_with_its_kind(self):
        game = Apprentices([[0.0, 101, "machinist", 2.0]])
        game._step_apprenticeships()
        (_year, line), = game.state.household.log
        self.assertEqual(cause_of(line), "training_finished")

    def test_nobody_joins_before_their_year(self):
        game = Apprentices([[0.0, 105, "machinist", 2.0]])
        game._step_apprenticeships()
        self.assertEqual(game.joined, [])


class Reteaching(unittest.TestCase):

    def test_a_trade_with_no_market_and_nobody_in_training_is_gone(self):
        self.assertTrue(trade_is_gone(True, 0.0, 0.0))

    def test_a_trade_with_someone_in_training_or_on_the_market_is_not_gone(self):
        self.assertFalse(trade_is_gone(True, 0.0, 1.0))
        self.assertFalse(trade_is_gone(True, 500.0, 0.0))

    def test_a_trade_that_does_not_exist_is_gone_whatever_the_supply(self):
        self.assertTrue(trade_is_gone(False, 500.0, 2.0))

    def test_a_trade_taught_within_the_cooldown_is_not_taught_again_and_one_past_it_is(self):
        want = {"machinist": 1, "chemist": 1}
        self.assertEqual(past_cooldown(want, {"machinist": 99}, 100, 25), {"chemist": 1})
        self.assertEqual(past_cooldown(want, {"machinist": 75}, 100, 25), want)

    def test_a_trade_a_project_in_hand_waits_on_may_borrow_against_capital(self):
        self.assertGreater(teaching_budget(PROJECT_IN_HAND_SCORE, 100.0, 10000.0), 100.0)

    def test_a_speculative_trade_is_paid_only_from_half_the_spare_income(self):
        self.assertEqual(teaching_budget(1, 100.0, 10000.0), 50.0)
        self.assertEqual(teaching_budget(1, -50.0, 10000.0), 0.0)


class HireWithNoFounder(unittest.TestCase):

    def test_a_dead_founder_with_no_deputy_cannot_take_anyone_on(self):
        calls = []
        game = types.SimpleNamespace(founder_alive=False, deputies_carry_the_work=lambda: False,
                                     labour=types.SimpleNamespace(hire=lambda *args: calls.append(args)))
        reply = _cmd_hire(game, {}, {"cmd": "hire", "trade": "smith", "n": 1}, None)
        self.assertIs(reply["ok"], False)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
