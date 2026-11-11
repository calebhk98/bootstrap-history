"""`sheet_of` turns an actor into the plain facts a mod may read; `ModCodeApi.reads` refuses the actors module's live registry."""
import unittest
from types import SimpleNamespace

from sim.actors.actor_sheets import sheet_of
from sim.engine.mod_code import ModCodeApi
from sim.mod_errors import ModError

QUICK_TOPIC = True


class ActorSheetTests(unittest.TestCase):
    def test_sheet_is_plain_data(self):
        actor = SimpleNamespace(actor_id="holder:a", money=12.5, workforce={"clerk": 2.0, "guard": 1.0},
                                stance=SimpleNamespace(prominence=lambda: 0.25),
                                record=SimpleNamespace(kind="mod:holder", cause="holder looted"))
        self.assertEqual(sheet_of(actor), {"actor_id": "holder:a", "kind": "mod:holder", "money": 12.5, "headcount": 3.0,
                                           "prominence": 0.25, "cause": "holder looted"})

    def test_no_actor_has_no_sheet(self):
        self.assertIsNone(sheet_of(None))

    def test_a_mod_may_not_declare_the_live_registry(self):
        with self.assertRaises(ModError) as caught:
            ModCodeApi("probe_mod").reads("year", "cast")
        self.assertIn("probe_mod", str(caught.exception))
        self.assertIn("cast", str(caught.exception))

    def test_a_wealth_claim_seizer_is_given_the_takers_id_not_the_actor(self):
        api = ModCodeApi("probe_mod")
        api.wealth_claims(lambda access: 1.0, lambda access, amount, taker_id: (access, amount, taker_id))
        owed, seize = api.operations.provided["wealth_claims"][0].function("the access")
        self.assertEqual(seize(5.0, SimpleNamespace(actor_id="actor:t")), ("the access", 5.0, "actor:t"))


if __name__ == "__main__":
    unittest.main()
