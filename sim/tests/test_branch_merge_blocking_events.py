"""`treetool.py merge --dry-run` must not lose anything a branch author wrote.

Complaints/54. The merge refuses to write while any event would drop a
requirement. Unknown trades, unresolvable prerequisites and dependency cycles
must stay at zero. Undeclared materials still block, and each remaining name is
pinned with its event count. The pin fails in both directions: a new name (or a
higher count) is a regression, and a cleared name asks to be un-pinned so the
list can only shrink.
"""
import collections
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# Materials that branch nodes name and no production recipe makes.
# Each needs a recipe with a physical yield, or a node edit; none may be guessed.
KNOWN_UNDECLARED_MATERIALS = {
    "arsenic": 1,
    "basic_slag": 1,
    "copper_wire_km": 1,
    "ethylene_glycol": 1,
    "fulminate_kg": 2,
    "hops": 1,
    "horn_kg": 3,
    "human_hair_g": 1,
    "hydrogen": 1,
    "magnesium_fluoride": 2,
    "mat_acetic_anhydride_kg": 1,
    "mat_acrylonitrile_kg": 1,
    "mat_adipic_acid_kg": 1,
    "mat_alnico_kg": 1,
    "mat_animal_gut": 1,
    "mat_bentonite_slurry": 1,
    "mat_bimetallic_kg": 1,
    "mat_cadmium_kg": 1,
    "mat_cemented_carbide": 1,
    "mat_cobalt": 4,
    "mat_copper_beryllium": 1,
    "mat_copper_wire_km": 1,
    "mat_ferrite_kg": 1,
    "mat_flame_retardant_kg": 1,
    "mat_glycerol": 1,
    "mat_glycerol_kg": 1,
    "mat_gum_kg": 1,
    "mat_gutta_percha": 1,
    "mat_iodine_compound": 1,
    "mat_magnesium": 4,
    "mat_mica": 2,
    "mat_mica_sheet_kg": 1,
    "mat_mirror_amalgam": 1,
    "mat_nickel_oxide_kg": 1,
    "mat_nylon": 1,
    "mat_oil_kg": 2,
    "mat_opium": 1,
    "mat_peroxide_h2o2_kg": 1,
    "mat_pesticide_kg": 1,
    "mat_phenolic_paper": 1,
    "mat_plant_extract": 1,
    "mat_polyethylene": 1,
    "mat_potash": 1,
    "mat_potato_starch": 1,
    "mat_silicon_carbide_kg": 1,
    "mat_silk_m": 4,
    "mat_starch_kg": 1,
    "mat_sugar": 1,
    "mat_tar": 1,
    "mat_titanium": 1,
    "mat_vanadium": 1,
    "mat_xenon_kg": 1,
    "media": 1,
    "mica": 1,
    "mirror_amalgam_kg": 1,
    "mulberry_leaves_kg": 1,
    "nicotine_extract": 1,
    "plutonium_kg": 1,
    "pyrethrum_flower": 1,
    "shell_kg": 1,
    "thickener_kg": 1,
    "tobacco_extract": 1,
    "uranium_235_kg": 1,
    "uranium_kg": 1,
}

ZERO_CATEGORIES = ("unknown_trade", "unresolvable_prerequisite", "material_is_technology", "dependency_cycle")


def measure_merge_events():
    """{category: [message, ...]} from a dry-run merge."""
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "sim", "treetool.py"), "merge", "--dry-run"],
        cwd=ROOT, capture_output=True, text=True, check=False)
    events = collections.defaultdict(list)
    category = None
    for line in result.stdout.splitlines():
        header = re.match(r"  (\w+) \(\d+\)$", line)
        if header:
            category = header.group(1)
        elif category and line.startswith("     "):
            events[category].append(line.strip())
    return events


def measure_undeclared_counts(events):
    counts = collections.Counter()
    for message in events.get("undeclared_material", []):
        match = re.search(r"UNDECLARED material '([^']+)'", message)
        counts[match.group(1)] += 1
    return counts


class BranchMergeBlockingEventTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.events = measure_merge_events()

    def test_no_unknown_trades_prerequisites_or_cycles(self):
        for category in ZERO_CATEGORIES:
            self.assertEqual(self.events.get(category, []), [], (
                "merge --dry-run reports %s events. Fix the branch source "
                "(trade alias in data/branches/ALIASES.json, prerequisite id, or the cycle edge)."
                % category))

    def test_no_new_undeclared_material(self):
        counts = measure_undeclared_counts(self.events)
        worse = {name: count for name, count in counts.items()
                 if count > KNOWN_UNDECLARED_MATERIALS.get(name, 0)}
        self.assertEqual(worse, {}, (
            "New undeclared material events: %s. Add a production recipe "
            "in data/production/ or alias the name in data/branches/ALIASES.json." % worse))

    def test_a_cleared_material_lowers_the_pin(self):
        counts = measure_undeclared_counts(self.events)
        cleared = {name: pinned for name, pinned in KNOWN_UNDECLARED_MATERIALS.items()
                   if counts.get(name, 0) < pinned}
        self.assertEqual(cleared, {}, (
            "Cleared or reduced: %s. Lower KNOWN_UNDECLARED_MATERIALS so the "
            "count can only go down." % cleared))


if __name__ == "__main__":
    unittest.main()
