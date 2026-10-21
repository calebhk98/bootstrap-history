"""Baseline validations (CLAUDE.md 4.2) of the state's budget on an opened England economy: a balanced budget leaves its
share of the coin steady, and a deficit paid by printing raises prices through the ordinary markets, runs away, and
raises them further the more is printed. They read the opened economy's behaviour over years, so a failure here
names Complaint 526 (the opening's money supply is still draining on the suite's short spin-up) before the rule.
The rules (the financing order, debasing, bids for hours and goods, conservation, the record round trip) are in
test_economy_agent_state and test_economy_state_budget.

One England economy is opened once (the opening spins it up); each scenario resumes a copy of it from its
saved record."""
import dataclasses
import math
import os
import random
import unittest
from unittest import mock

from sim import simulator
from sim.economy.economy import Economy
from sim.economy.protocols import YearInputs
from sim.economy.record import EconomyRecord
from sim.economy.state_policy import StatePolicy

NOTE = "baseline validation (4.2), Complaint 526: the opened England economy's behaviour over years"
OPENED = {}


def opened(full_length=False):
    """The opened England economy: on the suite's short spin-up, or on the declared-length one a player's game opens."""
    if full_length not in OPENED:
        tree, _prices, nodes, _wages, _goods = simulator.load()
        goal = tree["meta"]["goal_node"]
        _levels, order, _blocked = simulator.load_strategy("recommended", nodes, goal)
        with mock.patch.dict(os.environ):
            if full_length:
                os.environ.pop("ROME_SPIN_UP_YEARS", None)
            game = simulator.Sim(nodes, order, random.Random(1), events=True, manual=False,
                                 civ=simulator.load_civ("england_1300"))
        OPENED[full_length] = game.economy.agent.economy()
    return OPENED[full_length]


def resumed(policy=None, fiat=False, full_length=False) -> Economy:
    base = opened(full_length)
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
                     record.memory.basket_price_levels.get(money, 1.0), expected, supply))
    return rows


class StateBudgetTests(unittest.TestCase):
    def test_baseline_validation_a_balanced_budget_leaves_the_states_share_of_the_coin_steady(self):
        # on the declared-length opening: the suite's short spin-up leaves the money supply still draining and the
        # state's holdings still rising against it (Complaint 526), so a share measured there moves for the opening's sake
        economy = resumed(full_length=True)
        before = economy.record.book.balance(economy.setup.state_agent, economy.setup.currency_id) \
            / economy.record.book.money_supply(economy.setup.currency_id)
        rows = run(economy, 8)
        self.assertLess(rows[-1][0], before * 1.25, msg=NOTE)
        self.assertGreater(rows[-1][0], before * 0.5, msg=NOTE)
        self.assertTrue(economy.record.book.check_conservation(1e-9).ok, msg=NOTE)

    def test_baseline_validation_printing_to_cover_a_deficit_raises_prices_and_expectations_and_can_run_away(self):
        money = opened().setup.currency_id
        supply = opened().record.book.money_supply(money)
        control = run(resumed(fiat=True), 8)
        policy = StatePolicy(real_spending_target=4.0 * supply, financing_order=("issue",))
        printing = resumed(policy, fiat=True)
        rows = run(printing, 8)
        self.assertGreater(rows[-1][1], 3.0 * control[-1][1], msg=NOTE)
        self.assertGreater(rows[-1][2], control[-1][2] + 0.05, msg=NOTE)
        self.assertGreater(rows[-1][3], 3.0 * control[-1][3], msg=NOTE)
        # runaway: prices keep rising fast to the end instead of settling (a deficit that grows with prices)
        yearly = math.log(rows[-1][1] / rows[0][1]) / (len(rows) - 1)
        self.assertGreater(yearly, math.log(1.3), msg=NOTE)
        self.assertGreater(rows[-1][1], 20.0 * rows[0][1], msg=NOTE)
        self.assertTrue(printing.record.book.check_conservation(1e-9).ok, msg=NOTE)
        self.assertGreater(printing.record.state_budget.issued_total, 0.0, msg=NOTE)

    def test_baseline_validation_printing_more_raises_the_price_level_more_instead_of_saturating(self):
        # a bigger real programme must not stop at a few times the control however much is printed
        supply = opened(True).record.book.money_supply(opened(True).setup.currency_id)
        control = run(resumed(fiat=True, full_length=True), 4)[-1][1]
        levels = [run(resumed(StatePolicy(real_spending_target=times * supply, financing_order=("issue",)),
                              fiat=True, full_length=True), 4)[-1][1] for times in (4.0, 16.0)]
        self.assertGreater(levels[0], 3.0 * control, msg=NOTE)
        self.assertGreater(levels[1], 1.25 * levels[0], msg=NOTE)


if __name__ == "__main__":
    unittest.main()
