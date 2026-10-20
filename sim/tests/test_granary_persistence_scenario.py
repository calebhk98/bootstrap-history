"""Scenario (Complaint 640): the granary stock round-trips through a save and a load, and a save without it is refused
(CLAUDE.md 4.6: within a build, `--session` makes every command a save then a load). The granary rules are in
test_granary_persistence.py."""
import unittest

from .harness import *  # noqa: F401,F403


def _rome_sim(events=False):
    return sim(civ="rome_100ad", events=events)


class SaveLoadRoundTripTests(unittest.TestCase):
    """CLAUDE.md SS3.5: no save-format migration, ever - but round-tripping
    WITHIN a build is not optional, and `--session` makes every command a
    save and a load, so a field that does not round-trip breaks ordinary
    play immediately, not just a hypothetical resume.
    """

    def test_farm_stock_kg_round_trips_through_save_and_load(self):
        import tempfile, os
        from sim.engine import saveload as S

        test_sim = _rome_sim(events=False)
        for year in range(101, 111):
            test_sim._demographic_recovery(year)
        before = test_sim.farm_stock_kg
        self.assertNotEqual(before, 0.0, "expected a nonzero granary after "
                            "ten years - otherwise this test is not "
                            "actually exercising round-trip of a moved "
                            "value")

        path = tempfile.mktemp(suffix=".json")
        try:
            S.save_state(test_sim, path)
            fresh = _rome_sim(events=False)
            self.assertEqual(fresh.farm_stock_kg, 0.0,
                             "a freshly constructed Sim's own initial "
                             "condition - if this ever changes, the "
                             "assertion below proves nothing")
            S.load_state(fresh, path)
            self.assertEqual(fresh.farm_stock_kg, before)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_a_save_missing_farm_stock_kg_is_refused_not_silently_defaulted(self):
        # CLAUDE.md SS3.5's own rule: no upgrade path, no `if "old_key" in
        # data`. An old save simply does not load - see saveload.py's own
        # comment on REQUIRED_SAVE_FIELDS for why silently accepting a
        # partial shape is worse than refusing the file outright.
        import tempfile, os, json
        from sim.engine import saveload as S

        test_sim = _rome_sim(events=False)
        path = tempfile.mktemp(suffix=".json")
        try:
            S.save_state(test_sim, path)
            with open(path) as handle:
                blob = json.load(handle)
            if "farm_stock_kg" in blob:
                del blob["farm_stock_kg"]
            else:
                del blob["economy"]
            with open(path, "w") as handle:
                json.dump(blob, handle)
            fresh = _rome_sim(events=False)
            with self.assertRaises(ValueError):
                S.load_state(fresh, path)
        finally:
            if os.path.exists(path):
                os.remove(path)



if __name__ == "__main__":
    unittest.main()
