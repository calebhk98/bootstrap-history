"""Complaint 634: the urbanisation mod's yearly phase writes each tile's derived town and mortality premium into its two stores,
and the town provider it registers reads them back for the labour market, with no opinion before the first year. `register` is
called on a recording stand-in for the mod api and `urban_report` is replaced by rows written here; registration is
test_urbanisation_mod_registration_rule and the premium reaching deaths is test_urban_mortality_premium."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.tests.mod_files import load_mod_file

MOD = "bh_urbanisation_w2n6"
ROWS = [{"tile": "t1", "town_people": 4000, "urban_mortality_premium": 0.25},
        {"tile": "t2", "town_people": 900, "urban_mortality_premium": 0.05}]


class Store:
    def __init__(self):
        self.values = {}

    def get(self, sim, tile):
        return self.values.get(tile)


class FakeApi:
    """What `register` calls: stores, one phase, one town provider and a command decorator."""

    def __init__(self):
        self.stores, self.written, self.phase_handler, self.provider, self.premium = {}, [], None, None, None

    def reads(self, *views):
        pass

    def store(self, name, keyed_by, default, unit=""):
        self.stores[name] = Store()
        return self.stores[name]

    def phase(self, name, scope, handler, after=(), before=()):
        self.phase_handler = handler

    def town_provider(self, name, function, mortality_premium=None):
        self.provider, self.premium = function, mortality_premium

    def command(self, name, **fields):
        return lambda handler: handler

    def write_store(self, sim, name, key, value):
        self.written.append((name, key, value))
        self.stores[name].values[key] = value


def registered():
    hooks = load_mod_file(MOD, "hooks.py")
    api = FakeApi()
    hooks.register(api)
    return hooks, api


class RecordTownsTests(unittest.TestCase):
    def test_every_tile_writes_its_town_and_its_premium(self):
        hooks = load_mod_file(MOD, "hooks.py")
        written = []
        with mock.patch.object(hooks, "urban_report", return_value={"towns": ROWS}):
            hooks.record_towns(object(), lambda store, tile, value: written.append((store, tile, value)))
        self.assertEqual(written, [("town_people", "t1", 4000), ("urban_mortality_premium", "t1", 0.25),
                                   ("town_people", "t2", 900), ("urban_mortality_premium", "t2", 0.05)])

    def test_the_report_is_asked_for_every_tile_not_the_rows_shown(self):
        hooks = load_mod_file(MOD, "hooks.py")
        with mock.patch.object(hooks, "urban_report", return_value={"towns": []}) as report:
            hooks.record_towns(object(), lambda store, tile, value: None)
        self.assertIsNone(report.call_args.kwargs["limit"])


class RegisteredHooksTests(unittest.TestCase):
    def test_the_phase_writes_the_derived_towns_into_the_mods_stores(self):
        hooks, api = registered()
        with mock.patch.object(hooks, "urban_report", return_value={"towns": ROWS}):
            api.phase_handler(object(), [])
        self.assertEqual(api.stores["town_people"].values, {"t1": 4000, "t2": 900})
        self.assertEqual(api.stores["urban_mortality_premium"].values, {"t1": 0.25, "t2": 0.05})

    def test_the_provider_hands_the_stored_town_and_premium_to_the_labour_market(self):
        _hooks, api = registered()
        api.stores["town_people"].values["t1"] = 4000
        api.stores["urban_mortality_premium"].values["t1"] = 0.25
        self.assertEqual(api.provider(object(), "t1", 1000.0), 4000)
        self.assertEqual(api.premium(object(), "t1", 4000), 0.25)

    def test_before_the_first_year_the_provider_has_no_opinion(self):
        _hooks, api = registered()
        self.assertIsNone(api.provider(object(), "t1", 1000.0))
        self.assertIsNone(api.premium(object(), "t1", 1000.0))


if __name__ == "__main__":
    unittest.main()
