"""A full-length spin-up whose first stage runs to its bound keeps that stage's trace, equal to the trace run on its
own (port_trace.spin_up_trace's rows), and keeping it leaves the spun-up record unchanged. On the hand-built economy."""
import json
import os
import tempfile
import unittest
from unittest import mock

from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.markets import port_sites, spin_up_run, spin_up_trace_cache
from sim.markets.port_trace import TraceRows
from sim.markets.spin_up import SPIN_UP_MAXIMUM_YEARS, SPIN_UP_YEARS_ENV
from sim.prices.api import solve_cache


def trace_on_its_own(setup, years):
    economy = economy_api.blank_economy(setup)
    economy_api.begin_spin_up(economy)
    inputs = EconomyYearInputs(year=0, population_by_tile={},
                               yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
    rows = TraceRows(setup)
    for _year in range(years):
        rows.add(economy, economy.step(inputs))
    return rows.rows


def plain_record(setup):
    economy = economy_api.blank_economy(setup)
    economy_api.begin_spin_up(economy)
    spin_up_run.spin_up(economy)
    return economy_api.export_record(economy, (spin_up_run.PURSE_CURRENCY,))


class SpinUpKeepsItsTraceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        environment = {key: value for key, value in os.environ.items() if key != SPIN_UP_YEARS_ENV}
        patches = [mock.patch.dict(os.environ, environment, clear=True),
                   mock.patch.object(spin_up_trace_cache, "TRACE_CACHE_DIRECTORY", self.directory)]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.setup_value = economy_api.fixture_small_setup()

    def kept(self):
        key = spin_up_trace_cache.trace_key_of_setup(self.setup_value)
        return solve_cache.cached_json(key, lambda: None, cache_dir=self.directory)

    def test_the_kept_trace_is_the_trace_run_on_its_own(self):
        spin_up_run.spun_up(self.setup_value)
        expected = json.loads(json.dumps(trace_on_its_own(self.setup_value, int(SPIN_UP_MAXIMUM_YEARS))))
        self.assertEqual(self.kept(), expected)

    def test_keeping_the_trace_leaves_the_record_unchanged(self):
        self.assertEqual(json.dumps(spin_up_run.spun_up(self.setup_value), sort_keys=True),
                         json.dumps(plain_record(self.setup_value), sort_keys=True))

    def test_a_shortened_spin_up_keeps_no_trace(self):
        with mock.patch.dict(os.environ, {SPIN_UP_YEARS_ENV: "3,2"}):
            spin_up_run.spun_up(self.setup_value)
        self.assertIsNone(self.kept())


if __name__ == "__main__":
    unittest.main()
