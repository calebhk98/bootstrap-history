"""The commands the workforce module applies, on a module built over plain household figures, and the rules they call."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim.tests import module_harness
from sim.workforce import rules as workforce_rules
from sim.workforce.api import LoseStaff, NoteTradeSpread, PressLabour, SetEmployed, TakeWageFallback
from sim.workforce.api import AutoBuyPeople, AutoManumit, CloseHoursYear, FadeMarketPressure, NoteBuyRefusal, SettleLivingCost
from sim.reporting.api import RecordEvent
from sim.workforce.constants import AUTO_MANUMIT_ANNUAL_CHANCE, MARKET_PRESSURE_ANNUAL_FADE, MARKET_PRESSURE_DECAY, WAGE_FALLBACK_LIVING_COST_YEARS, WAGE_FALLBACK_MAX_HOURS, WAGE_FALLBACK_MIN_HOURS
from sim.workforce.module import Workforce
from sim.workforce.state import WorkforceSeat


class SurvivingPeople(unittest.TestCase):
    def test_everyone_survives_a_share_of_one_and_no_one_a_share_of_zero(self):
        self.assertEqual(workforce_rules.surviving_people(random.Random(1), 40.0, 1.0), 40.0)
        self.assertEqual(workforce_rules.surviving_people(random.Random(1), 40.0, 0.0), 0.0)

    def test_the_headcount_is_whole_and_one_draw_is_made_per_person(self):
        dice = random.Random(3)
        kept = workforce_rules.surviving_people(dice, 12.4, 0.5)
        self.assertEqual(kept, float(int(kept)))
        mirror = random.Random(3)
        for _ in range(12):
            mirror.random()
        self.assertEqual(dice.random(), mirror.random())


class Commands(unittest.TestCase):
    def test_a_loss_multiplies_the_deputies_by_their_share_and_answers_the_people_on_the_books_either_side(self):
        household = SimpleNamespace(directors_extra=4.0, scholars=2.0, artisans=3.0, employees={"smith": 5.0})
        workforce = module_harness.build(Workforce, seat=household, views={"game_random": random.Random(3)})
        workforce.labour = SimpleNamespace(staff_snapshot=lambda: {}, log_staff_reduction=lambda cause, before: None)
        answer = workforce.lose_staff(LoseStaff("a sack", 1.0, 0.5))
        self.assertEqual((household.directors_extra, answer), (2.0, {"people_before": 10.0, "people_after": 10.0}))

    def test_a_loss_logs_the_cause_and_the_headcount_before_it(self):
        asked = []
        household = SimpleNamespace(directors_extra=0.0, scholars=0.0, artisans=0.0, employees={"smith": 3.0})
        workforce = module_harness.build(Workforce, seat=household, views={"game_random": random.Random(3)})
        workforce.labour = SimpleNamespace(staff_snapshot=lambda: {"smith": 3.0}, log_staff_reduction=lambda cause, before: asked.append((cause, before)))
        workforce.lose_staff(LoseStaff("a sack", 1.0, 1.0))
        self.assertEqual(asked, [("a sack", {"smith": 3.0})])

    def test_a_trade_spread_notes_the_year_first_taught_and_that_it_became_endemic(self):
        household = SimpleNamespace(trade_introduced_year={}, trades_endemic=set())
        workforce = module_harness.build(Workforce, seat=household, views={"acting_balance": lambda: household.capital})
        workforce.note_trade_spread(NoteTradeSpread("smith", introduced_year=120))
        self.assertEqual((household.trade_introduced_year, household.trades_endemic), ({"smith": 120}, set()))
        workforce.note_trade_spread(NoteTradeSpread("smith", endemic=True))
        self.assertEqual((household.trade_introduced_year, household.trades_endemic), ({"smith": 120}, {"smith"}))

    def test_setting_the_staff_of_a_trade_resyncs_the_hour_pools_after(self):
        calls = []
        workforce = module_harness.build(Workforce)
        workforce.labour = SimpleNamespace(set_employed=lambda trade, headcount: calls.append(("set", trade, headcount)),
                                           resync_pools=lambda: calls.append(("resync",)))
        workforce.set_employed(SetEmployed("smith", 3.0))
        self.assertEqual(calls, [("set", "smith", 3.0), ("resync",)])

    def test_pressing_labour_presses_the_markets_trade(self):
        pressed = []
        workforce = module_harness.build(Workforce)
        workforce.labour = SimpleNamespace(market=SimpleNamespace(press=lambda trade, hours: pressed.append((trade, hours))))
        workforce.press_labour(PressLabour("smith", 500.0))
        self.assertEqual(pressed, [("smith", 500.0)])


class WageFallback(unittest.TestCase):
    """A household with no work and thin means sells idle hours for wages, unless it is played by hand."""

    def fallback(self, remaining, manual=False, capital=0.0, active=(), pays=(10.0, 4.0), held=None):
        sold = []
        household = SimpleNamespace(capital=capital)
        workforce = module_harness.build(Workforce, views={
            "acting_balance": lambda: household.capital, "automation": {"manual": manual}, "living_cost": lambda *args: 100.0,
            "active_projects": dict.fromkeys(active), "held_trade": lambda: held})
        workforce.labour = SimpleNamespace(
            effective_scholars=lambda: 2.0, work_for_wages=lambda trade, hours: sold.append((trade, hours)) or (1.0, None),
            wage_for_hours=lambda trade, hours: pays[0] if trade == "scholar" else pays[1])
        return workforce.take_wage_fallback(TakeWageFallback(remaining)), sold

    def test_idle_hours_are_sold_up_to_the_ceiling_and_leave_the_year_less_unspent(self):
        left, sold = self.fallback(WAGE_FALLBACK_MAX_HOURS + 500.0)
        self.assertEqual(sold, [("scholar", WAGE_FALLBACK_MAX_HOURS)])
        self.assertEqual(left, 500.0)

    def test_a_seat_played_by_hand_and_a_token_amount_of_hours_sell_nothing(self):
        self.assertEqual(self.fallback(WAGE_FALLBACK_MAX_HOURS, manual=True), (WAGE_FALLBACK_MAX_HOURS, []))
        self.assertEqual(self.fallback(WAGE_FALLBACK_MIN_HOURS), (WAGE_FALLBACK_MIN_HOURS, []))

    def test_a_household_with_cash_and_projects_in_hand_sells_nothing(self):
        capital = 100.0 * WAGE_FALLBACK_LIVING_COST_YEARS + 1.0
        self.assertEqual(self.fallback(500.0, capital=capital, active=("a",)), (500.0, []))

    def test_hours_are_not_moved_from_a_standing_job_that_pays_better(self):
        self.assertEqual(self.fallback(500.0, pays=(3.0, 3.0), held="artisan"), (500.0, []))


class HoursYear(unittest.TestCase):
    def test_the_year_ends_with_its_breakdown_kept_the_ledger_closed_and_the_tallies_reset(self):
        closed = []
        household = SimpleNamespace(log=[], wage_hours_this_year=120.04, teaching_hours_this_year=30.0, relocation_hours_this_year=None,
                                    supervision_hours_this_year=7.0, contract_hours={"smith": 40.0}, hours_this_year=None)
        workforce = module_harness.build(Workforce, seat=household, views={"acting_balance": lambda: household.capital})
        workforce.labour = SimpleNamespace(director_pool=lambda: 2000.04, close_wage_year=lambda: closed.append(dict(
            kept=household.hours_this_year, wage=household.wage_hours_this_year)))
        workforce.close_hours_year(CloseHoursYear(pool=1500.0, remaining=-3.0, remaining_after_projects=400.0, hours_effective_total=800.04))
        self.assertEqual(household.hours_this_year, {
            "available": 2000.0, "wage_work": 120.0, "teaching": 30.0, "moving": 0.0, "supervising": 7.0,
            "offered_to_projects": 1100.0, "effective_on_projects": 800.0, "unused": 0.0})
        self.assertEqual([entry["kept"] is household.hours_this_year for entry in closed], [True])   # kept before the ledger closed
        self.assertEqual((household.contract_hours, household.teaching_hours_this_year, household.relocation_hours_this_year,
                          household.supervision_hours_this_year), ({}, 0.0, 0.0, 0.0))


class LivingCost(unittest.TestCase):
    def test_settling_the_living_cost_uses_up_the_advance_and_adds_the_bill_to_what_was_paid(self):
        seat = WorkforceSeat(wages_prepaid=20.0, living_cost_paid=100.0)
        module_harness.build(Workforce, seat=seat, views={}).settle_living_cost(SettleLivingCost(50.0))
        self.assertEqual((seat.wages_prepaid, seat.living_cost_paid), (0.0, 150.0))


class StandingPolicyRules(unittest.TestCase):
    def buy(self, capital=1000.0, lacking=3.0):
        return workforce_rules.people_to_buy(capital, 10.0, lacking, 20.0, 5.0)

    def test_nobody_is_bought_under_the_capital_floor_or_when_no_hands_are_lacking(self):
        self.assertEqual((self.buy(capital=200.0), self.buy(lacking=0.0), self.buy(lacking=1e-12)), (0, 0, 0))

    def test_the_whole_people_the_concerns_lack_are_bought_however_many_that_is(self):
        self.assertEqual((self.buy(lacking=0.2), self.buy(lacking=2.5), self.buy(capital=100000.0, lacking=300.0)), (1, 3, 300))

    def test_no_more_are_bought_than_the_reserve_per_person_allows(self):
        self.assertEqual((self.buy(capital=210.0, lacking=30.0), self.buy(capital=1000.0, lacking=30.0)), (4, 20))

    def test_a_share_of_the_slaves_is_freed_and_never_fewer_than_one(self):
        self.assertEqual((workforce_rules.people_to_free(40, 4), workforce_rules.people_to_free(2, 4)), (10, 1))

    def test_pressure_keeps_a_share_loses_a_flat_amount_and_stops_at_zero(self):
        self.assertEqual((workforce_rules.market_pressure_after_a_year(100.0, 0.5, 2.0), workforce_rules.market_pressure_after_a_year(1.0, 0.5, 2.0)), (48.0, 0.0))


class StandingPolicies(unittest.TestCase):
    def build(self, policy, slaves=8.0, capital=1000.0, dice=None, mechanics=("hosts",), manual=False, lacking=6.0):
        calls = []
        household = SimpleNamespace(capital=capital)
        workforce = module_harness.build(Workforce, seat=WorkforceSeat(), views={
            "founder": lambda: {"policy": policy}, "automation": lambda: {"manual": manual}, "acting_balance": lambda: household.capital,
            "game_random": lambda: dice, "running_mechanics": lambda name: list(mechanics),
            "staffing_closed_hand_shortfall": lambda: (0.0, lacking)})
        workforce.staff = lambda: {"artisans": 3.0, "slaves": slaves}
        workforce.labour = SimpleNamespace(SLAVE_BASE_PRICE=10.0, buy_slaves=lambda count: calls.append(("buy", count)) or count,
                                           manumit=lambda count: calls.append(("free", count)) or count)
        return workforce, calls

    def test_the_policy_buys_people_when_on_and_records_it(self):
        workforce, calls = self.build({"auto_buy_people": True})
        workforce.auto_buy_people(AutoBuyPeople())
        self.assertEqual(calls, [("buy", 6)])
        self.assertEqual([command.kind for command in module_harness.sent(workforce) if isinstance(command, RecordEvent)], ["people_bought"])

    def test_the_policy_buys_nobody_when_off_or_when_no_mechanic_hosts_bought_people(self):
        for policy, mechanics in (({"auto_buy_people": False}, ("hosts",)), ({}, ("hosts",)), ({"auto_buy_people": True}, ())):
            workforce, calls = self.build(policy, mechanics=mechanics)
            workforce.auto_buy_people(AutoBuyPeople())
            self.assertEqual(calls, [], policy)

    def test_the_policy_frees_a_share_on_a_hit_and_draws_once(self):
        dice = random.Random(5)
        mirror = random.Random(5)
        workforce, calls = self.build({"auto_manumit": True}, dice=dice)
        workforce.auto_manumit(AutoManumit())
        self.assertEqual(calls, [("free", 2)] if mirror.random() < AUTO_MANUMIT_ANNUAL_CHANCE else [])
        self.assertEqual(dice.random(), mirror.random())

    def test_the_policy_draws_nothing_when_off_or_when_there_are_no_slaves(self):
        for policy, slaves in (({"auto_manumit": False}, 8.0), ({"auto_manumit": True}, 0.0)):
            dice = random.Random(5)
            workforce, calls = self.build(policy, slaves=slaves, dice=dice)
            workforce.auto_manumit(AutoManumit())
            self.assertEqual((calls, dice.random()), ([], random.Random(5).random()))

    def test_the_market_pressure_fades_on_the_acting_seat(self):
        seat = WorkforceSeat(market_pressure=100.0)
        workforce = module_harness.build(Workforce, seat=seat)
        workforce.fade_market_pressure(FadeMarketPressure())
        self.assertAlmostEqual(seat.market_pressure, 100.0 * MARKET_PRESSURE_DECAY - MARKET_PRESSURE_ANNUAL_FADE)

    def test_a_refusal_to_buy_people_is_kept_for_the_acting_seat_until_it_is_cleared(self):
        workforce = module_harness.build(Workforce, seat=WorkforceSeat())
        workforce.clock.acting_seat = "founder"
        workforce.note_buy_refusal(NoteBuyRefusal("cannot afford 3 slaves"))
        self.assertEqual(workforce.last_buy_refusal(), "cannot afford 3 slaves")
        workforce.clock.acting_seat = "second"
        self.assertIsNone(workforce.last_buy_refusal())
        workforce.clock.acting_seat = "founder"
        workforce.note_buy_refusal(NoteBuyRefusal(None))
        self.assertIsNone(workforce.last_buy_refusal())


if __name__ == "__main__":
    unittest.main()
