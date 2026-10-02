"""The state spends what it takes in and finances a deficit by a stated order: a balanced budget leaves its
share of the coin steady, and a deficit paid by printing raises prices through the ordinary markets.

One England economy is opened once (the opening spins it up); each scenario resumes a copy of it from its
saved record, which is also the save round trip."""
import dataclasses
import math
import random
import unittest

from sim import simulator
from sim.economy.economy import Economy
from sim.economy.protocols import YearInputs
from sim.economy.record import EconomyRecord
from sim.economy.state_policy import StatePolicy

OPENED = {}


def opened():
    if not OPENED:
        tree, _prices, nodes, _wages, _goods = simulator.load()
        goal = tree["meta"]["goal_node"]
        _levels, order, _blocked = simulator.load_strategy("recommended", nodes, goal)
        game = simulator.Sim(nodes, order, random.Random(1), events=True, manual=False,
                             civ=simulator.load_civ("england_1300"), cfg={"agent_economy": True})
        OPENED["economy"] = game.economy.agent.economy()
    return OPENED["economy"]


def resumed(policy=None, fiat=False) -> Economy:
    base = opened()
    setup = dataclasses.replace(base.setup, state_policy=policy or base.setup.state_policy)
    record = EconomyRecord.from_record(base.record.to_record())
    if fiat:
        record.currency = dataclasses.replace(record.currency, regime="fiat", backing_good=None, backing_per_unit=0.0)
    return Economy(setup, record)


def run(economy: Economy, years: int):
    """Year by year: (state's share of the coin, price level, mean expected inflation, money supply)."""
    rows = []
    money = economy.setup.currency_id
    for year in range(years):
        economy.step(YearInputs(year=year, population_by_tile={}, working_age_share=0.6,
                                yield_factor_by_producer={}, engine_orders={}))
        record = economy.record
        supply = record.book.money_supply(money)
        people = sum(cohort.people for cohort in record.cohorts.values())
        expected = sum(cohort.expected_inflation * cohort.people for cohort in record.cohorts.values()) / people
        rows.append((record.book.balance(economy.setup.state_agent, money) / supply,
                     record.memory.price_levels.get(money, 1.0), expected, supply))
    return rows


class StateBudgetTests(unittest.TestCase):
    def test_a_balanced_budget_leaves_the_states_share_of_the_coin_steady(self):
        economy = resumed()
        before = economy.record.book.balance(economy.setup.state_agent, economy.setup.currency_id) \
            / economy.record.book.money_supply(economy.setup.currency_id)
        rows = run(economy, 8)
        self.assertLess(rows[-1][0], before * 1.25)
        self.assertGreater(rows[-1][0], before * 0.5)
        self.assertTrue(economy.record.book.check_conservation(1e-9).ok)

    def test_the_state_bids_for_hours_and_goods_through_the_markets(self):
        economy = resumed()
        run(economy, 2)
        budget = economy.record.state_budget
        self.assertGreater(budget.revenue, 0.0)
        self.assertGreater(budget.wage_budget, 0.0)
        self.assertGreater(budget.goods_budget, 0.0)

    def test_printing_to_cover_a_deficit_raises_prices_and_expectations_and_can_run_away(self):
        money = opened().setup.currency_id
        supply = opened().record.book.money_supply(money)
        control = run(resumed(fiat=True), 8)
        policy = StatePolicy(real_spending_target=4.0 * supply, financing_order=("issue",))
        printing = resumed(policy, fiat=True)
        rows = run(printing, 8)
        self.assertGreater(rows[-1][1], 3.0 * control[-1][1])
        self.assertGreater(rows[-1][2], control[-1][2] + 0.05)
        self.assertGreater(rows[-1][3], 3.0 * control[-1][3])
        # runaway: prices keep rising fast to the end instead of settling (a deficit that grows with prices)
        late = math.log(rows[-1][1] / rows[-4][1]) / 3.0
        self.assertGreater(late, math.log(1.3))
        self.assertGreater(rows[-1][1], 20.0 * rows[0][1])
        self.assertTrue(printing.record.book.check_conservation(1e-9).ok)
        self.assertGreater(printing.record.state_budget.issued_total, 0.0)

    def test_a_struck_coin_is_debased_to_pay_the_deficit_and_money_is_conserved(self):
        economy = opened()
        supply = economy.record.book.money_supply(economy.setup.currency_id)
        policy = StatePolicy(real_spending_target=0.3 * supply, financing_order=("debase",))
        debasing = resumed(policy)
        metal_before = debasing.record.currency.backing_per_unit
        run(debasing, 3)
        self.assertLess(debasing.record.currency.backing_per_unit, metal_before)
        self.assertTrue(debasing.record.book.check_conservation(1e-9).ok)

    def test_borrowing_comes_before_printing_and_the_state_owes_what_it_borrowed(self):
        economy = opened()
        supply = economy.record.book.money_supply(economy.setup.currency_id)
        policy = StatePolicy(real_spending_target=0.1 * supply)
        borrowing = resumed(policy)
        run(borrowing, 3)
        owed = [loan for loan in borrowing.record.loans if loan.borrower == borrowing.setup.state_agent]
        self.assertTrue(owed)
        self.assertTrue(borrowing.record.book.check_conservation(1e-9).ok)

    def test_the_budget_round_trips_through_the_save(self):
        economy = resumed()
        run(economy, 2)
        again = EconomyRecord.from_record(economy.record.to_record())
        self.assertEqual(again.state_budget, economy.record.state_budget)


if __name__ == "__main__":
    unittest.main()
