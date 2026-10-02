"""Producers: planning on expected prices, Leontief production, offers, and the year's close."""
import unittest

from sim.economy import producers, producers_close
from sim.economy.types import EDGE_CONSUMPTION, EDGE_PRODUCTION, GoodSpec, Recipe

FARM = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})
SMELT = Recipe("smelt", {"metal": 10.0, "silver": 1.0}, {"ore": 4.0}, {"smith": 1.0},
               {"stone": 10.0}, {}, 10.0)


class View:
    year = 3

    def __init__(self, prices=None, wages=None, rate=0.05, cash=0.0, stock=None):
        self.prices, self.wages, self.rate, self.cash_held, self.stocks = (
            prices or {}, wages or {}, rate, cash, stock or {})

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return self.rate

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def price_level(self, currency):
        return 1.0

    def expected_inflation(self, currency):
        return 0.0

    def cash(self, agent, currency):
        return self.cash_held

    def stock(self, agent, good, tile):
        return self.stocks.get(good, 0.0)


def farmer(**changes):
    base = dict(agent_id="f1", owner="lord", recipe_id="farm", tile="t", capacity_runs=10.0)
    base.update(changes)
    return producers.Producer(**base)


def farm_view(grain_price, **changes):
    return View({"grain": grain_price, "seed": 1.0}, {"hand": 1.0}, **changes)     # a run costs 2 + 5


class PlanTests(unittest.TestCase):
    def test_idles_below_variable_cost_and_resumes_when_the_price_rises(self):
        low = producers.plan(farmer(), FARM, farm_view(0.6), 1000.0)         # revenue 6 < cost 7
        self.assertEqual(low.runs, 0.0)
        self.assertEqual((low.bids, low.labour_bids), ((), ()))
        high = producers.plan(farmer(), FARM, farm_view(0.8), 1000.0)
        self.assertEqual(high.runs, 10.0)

    def test_orders_follow_the_plan_and_budgets_stay_within_cash(self):
        plan = producers.plan(farmer(), FARM, farm_view(2.0), 100.0)         # 7 a run: cash allows 14, cap 10
        self.assertEqual(plan.runs, 10.0)
        self.assertEqual(plan.bids[0].floor_quantity, 20.0)
        self.assertEqual(plan.labour_bids[0].hours, 50.0)
        self.assertAlmostEqual(plan.labour_bids[0].maximum_wage, (20.0 - 2.0) / 5.0)
        spent = sum(bid.budget for bid in plan.bids) + plan.runs * 5.0
        self.assertLessEqual(spent, 100.0 + 1e-9)

    def test_cash_limits_the_runs(self):
        plan = producers.plan(farmer(), FARM, farm_view(2.0), 21.0)
        self.assertAlmostEqual(plan.runs, 3.0)

    def test_held_inputs_are_not_bought_again(self):
        plan = producers.plan(farmer(), FARM, farm_view(2.0, stock={"seed": 20.0}), 1000.0)
        self.assertEqual(plan.bids, ())

    def test_cobweb_output_follows_last_years_price_not_this_years(self):
        expecting_high = farmer(expected_prices={"grain": 2.0})
        self.assertEqual(producers.plan(expecting_high, FARM, farm_view(0.1), 1000.0).runs, 10.0)
        expecting_low = farmer(expected_prices={"grain": 0.1})
        self.assertEqual(producers.plan(expecting_low, FARM, farm_view(5.0), 1000.0).runs, 0.0)

    def test_a_poor_harvest_yield_lowers_the_revenue_a_run_counts_on(self):
        self.assertEqual(producers.plan(farmer(yield_factor=0.5), FARM, farm_view(1.0), 1000.0).runs, 0.0)

    def test_no_input_price_means_no_plan(self):
        view = View({"grain": 5.0}, {"hand": 1.0})
        self.assertEqual(producers.plan(farmer(), FARM, view, 1000.0).runs, 0.0)


class ProduceTests(unittest.TestCase):
    def test_the_scarcest_input_limits_the_runs(self):
        achieved, moves = producers.produce(farmer(), FARM, {"seed": 6.0}, {"hand": 500.0}, 10.0)
        self.assertAlmostEqual(achieved, 3.0)
        by_good = {move.good: move for move in moves}
        self.assertEqual(by_good["seed"].receiver, EDGE_CONSUMPTION)
        self.assertAlmostEqual(by_good["seed"].quantity, 6.0)
        self.assertEqual(by_good["grain"].giver, EDGE_PRODUCTION)
        self.assertAlmostEqual(by_good["grain"].quantity, 30.0)

    def test_hours_can_be_the_scarcest(self):
        achieved, _moves = producers.produce(farmer(), FARM, {"seed": 100.0}, {"hand": 10.0}, 10.0)
        self.assertAlmostEqual(achieved, 2.0)

    def test_the_yield_factor_scales_output_not_inputs(self):
        achieved, moves = producers.produce(farmer(yield_factor=0.5), FARM, {"seed": 20.0}, {"hand": 50.0}, 10.0)
        self.assertAlmostEqual(achieved, 5.0)
        self.assertAlmostEqual(sum(m.quantity for m in moves if m.good == "seed"), 20.0)
        self.assertAlmostEqual(sum(m.quantity for m in moves if m.good == "grain"), 50.0)

    def test_joint_outputs_are_both_booked(self):
        _achieved, moves = producers.produce(farmer(recipe_id="smelt"), SMELT, {"ore": 8.0}, {"smith": 2.0}, 2.0)
        self.assertEqual({move.good for move in moves if move.giver == EDGE_PRODUCTION}, {"metal", "silver"})

    def test_nothing_is_made_without_inputs(self):
        self.assertEqual(producers.produce(farmer(), FARM, {}, {"hand": 50.0}, 10.0), (0.0, []))


SPECS = {"metal": GoodSpec("metal", 1.0, 0.0, 0.0, "x"), "silver": GoodSpec("silver", 1.0, 0.0, 0.0, "x"),
         "fish": GoodSpec("fish", 1.0, 1.0, 0.0, "x")}


class OfferTests(unittest.TestCase):
    def smelter(self):
        return farmer(recipe_id="smelt", expected_prices={"metal": 4.0, "silver": 30.0})

    def test_joint_outputs_are_each_offered_on_their_own_market_at_the_holding_reservation(self):
        rows = producers.offers(self.smelter(), SMELT, View(), {"metal": 5.0, "silver": 1.0}, 0.0, 0.05, SPECS)
        self.assertEqual({row.good for row in rows}, {"metal", "silver"})
        metal = next(row for row in rows if row.good == "metal")
        self.assertAlmostEqual(metal.reservation_price, 4.0 / 1.05)      # not the cost of making it

    def test_cash_shortage_lowers_the_reservation(self):
        calm = producers.offers(self.smelter(), SMELT, View(), {"metal": 5.0}, 0.0, 0.05, SPECS)[0]
        needy = producers.offers(self.smelter(), SMELT, View(), {"metal": 5.0}, 10.0, 0.05, SPECS)[0]
        self.assertLess(needy.reservation_price, calm.reservation_price)

    def test_a_perishable_sells_at_any_price(self):
        fish = Recipe("fish", {"fish": 1.0}, {}, {})
        rows = producers.offers(farmer(expected_prices={"fish": 3.0}), fish, View(), {"fish": 4.0}, 0.0, 0.05, SPECS)
        self.assertLessEqual(rows[0].reservation_price, 0.0)

    def test_stock_kept_back_for_inputs_is_not_offered(self):
        rows = producers.offers(self.smelter(), SMELT, View(), {"metal": 5.0}, 0.0, 0.05, SPECS, {"metal": 5.0})
        self.assertEqual(rows, [])


class CloseYearTests(unittest.TestCase):
    def test_dividends_are_the_cash_above_target_and_never_more_than_cash(self):
        view = farm_view(2.0, cash=500.0)
        result = producers_close.close_year(farmer(), FARM, 300.0, 100.0, view)
        dividend = sum(transfer.amount for transfer in result.transfers)
        self.assertGreater(dividend, 0.0)
        self.assertLessEqual(dividend, 500.0)
        self.assertAlmostEqual(dividend, 500.0 - result.producer.cash_target)
        self.assertEqual(result.transfers[0].payee, "lord")

    def test_no_dividend_when_cash_is_below_target(self):
        result = producers_close.close_year(farmer(), FARM, 300.0, 100.0, farm_view(2.0, cash=5.0))
        self.assertEqual(result.transfers, ())

    def test_exit_after_persistent_losses_pays_out_the_cash(self):
        view = farm_view(2.0, cash=50.0)
        producer = farmer()
        for _year in range(producers_close.LOSS_YEARS_BEFORE_EXIT):
            self.assertGreater(producer.capacity_runs, 0.0)
            result = producers_close.close_year(producer, FARM, 10.0, 100.0, view)
            producer = result.producer
        self.assertTrue(result.exited)
        self.assertEqual(producer.capacity_runs, 0.0)
        self.assertAlmostEqual(sum(transfer.amount for transfer in result.transfers), 50.0)

    def test_a_profitable_year_resets_the_count(self):
        view = farm_view(2.0)
        lost = producers_close.close_year(farmer(), FARM, 10.0, 100.0, view).producer
        self.assertEqual(lost.years_of_loss, 1)
        self.assertEqual(producers_close.close_year(lost, FARM, 500.0, 100.0, view).producer.years_of_loss, 0)

    def test_plant_wears_without_replacement_when_new_plant_does_not_pay(self):
        view = View({"metal": 0.1, "silver": 0.1, "ore": 1.0, "stone": 1.0}, {"smith": 1.0})
        producer = farmer(recipe_id="smelt", capacity_runs=10.0)
        result = producers_close.close_year(producer, SMELT, 100.0, 50.0, view)
        self.assertAlmostEqual(result.producer.capacity_runs, 9.0)
        self.assertIsNone(result.loan_request)

    def test_a_loan_to_expand_is_asked_only_when_new_plant_beats_the_rate(self):
        rich = View({"metal": 20.0, "silver": 5.0, "ore": 1.0, "stone": 1.0}, {"smith": 1.0})
        result = producers_close.close_year(farmer(recipe_id="smelt"), SMELT, 500.0, 50.0, rich)
        request = result.loan_request
        self.assertIsNotNone(request)
        self.assertGreater(request.maximum_rate, rich.rate)
        self.assertGreater(result.expansion_runs, 1.0)
        self.assertAlmostEqual(request.amount, result.expansion_runs * 10.0)

    def test_expected_prices_move_toward_the_latest_price(self):
        view = farm_view(3.0)
        result = producers_close.close_year(farmer(expected_prices={"grain": 1.0}), FARM, 100.0, 10.0, view)
        expected = result.producer.expected_prices["grain"]
        self.assertGreater(expected, 1.0)
        self.assertLessEqual(expected, 3.0)


class EntrantTests(unittest.TestCase):
    def sites(self):
        return [producers_close.Site("t%d" % i, "owner%d" % i, 5.0) for i in range(6)]

    def test_entry_where_return_beats_the_rate_and_not_where_it_does_not(self):
        rich = View({"grain": 5.0, "seed": 1.0}, {"hand": 1.0})
        poor = View({"grain": 0.5, "seed": 1.0}, {"hand": 1.0})
        self.assertTrue(producers_close.entrants({"farm": FARM}, rich, self.sites()))
        self.assertEqual(producers_close.entrants({"farm": FARM}, poor, self.sites()), [])

    def test_entry_is_bounded_each_year_and_skips_occupied_sites(self):
        rich = View({"grain": 5.0, "seed": 1.0}, {"hand": 1.0})
        chosen = producers_close.entrants({"farm": FARM}, rich, self.sites(), occupied={("farm", "t0")})
        self.assertEqual(len(chosen), producers_close.MAXIMUM_ENTRANTS_PER_YEAR)
        self.assertNotIn("t0", [producer.tile for producer in chosen])
        self.assertEqual(chosen[0].expected_prices["grain"], 5.0)

    def test_entry_is_deterministic(self):
        rich = View({"grain": 5.0, "seed": 1.0}, {"hand": 1.0})
        first = producers_close.entrants({"farm": FARM}, rich, self.sites())
        self.assertEqual(first, producers_close.entrants({"farm": FARM}, rich, list(reversed(self.sites()))))


if __name__ == "__main__":
    unittest.main()
