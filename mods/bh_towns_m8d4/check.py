"""Standalone check of the town table, no game needed: python3 mods/bh_towns_m8d4/check.py"""
import glob
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)   # the hooks import the mod door, sim.mod_api
spec = importlib.util.spec_from_file_location("hooks", os.path.join(HERE, "hooks.py"))
hooks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hooks)

tiles = json.load(open(os.path.join(ROOT, "data/world/geography/tile_grid.json")))["tiles"]
towns = {}
for path in glob.glob(os.path.join(HERE, "data/world/geography/towns/*.json")):
    for entry in json.load(open(path))["entries"]:
        assert entry["id"] not in towns, "duplicate id " + entry["id"]
        towns[entry["id"]] = entry
for town in towns.values():
    assert town["tile"] in tiles, town["id"]
    years = [record["year"] for record in town["sizes"]]
    assert years == sorted(set(years)), "snapshots must be ascending and distinct: " + town["id"]
names = {}
for town in towns.values():
    for name in hooks._names(town):
        assert names.setdefault(name.lower(), town["id"]) == town["id"], "name on two towns: " + name

def listed(year):
    return {town["name"] for town, _record in hooks._present(towns.values(), year)}

assert "Paris" not in listed(100) and "London" in listed(100) and "Rome" in listed(1300)
assert "Birka" not in listed(100) and "Birka" in listed(900)
london = towns["bh_towns_m8d4:london"]
assert hooks._snapshot(london, 100)["name"] == "Londinium" and hooks._snapshot(london, 1300)["people"] == 80000
assert hooks._snapshot(london, 99) is None
print("ok: %d towns" % len(towns))
