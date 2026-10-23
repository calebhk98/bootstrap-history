"""A save says what game it is. A save played without fog is refused by a fogged game (`save_fog_mismatch`), the fog flag
survives a save and load, resuming `play --session` needs no --civ and a contradicting --civ is refused (`_civ_for_session`).
Each rule is called on inputs built here: no game, no command line."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from sim.engine.save_fog import fog_mismatch
from sim.engine.state import (EconomyState, FounderState, GovernanceState, HoldingsState, HouseholdState, PopulationState,
                              ProjectsState, ScenarioState, SimulationState, deserialize_state, serialize_state)
from sim.refusal import cause_of
from sim.ui.cli import _civ_for_session

QUICK_TOPIC = True


class FogMismatch(unittest.TestCase):

    def test_a_fogged_game_refuses_a_save_played_without_fog(self):
        self.assertEqual(cause_of(fog_mismatch(True, False)), "save_fog_mismatch")

    def test_a_game_without_fog_accepts_any_save(self):
        self.assertIsNone(fog_mismatch(False, False))
        self.assertIsNone(fog_mismatch(False, True))

    def test_a_fogged_game_accepts_a_fogged_save_and_one_that_does_not_say(self):
        self.assertIsNone(fog_mismatch(True, True))
        self.assertIsNone(fog_mismatch(True, None))


def state_with(fog):
    state = SimulationState(
        household=HouseholdState(capital=1.0), projects=ProjectsState(), economy=EconomyState(), holdings=HoldingsState(),
        governance=GovernanceState(), founder=FounderState(), scenario=ScenarioState(year=1302), population=PopulationState())
    state._fog, state._civ = fog, "england_1300"
    return state


class SavedFlags(unittest.TestCase):

    def test_the_fog_flag_and_the_civilisation_survive_a_save_and_load(self):
        loaded = deserialize_state(json.loads(json.dumps(serialize_state(state_with(True)))))
        self.assertIs(loaded._fog, True)
        self.assertEqual(loaded._civ, "england_1300")

    def test_a_save_without_fog_loads_as_without_fog(self):
        loaded = deserialize_state(json.loads(json.dumps(serialize_state(state_with(False)))))
        self.assertIs(loaded._fog, False)


class CivilisationOfASession(unittest.TestCase):

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.saved = os.path.join(folder.name, "save.json")
        with open(self.saved, "w") as handle:
            json.dump({"_civ": "england_1300"}, handle)
        self.empty = os.path.join(folder.name, "claimed.json")
        open(self.empty, "w").close()

    def args(self, session, civ=None):
        return SimpleNamespace(session=session, civ=civ)

    def test_a_save_resumes_without_being_told_which_game_it_is(self):
        self.assertEqual(_civ_for_session(self.args(self.saved)), "england_1300")

    def test_naming_the_saved_civilisation_is_fine(self):
        self.assertEqual(_civ_for_session(self.args(self.saved, "england_1300")), "england_1300")

    def test_a_contradicting_civilisation_is_refused_with_a_nonzero_exit(self):
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(io.StringIO()):
            _civ_for_session(self.args(self.saved, "rome_100ad"))
        self.assertEqual(raised.exception.code, 1)

    def test_a_claimed_empty_slot_is_a_new_game_of_the_civilisation_asked_for(self):
        self.assertEqual(_civ_for_session(self.args(self.empty, "han_china_100ad")), "han_china_100ad")

    def test_no_session_gives_the_civilisation_asked_for(self):
        self.assertEqual(_civ_for_session(self.args(None, "mexica_1500")), "mexica_1500")


if __name__ == "__main__":
    unittest.main()
