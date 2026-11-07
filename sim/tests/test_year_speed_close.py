"""Numba port item 0b: the producers' year end over the year arrays (close_kernel) does what the per-producer Python it
replaced does (producers_close.close_year, firm_year.settle_year, year_close.runs_sold and _with_sales), on random built
economies. The old functions are the reference and are called here exactly as the old close loop called them.

Tolerance: a relative 1e-9. The kernel sums left to right over a recipe's goods in sorted order where the Python sums in
dictionary order or with math.fsum, so the last digits differ; a rule that compares two sums (a loss year, a margin below
zero) could in principle flip under that nudge, and the random economies here do not come near one."""

QUICK_TOPIC = True

import math
import unittest

import numpy as np

from sim.economy import expansion_price, firm_finance, firm_year, producers, producers_close, year_close
from sim.economy.close_kernel import REQUEST_EXPAND, REQUEST_NONE, STATE_OK
from sim.economy.close_pack import pack
from sim.economy.close_run import close_producers
from sim.economy.expected_sales import market_capacities
from sim.economy.producers import live_input_prices, live_wages
from sim.economy.year_arrays import YearArrays
from sim.tests.year_close_fixture import economy_of

STATES = ("ok", "crisis", "illiquid", "insolvent")
SHARE = 0.9


def close(a, b, tolerance=1e-9):
    if a is None or b is None:
        return a is None and (b is None or math.isnan(b)) or b is None and math.isnan(a)
    return a == b or abs(a - b) <= tolerance * max(1.0, abs(a), abs(b))


def old_close(setup, record, view, ledger, area_map, producer_id):
    """The old loop body up to the producer put back; (YearClose, FirmYear or None, demand runs, the producer after, prices)."""
    traded, round_prices = ledger.market_totals()
    clearing = {key: price for key, price in round_prices.items() if traded[key] > 0.0 and price is not None}
    loans = [loan for loan in record.credit.loans if loan.borrower == producer_id]
    capacity = market_capacities(((each.tile, setup.recipes[each.recipe_id].outputs, each.capacity_runs * each.yield_factor)
                                  for each in record.producers.values() if each.idle_years <= 0), area_map.area_of)
    producer = record.producers[producer_id]
    recipe = setup.recipes[producer.recipe_id]
    revenue, costs = ledger.sales_in.get(producer_id, 0.0), ledger.running_costs(producer_id)
    here = year_close._prices_here(clearing, recipe, area_map.area_of, producer.tile)
    worked = year_close.worked_runs(producer, recipe, ledger, producers.paying_output(recipe, here))
    demand = year_close.runs_sold(producer, recipe, ledger, record.book, area_map.area_of, here, capacity)
    inputs, wages = live_input_prices(producer, recipe, view), live_wages(producer, recipe, view)
    closed = producers_close.close_year(
        producer, recipe, revenue, costs, view, worked, lambda good, added: SHARE,
        [good for good in recipe.outputs if good in setup.specs and not setup.specs[good].portable],
        {good: spec.service_life_years for good, spec in setup.specs.items()}, firm_finance.interest_due(loans, producer_id), demand,
        spoilage={good: setup.specs[good].spoilage_per_year for good in recipe.outputs if good in setup.specs},
        inputs=inputs, wages=wages)
    year = None
    if not closed.exited:
        closed, _paid, year = firm_year.settle_year(setup, record, view, producer, closed, recipe, revenue, costs, loans, inputs, wages)
    return closed, year, demand, here


class KernelEqualsThePerProducerClose(unittest.TestCase):
    def test_every_producer_closes_as_the_python_close_does(self):
        compared = exits = bankrupt = expansions = 0
        for seed in range(12):
            setup, record, view, ledger, area_map = economy_of(seed, producer_count=60)
            arrays = YearArrays.build(setup, record, area_map, view)
            answer = close_producers(arrays, pack(setup, record, view, ledger, arrays),
                                     lambda row, added: np.full(len(added), SHARE))
            for row, producer_id in enumerate(arrays.producers.ids):
                producer = record.producers[producer_id]
                if producer.idle_years > 0:
                    continue
                closed, year, demand, here = old_close(setup, record, view, ledger, area_map, producer_id)
                recipe = setup.recipes[producer.recipe_id]
                self.assertEqual(bool(answer.exited[row]), closed.exited, producer_id)
                self.assertTrue(close(demand, answer.demand_runs[row]), (producer_id, demand, answer.demand_runs[row]))
                self.assertTrue(close(sum(each.amount for each in closed.transfers), answer.dividend[row]), producer_id)
                compared += 1
                if closed.exited:
                    exits += 1
                    continue
                after = closed.producer
                self.assertTrue(close(after.capacity_runs, answer.new_capacity[row]), (producer_id, after.capacity_runs, answer.new_capacity[row]))
                self.assertEqual(after.years_of_loss, answer.new_losses[row])
                self.assertTrue(close(after.cash_target, answer.new_target[row]), producer_id)
                self.assertEqual(STATES.index(year.state), answer.state[row], producer_id)
                self.assertTrue(close(year.write_off_ratio, answer.write_off[row]), producer_id)
                self.assertEqual(after.idle_years, answer.new_idle[row])
                self.assertTrue(close(closed.replacement_runs, answer.replacement_runs[row]), producer_id)
                self.assertTrue(close(closed.expansion_runs, answer.expansion_runs[row]), producer_id)
                count = answer.new_count[row]
                self.assertEqual(len(after.net_earnings_history), count)
                self.assertTrue(close(after.net_earnings_history[-1], answer.new_earnings[row, count - 1]), producer_id)
                self.assertTrue(close(after.revenue_history[-1], answer.new_revenues[row, count - 1]), producer_id)
                request = closed.loan_request
                self.assertEqual(answer.request_kind[row],
                                 REQUEST_NONE if request is None else REQUEST_EXPAND if request.purpose == "expand" else 2, producer_id)
                if request is not None:
                    self.assertTrue(close(request.amount, answer.request_amount[row]), producer_id)
                    self.assertTrue(close(request.maximum_rate, answer.request_rate[row]), producer_id)
                    self.assertTrue(close(request.collateral_value, answer.request_collateral[row]), producer_id)
                    expansions += request.purpose == "expand"
                bankrupt += answer.state[row] != STATE_OK and year.state in ("illiquid", "insolvent")
                for slot, column in enumerate(arrays.matrices.slot_goods[arrays.producers.recipe_row[row]]):
                    if column >= 0 and answer.written[row, slot]:
                        good = arrays.matrices.goods.ids[column]
                        self.assertTrue(close(after.expected_prices[good], answer.new_expected[row, slot]), (producer_id, good))
                    elif column >= 0:
                        good = arrays.matrices.goods.ids[column]
                        self.assertEqual(after.expected_prices.get(good), producer.expected_prices.get(good))
                sales = year_close._with_sales(after, recipe, ledger, demand, here)
                self.assertTrue(close(sales.expected_sales, answer.new_expected_sales[row]), producer_id)
                self.assertTrue(close(sales.last_runs, answer.new_last_runs[row]), producer_id)
                self.assertTrue(close(sales.staffed_runs, answer.new_staffed[row]), producer_id)
        self.assertGreater(compared, 400)
        self.assertGreater(exits, 0)          # the random economies reach each branch, so the comparison covers it
        self.assertGreater(expansions, 0)

    def test_no_producers_is_an_empty_answer(self):
        setup, record, view, ledger, area_map = economy_of(0, producer_count=1)
        record.producers.clear()
        arrays = YearArrays.build(setup, record, area_map, view)
        answer = close_producers(arrays, pack(setup, record, view, ledger, arrays), None)
        self.assertEqual(len(answer.new_capacity), 0)


if __name__ == "__main__":
    unittest.main()
