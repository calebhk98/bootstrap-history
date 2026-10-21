"""BASELINE VALIDATION (CLAUDE.md 4.2, Complaint 648), slow only. Not a rule test: it plays Rome from `rome_100ad` for two
market years under several seeds, with no intervention, and reads the bonded stratum's share of all people at the end.
The range is read from the civilisation file's own source note (Scheidel 2005, JRS 95: 64-79: eight to fifteen per cent
of the empire's people), never typed here; a share outside it, or a bonded stratum that went empty, fails and names the
complaint. A validation, not a target: nothing in the model aims at the range. The captives and the bonded purchases a
game makes are counted and printed so a run shows whether the supply side acted at all.
Run one seed at a time with `python3 -m sim.tests --slow --only rome_bonded_share_baseline_validation --jobs 1`
(each game takes a few minutes)."""

import functools
import random
import re
import unittest

from . import harness  # noqa: F401  (sets the short spin-up the suite's games open on)
from sim.engine.ui_port import Sim, load, load_civ

SEEDS = (1, 2, 3)
YEARS = 2


def sourced_range(civ):
    """(low, high) as shares, read from the 'a plausible range being 8 to 15 per cent' note in the civilisation's source."""
    found = re.search(r"range being (\d+(?:\.\d+)?) to (\d+(?:\.\d+)?) per cent", civ["_internal"]["cast"]["source"])
    if not found:
        raise AssertionError("rome_100ad's cast source no longer states a range in per cent: the validation has nothing to read")
    return float(found.group(1)) / 100.0, float(found.group(2)) / 100.0


def bonded_share(strata):
    """(share of all members that are bonded, bonded members, all members) over stratum actors."""
    strata = list(strata)
    total = sum(stratum.record.members for stratum in strata)
    bonded = sum(stratum.record.members for stratum in strata if stratum.is_bonded())
    return (bonded / total if total > 0.0 else 0.0), bonded, total


def within(share, low, high):
    return low <= share <= high


@functools.lru_cache(maxsize=None)
def played(seed):
    """A game of Rome played YEARS market years; its starting and ending shares, and the supply side's counts."""
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(seed), events=False, manual=True, civ=load_civ("rome_100ad"))
    game.done_year = {}
    start = bonded_share(game.actors.of_kind("stratum"))
    bought, outcomes_seen = 0.0, []
    for _year in range(YEARS):
        game._step_market()
        latest = list(game.economy.agent.outcomes)[-1]
        if not any(latest is seen for seen in outcomes_seen):
            outcomes_seen.append(latest)           # a year the economy really ran leaves its own outcome
            bought += sum(latest.bonded_bought.values())
    events = [event for event in game.state.economy.world_events if event.get("kind") == "captives"]
    return {"start": start, "end": bonded_share(game.actors.of_kind("stratum")), "years": len(outcomes_seen),
            "bought": bought, "captives": sum(event.get("people", 0.0) for event in events)}


class RangeRule(unittest.TestCase):
    """The check itself, on numbers, so it is seen to be able to fail."""

    def test_a_share_outside_the_range_fails(self):
        self.assertFalse(within(0.02, 0.08, 0.15))
        self.assertFalse(within(0.30, 0.08, 0.15))
        self.assertTrue(within(0.10, 0.08, 0.15))

    def test_the_share_is_read_from_the_strata(self):
        class Stub:
            def __init__(self, members, bonded):
                self.record = type("Record", (), {"members": members})()
                self._bonded = bonded

            def is_bonded(self):
                return self._bonded
        self.assertAlmostEqual(bonded_share([Stub(90.0, False), Stub(10.0, True)])[0], 0.10)
        self.assertEqual(bonded_share([])[0], 0.0)


class BaselineValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.low, cls.high = sourced_range(load_civ("rome_100ad"))

    def check_seed(self, seed):
        result = played(seed)
        share, bonded, total = result["end"]
        print("rome_100ad seed %d: bonded share %.4f at start, %.4f after %d years (%.0f of %.0f); bought %.1f, captives %.1f"
              % (seed, result["start"][0], share, result["years"], bonded, total, result["bought"], result["captives"]))
        self.assertGreater(total, 0.0, "baseline validation, Complaint 648: the game holds no people")
        self.assertGreater(bonded, 0.0, "baseline validation, Complaint 648: the bonded stratum went empty")
        self.assertEqual(result["years"], YEARS, "baseline validation, Complaint 648: the years were not played")
        self.assertTrue(within(share, self.low, self.high),
                        "baseline validation, Complaint 648: bonded share %.4f outside the sourced range %.2f to %.2f (Scheidel 2005)"
                        % (share, self.low, self.high))

    def test_validation_seed_1(self):
        self.check_seed(SEEDS[0])

    def test_validation_seed_2(self):
        self.check_seed(SEEDS[1])

    def test_validation_seed_3(self):
        self.check_seed(SEEDS[2])

    def test_validation_the_seeds_are_distinct_and_several(self):
        self.assertGreaterEqual(len(set(SEEDS)), 3)


if __name__ == "__main__":
    unittest.main()
