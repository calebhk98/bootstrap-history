"""A producer that keeps losing leaves; capacity with no plant follows use; plant already built is sunk."""

QUICK_TOPIC = True

import unittest

from sim.economy import entry, producer_exit, producers, producers_close
from sim.economy.economy import Economy
from sim.economy.types import EDGE_PRODUCTION, GoodsMove, Loan, Transfer
from sim.tests.economy_fixture import HILLS, LABOURER, MINE, MINER, ORE, SMITH, quiet_year, run, small_setup
from sim.tests.test_economy_producers import FARM, SMELT, View, farm_view, farmer

YEARS = 12


def smelter_view(**changes):
    return View({"metal": 0.1, "silver": 0.1, "ore": 1.0, "stone": 1.0}, {"smith": 1.0}, **changes)


class IdleCapacityTests(unittest.TestCase):
    def test_plantless_capacity_whose_runs_would_not_pay_decays_toward_the_runs_worked(self):
        producer = farmer(capacity_runs=10.0)
        for _year in range(40):
            before = producer.capacity_runs
            producer = producers_close.close_year(producer, FARM, 100.0, 50.0, farm_view(1e-6), 4.0).producer
            self.assertLess(producer.capacity_runs, before + 1e-12)
            self.assertGreaterEqual(producer.capacity_runs, 4.0)
        self.assertAlmostEqual(producer.capacity_runs, 4.0, places=3)

    def test_plantless_capacity_whose_runs_would_pay_is_kept_while_it_waits(self):
        # idle for want of inputs or buyers, not of a margin: the hands are kept
        result = producers_close.close_year(farmer(capacity_runs=10.0), FARM, 100.0, 50.0, farm_view(2.0), 4.0)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0)

    def test_plantless_capacity_that_was_all_worked_is_unchanged(self):
        result = producers_close.close_year(farmer(capacity_runs=10.0), FARM, 100.0, 50.0, farm_view(2.0), 10.0)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0)

    def test_idle_sunk_plant_is_not_charged_in_the_loss_test(self):
        view = smelter_view()
        producer = farmer(recipe_id="smelt", capacity_runs=10.0)
        # revenue covers costs and the charge on one run worked, but not on all ten
        self.assertEqual(producers_close.close_year(producer, SMELT, 55.0, 50.0, view, 10.0).producer.years_of_loss, 1)
        self.assertEqual(producers_close.close_year(producer, SMELT, 55.0, 50.0, view, 1.0).producer.years_of_loss, 0)


class ExitTests(unittest.TestCase):
    def test_a_plantless_producer_with_no_margin_over_variable_cost_exits_after_the_loss_years(self):
        view = farm_view(0.5, cash=20.0)
        producer = farmer()
        for _year in range(producers_close.LOSS_YEARS_BEFORE_EXIT):
            result = producers_close.close_year(producer, FARM, 3.0, 70.0, view, 1.0)
            producer = result.producer
        self.assertTrue(result.exited)
        self.assertEqual(producer.capacity_runs, 0.0)
        self.assertAlmostEqual(sum(transfer.amount for transfer in result.transfers), 20.0)

    def test_a_loser_whose_runs_still_cover_variable_cost_does_not_exit(self):
        view = farm_view(2.0)
        producer = farmer()
        for _year in range(producers_close.LOSS_YEARS_BEFORE_EXIT + 3):
            result = producers_close.close_year(producer, FARM, 10.0, 100.0, view, 5.0)
            producer = result.producer
            self.assertFalse(result.exited)
        self.assertGreater(producer.capacity_runs, 0.0)

    def test_plant_with_a_positive_variable_margin_is_mothballed_and_wears_by_its_life(self):
        view = View({"metal": 20.0, "silver": 5.0, "ore": 1.0, "stone": 1.0}, {"smith": 1.0})
        producer = farmer(recipe_id="smelt", capacity_runs=10.0, years_of_loss=producers_close.LOSS_YEARS_BEFORE_EXIT)
        result = producers_close.close_year(producer, SMELT, 0.0, 500.0, view, 1.0)
        self.assertFalse(result.exited)
        self.assertAlmostEqual(result.producer.capacity_runs, 9.0)
        self.assertGreater(result.producer.years_of_loss, producers_close.LOSS_YEARS_BEFORE_EXIT)

    def test_a_profitable_producer_is_unaffected(self):
        result = producers_close.close_year(farmer(), FARM, 300.0, 100.0, farm_view(2.0), 10.0)
        self.assertFalse(result.exited)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0)
        self.assertEqual(result.producer.years_of_loss, 0)

    def test_a_sliver_of_past_scale_closes_and_a_working_producer_does_not(self):
        sliver = farmer(agent_id="sliver", capacity_runs=0.001, last_runs=10.0)
        working = farmer(agent_id="working", capacity_runs=5.0, last_runs=5.0)
        newcomer = farmer(agent_id="new", capacity_runs=0.0)
        closing = entry.producers_to_close({"sliver": sliver, "working": working, "new": newcomer}, set(), set())
        self.assertEqual(closing, ["new", "sliver"])


class ExitBooksTests(unittest.TestCase):
    def test_cash_goods_and_debt_of_an_exiting_producer(self):
        setup = small_setup()
        economy = Economy(setup)
        record, money = economy.record, setup.currency_id
        producer_id = next(agent for agent, each in sorted(record.producers.items()) if each.recipe_id == MINE)
        owner = record.producers[producer_id].owner
        record.book.transfer(Transfer(owner, producer_id, money, 30.0, "test stake"))
        record.book.move(GoodsMove(EDGE_PRODUCTION, producer_id, ORE, HILLS, 7.0, "test stock"))
        lender = next(agent for agent in sorted(record.cohorts) if agent != owner)
        record.loans.append(Loan("loan-1", lender, producer_id, money, 100.0, 0.05, 5.0, 0.0, arrears=10.0))
        cohort_cash = sum(record.book.balance(agent, money) for agent in record.cohorts)
        owner_ore = record.book.holdings(owner)["goods"].get(ORE, {}).get(HILLS, 0.0)
        held = record.book.balance(producer_id, money)
        payout = [Transfer(producer_id, owner, money, held, "dividend")]
        producer_exit.exit_producer(record, producer_id, payout)
        self.assertNotIn(producer_id, record.producers)
        self.assertAlmostEqual(sum(record.book.balance(agent, money) for agent in record.cohorts), cohort_cash + held)
        self.assertAlmostEqual(record.book.balance(producer_id, money), 0.0)
        self.assertAlmostEqual(record.book.holdings(owner)["goods"][ORE][HILLS], owner_ore + 7.0)
        self.assertEqual(record.loans, [])
        repaid = min(held, 110.0)
        self.assertAlmostEqual(record.credit_losses.get(lender, 0.0), 110.0 - repaid)
        self.assertAlmostEqual(record.remembered_defaults.get(producer_id, 0.0), 110.0 - repaid)
        self.assertGreater(held, 0.0)

    def test_lenders_are_repaid_before_the_owner(self):
        setup = small_setup()
        economy = Economy(setup)
        record, money = economy.record, setup.currency_id
        producer_id = next(agent for agent, each in sorted(record.producers.items()) if each.recipe_id == MINE)
        owner = record.producers[producer_id].owner
        tile = record.producers[producer_id].tile
        lender = next(agent for agent, cohort in sorted(record.cohorts.items()) if cohort.tile != tile)  # shares no dividend
        held = record.book.balance(producer_id, money)
        record.loans.append(Loan("loan-1", lender, producer_id, money, 0.5 * held, 0.05, 5.0, 0.0))
        owner_before = record.book.balance(owner, money)
        lender_before = record.book.balance(lender, money)
        producer_exit.exit_producer(record, producer_id, [Transfer(producer_id, owner, money, held, "dividend")])
        self.assertAlmostEqual(record.book.balance(lender, money) - lender_before, 0.5 * held)
        self.assertAlmostEqual(record.credit_losses.get(lender, 0.0), 0.0)
        self.assertLess(record.book.balance(owner, money) - owner_before, 0.5 * held + 1e-9)
        self.assertEqual(record.book.check_conservation(1e-6).breaches, ())
        self.assertEqual(record.book.check_conservation(1e-6).breaches, ())


class ScenarioTests(unittest.TestCase):
    def test_a_mine_whose_labour_costs_more_than_its_ore_is_worth_leaves_and_money_is_conserved(self):
        setup = small_setup(opening_wages={LABOURER: 1.0, MINER: 40.0, SMITH: 1.5})
        economy = Economy(setup)
        mines_by_year = []
        for _year in range(YEARS):
            economy.step(quiet_year(setup))
            mines_by_year.append(sum(producer.capacity_runs for producer in economy.record.producers.values()
                                     if producer.recipe_id == MINE))
        self.assertIn(0.0, mines_by_year)       # it left; it may come back once miners' wages fall
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())

    def test_a_healthy_economy_keeps_its_grain_producer(self):
        economy, _outcomes = run(small_setup(), YEARS)
        self.assertIn("grow_grain", " ".join(economy.record.producers))
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())


if __name__ == "__main__":
    unittest.main()
