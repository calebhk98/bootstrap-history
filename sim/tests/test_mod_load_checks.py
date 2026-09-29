"""Checks the real load path runs: removed trades in technologies, removed starting techs."""
import glob
import json
import os
from unittest import mock
import unittest

from sim.engine import data, prices
from sim.engine.mods import ModError
from sim.tests.test_mod_removal_and_civs import ModTestBase


def _labour_only_trade():
    """A base trade some technology needs and no production recipe uses."""
    used = set()
    for entry in data.load_production_catalog(data.ROOT, data.MODDIR).values():
        used.update(entry.get("labour_hours") or {})
        for capital in entry.get("capital") or ():
            used.update(capital.get("build_labour_hours") or {})
    with open(data.TREE) as source:
        wanted = {trade for node in json.load(source)["nodes"] for trade in node.get("lab") or {}}
    return sorted((wanted - used) & set(data._TRADE_REGISTRY))[0]


def _tech_only_in_one_non_rome_civ():
    owners = {}
    for path in glob.glob(os.path.join(data.CIVDIR, "[a-z]*.json")):
        with open(path) as source:
            civ = json.load(source)
        for tech_id in civ["starting_techs"]:
            owners.setdefault(tech_id, []).append(civ["id"])
    for tech_id, civ_ids in sorted(owners.items()):
        if len(civ_ids) == 1 and civ_ids[0] != "rome_100ad":
            return tech_id, civ_ids[0]
    raise AssertionError("no such tech")


class RealLoadPathTests(ModTestBase):
    def test_load_catches_removed_trade_used_by_technology(self):
        trade = _labour_only_trade()
        self.add_mod("test_acme_k3f9", trades={trade: {"remove": True}})
        with mock.patch.object(data, "MODDIR", str(self.mods_dir)):
            with self.assertRaises(ModError) as caught:
                data.load()
        for word in (trade, "test_acme_k3f9"):
            self.assertIn(word, str(caught.exception))

    def test_price_solver_registry_sees_technologies(self):
        trade = _labour_only_trade()
        self.add_mod("test_acme_k3f9", trades={trade: {"remove": True}})
        with mock.patch("sim.engine.catalog.get_ordered_mods", return_value=self.manifests()):
            with self.assertRaises(ModError):
                prices.solver_trade_registry({})

    def test_all_civs_checked_at_load_even_if_unpicked(self):
        tech_id, civ_id = _tech_only_in_one_non_rome_civ()
        self.add_mod("test_acme_k3f9", nodes=[{"id": tech_id, "remove": True}])
        with mock.patch.object(data, "MODDIR", str(self.mods_dir)):
            with self.assertRaises(ModError) as caught:
                data.load()
        for word in (tech_id, civ_id, "test_acme_k3f9"):
            self.assertIn(word, str(caught.exception))

    def test_mod_civ_with_removed_starting_tech_is_reported_at_load(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "test_acme_k3f9:tool", "name": "Tool"}],
                     civs={"test_acme_k3f9:land": {"id": "test_acme_k3f9:land", "starting_techs": ["test_acme_k3f9:tool"]}})
        self.add_mod("test_zeta_k3f9", dependencies=["test_acme_k3f9"], nodes=[{"id": "test_acme_k3f9:tool", "remove": True}])
        with mock.patch.object(data, "MODDIR", str(self.mods_dir)):
            with self.assertRaises(ModError) as caught:
                data.load()
        for word in ("test_acme_k3f9:land", "test_acme_k3f9:tool", "test_zeta_k3f9"):
            self.assertIn(word, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
