"""SCENARIO (Complaint 640): How the spin-up measures whether it settled: a rate near zero can settle, the reported result describes the
final (trimmed) state over several consecutive years and includes quantities, and the rebase keeps expectations."""
QUICK_TOPIC = True

import os
import types
import unittest
from unittest import mock

from sim.markets import port_year, spin_up_gap
from sim.book import Book, GoodsMove
from sim.economy import year_close
from sim.economy.spin_up_state import spin_up_state as year_state_of   # a pure read of a record, not a builder
from sim.economy.households_cohort import Cohort

FULL_GAME = {key: value for key, value in os.environ.items() if key != port_year.SPIN_UP_YEARS_ENV}
TOLERANCE = port_year.SPIN_UP_TOLERANCE


class ChangeGapTests(unittest.TestCase):
    def test_a_price_is_measured_by_its_relative_change(self):
        self.assertAlmostEqual(spin_up_gap.change_gap(1.5, 1.0), 0.5)

    def test_a_rate_shrinking_by_a_fixed_share_toward_zero_passes_beside_its_floor(self):
        rate = 0.05
        for _year in range(40):
            shrunk = rate * 0.9
            gap = spin_up_gap.change_gap(shrunk, rate, spin_up_gap.SPIN_UP_RATE_FLOOR)
            rate = shrunk
        self.assertLess(gap, TOLERANCE)

    def test_a_rate_that_really_moves_still_fails(self):
        self.assertGreater(spin_up_gap.change_gap(0.10, 0.05, spin_up_gap.SPIN_UP_RATE_FLOOR), TOLERANCE)

    def test_nothing_to_nothing_is_no_change_and_nothing_to_something_is_whole(self):
        self.assertEqual(spin_up_gap.change_gap(0.0, 0.0), 0.0)
        self.assertEqual(spin_up_gap.change_gap(3.0, 0.0), 1.0)

    def test_unmet_need_of_a_fraction_of_a_unit_is_not_measured_as_a_swing(self):
        self.assertLess(spin_up_gap.change_gap(0.004, 0.002, spin_up_gap.SPIN_UP_UNMET_FLOOR), TOLERANCE)


def _state(**changes):
    state = {"price_level": 1.0, "rate": 0.05, "prices": {"wheat_kg": 1.0}, "real_output": 100.0,
             "hired_hours": 50.0, "inventory_value": 10.0, "unmet_need": 0.0}
    state.update(changes)
    return state


class WindowGapTests(unittest.TestCase):
    def test_the_gap_is_the_worst_over_every_consecutive_pair_and_names_the_quantity(self):
        states = [_state(), _state(real_output=100.5), _state(real_output=130.0), _state(real_output=130.0)]
        gaps = spin_up_gap.window_gaps(states)
        self.assertAlmostEqual(gaps["real_output"], 29.5 / 100.5)
        self.assertEqual(gaps["price_level"], 0.0)
        self.assertEqual(gaps["prices"], 0.0)

    def test_fewer_than_two_states_measure_nothing(self):
        self.assertIsNone(spin_up_gap.window_gaps([_state()]))

    def test_employment_and_inventories_and_unmet_need_count_toward_settled(self):
        for name, moved in (("hired_hours", 80.0), ("inventory_value", 30.0), ("unmet_need", 5.0)):
            gaps = spin_up_gap.window_gaps([_state(), _state(**{name: moved})])
            self.assertGreater(gaps[name], TOLERANCE, name)


class FinalResultTests(unittest.TestCase):
    first = {"settled": True, "years": 7, "gap": 0.01}

    def test_the_result_is_settled_only_when_the_final_window_is(self):
        steady = [_state() for _year in range(4)]
        result = port_year.AgentEconomy.final_result(self.first, steady, 22)
        self.assertTrue(result["settled"])
        self.assertEqual(result["years"], 22)
        self.assertEqual(result["measured_years"], 4)
        self.assertEqual(result["first_stage"], self.first)
        self.assertEqual(result["final"]["real_output"], 100.0)
        moving = steady[:3] + [_state(real_output=200.0)]
        result = port_year.AgentEconomy.final_result(self.first, moving, 22)
        self.assertFalse(result["settled"])
        self.assertAlmostEqual(result["gap"], 1.0)

    def test_a_final_state_with_too_few_years_to_compare_is_not_settled(self):
        result = port_year.AgentEconomy.final_result(self.first, [_state()], 8)
        self.assertFalse(result["settled"])
        self.assertEqual(result["measured_years"], 1)


class StopRuleTests(unittest.TestCase):
    def test_the_first_stage_stops_when_a_rate_shrinking_toward_zero_has_constant_prices(self):
        economy = types.SimpleNamespace(setup=types.SimpleNamespace(currency_id="coin"),
                                        record=types.SimpleNamespace(memory=types.SimpleNamespace(rates={})), years=0)

        def step(inputs):
            economy.record.memory.rates["coin"] = 0.05 * 0.5 ** economy.years
            economy.years += 1
            return types.SimpleNamespace(basket_price_level=1.0, prices={"wheat_kg": 1.0})
        economy.step = step
        with mock.patch.dict(os.environ, FULL_GAME, clear=True):
            result = port_year.AgentEconomy._settle(economy, object(), ["wheat_kg"])
        self.assertTrue(result["settled"])


class OrderTests(unittest.TestCase):
    def test_the_recorded_result_is_measured_after_the_workforce_is_trimmed_and_trimmed_again_before_play(self):
        calls = []
        window = [_state() for _year in range(4)]
        agent = port_year.AgentEconomy.__new__(port_year.AgentEconomy)
        agent._economy = types.SimpleNamespace(setup=types.SimpleNamespace(opening_prices={}, working_share=0.5))
        api = port_year.economy_api
        first = {"settled": True, "years": 3, "gap": 0.0}
        with mock.patch.object(api, "opening_quantities", lambda economy: {}), \
                mock.patch.object(port_year.port_sites, "crop_yields", lambda economy: {}), \
                mock.patch.object(api, "trim_workforce_to_expected_hours", lambda economy: calls.append("trim")), \
                mock.patch.object(api, "finish_spin_up", lambda economy: calls.append("finish")), \
                mock.patch.object(api, "note_spin_up_result",
                                  lambda economy, result: calls.append(("note", result))), \
                mock.patch.object(port_year.AgentEconomy, "_settle",
                                  staticmethod(lambda economy, inputs, watched: calls.append("settle") or first)), \
                mock.patch.object(port_year.AgentEconomy, "_settle_trimmed",
                                  staticmethod(lambda economy, inputs, watched: calls.append("trimmed") or window)):
            agent._spin_up()
        self.assertEqual(calls[:5], ["settle", "trim", "trimmed", "trim", "finish"])
        self.assertEqual(calls[5][1]["measured_years"], 4)
        self.assertEqual(calls[5][1]["first_stage"], first)


class StateTests(unittest.TestCase):
    def test_a_year_state_carries_output_employment_inventory_and_unmet_need(self):
        book = Book()
        book.move(GoodsMove("edge:production", "producer:a", "wheat_kg", "farms", 40.0, "production"))
        setup = types.SimpleNamespace(opening_prices={"wheat_kg": 2.0})
        record = types.SimpleNamespace(producers={"producer:a": None}, book=book)
        outcome = types.SimpleNamespace(output={"wheat_kg": 100.0}, hired_hours=900.0, idle_hours=100.0,
                                        hunger_by_tile={"farms": 3.0, "town": 1.5})
        state = year_state_of(setup, record, outcome)
        self.assertEqual(sorted(state), ["hired_hours", "idle_hours", "inventory_value", "real_output", "unmet_need"])
        self.assertEqual(state["real_output"], 200.0)           # at the opening prices
        self.assertEqual(state["hired_hours"], 900.0)
        self.assertEqual(state["inventory_value"], 80.0)
        self.assertEqual(state["unmet_need"], 4.5)


class RebaseTests(unittest.TestCase):
    def test_rebasing_keeps_what_households_and_the_market_expect_of_inflation(self):
        money = "coin"
        memory = types.SimpleNamespace(
            prices={"wheat_kg|area": 1.5}, volume_weights={}, quote_kinds={}, basket_price_levels={money: 1.8},
            price_levels={money: 1.7}, expected_inflation={money: 0.07})
        cohorts = {"household:a": Cohort("household:a", "farms", 0, 10.0, 5.0, 0.2, expected_inflation=0.07,
                                         last_basket_price_level=1.8)}
        record = types.SimpleNamespace(memory=memory, volumes={"wheat_kg|area": 10.0}, cohorts=cohorts, index_base_prices={})
        year_close.rebase_basket_price_level(types.SimpleNamespace(currency_id=money), record)
        self.assertEqual(record.index_base_prices, {"wheat_kg": 1.5})
        self.assertEqual(memory.basket_price_levels[money], 1.0)
        self.assertEqual(memory.expected_inflation[money], 0.07)
        for cohort in record.cohorts.values():
            self.assertEqual(cohort.expected_inflation, 0.07)
            self.assertEqual(cohort.last_basket_price_level, 1.0)


if __name__ == "__main__":
    unittest.main()
