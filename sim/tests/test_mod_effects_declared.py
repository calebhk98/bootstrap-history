"""A mod's effects act through the mod's `ModAccess`: each effect sends the owner's command, so the mod must have declared that
command (`api.sends`) and the view it reads (`api.reads`); an undeclared one is refused naming the mod and the name. The
`ModAccess` is built over a stand-in assembly that records the commands it applies; each test calls one effect."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.actors.api import MoveStratumPeople
from sim.agents.api import edges
from sim.assembly.api import ModAccess, UndeclaredRead, UndeclaredSend
from sim.demography.api import KillPeople
from sim.content.api import ModError
from sim.engine.mod_code import ModCodeApi
from sim.engine.mod_effects import ModEffects
from sim.hazards.api import RecordWorldEvent
from sim.land.api import TransferTile
from sim.ledger.api import PayActor, PayActorFromEdge, PayEdgeFrom
from sim.markets.api import MoveGoods
from sim.stores.api import WriteStore

MOD = "test_acme_t5v1"
effects = ModEffects(MOD)


class StandInView:
	def __init__(self, name, answer):
		self.spec = SimpleNamespace(name=name)
		self._answer = answer

	def __call__(self, *arguments):
		return self._answer


def access(reads=(), sends=()):
	"""A mod's access over an assembly that answers the cast and records what is sent."""
	sent = []
	cast = SimpleNamespace(get=lambda actor_id: object())
	handlers = {kind: (lambda command, kind=kind: sent.append(command) or {"moved": 1.0, "countries": ["home"]}) for kind in
	            (PayActor, PayEdgeFrom, PayActorFromEdge, MoveGoods, KillPeople, MoveStratumPeople, TransferTile, WriteStore, RecordWorldEvent)}
	assembly = SimpleNamespace(views={"cast": StandInView("cast", cast)}, handlers=handlers)
	return ModAccess(assembly, MOD, frozenset(reads), frozenset(sends)), sent


class DeclaredSendsAreRequired(unittest.TestCase):
	def refused_send(self, call, command):
		given, sent = access(reads=("cast",))
		with self.assertRaises(UndeclaredSend) as caught:
			call(given)
		self.assertEqual((caught.exception.mod_id, caught.exception.command), (MOD, command.__name__))
		self.assertEqual(sent, [])

	def test_pay_needs_PayActor(self):
		self.refused_send(lambda given: effects.pay(given, "a", "b", 1.0, "a gift"), PayActor)

	def test_pay_edge_needs_PayEdgeFrom(self):
		self.refused_send(lambda given: effects.pay_edge(given, "a", edges.EDGE_OFFICIALS, 1.0, "a bribe"), PayEdgeFrom)

	def test_receive_from_edge_needs_PayActorFromEdge(self):
		self.refused_send(lambda given: effects.receive_from_edge(given, "a", edges.EDGE_OFFICIALS, 1.0, "a refund"), PayActorFromEdge)

	def test_add_goods_needs_MoveGoods(self):
		self.refused_send(lambda given: effects.add_goods(given, "account", "grain", "tile", 1.0, "a gift"), MoveGoods)

	def test_remove_goods_needs_MoveGoods(self):
		self.refused_send(lambda given: effects.remove_goods(given, "account", "grain", "tile", 1.0, "a fire"), MoveGoods)

	def test_kill_people_needs_KillPeople(self):
		self.refused_send(lambda given: effects.kill_people(given, "home", 0.1, "a curse"), KillPeople)

	def test_move_people_needs_MoveStratumPeople(self):
		self.refused_send(lambda given: effects.move_people(given, "stratum:a", "stratum:b", 1.0, "a reform"), MoveStratumPeople)

	def test_transfer_tile_needs_TransferTile(self):
		self.refused_send(lambda given: effects.transfer_tile(given, "tile", "home", "a treaty"), TransferTile)

	def test_write_store_needs_WriteStore(self):
		self.refused_send(lambda given: effects.write_store(given, MOD + ":mana", "tile", 1.0), WriteStore)

	def test_record_event_needs_RecordWorldEvent(self):
		self.refused_send(lambda given: effects.record_event(given, "omen", "a comet"), RecordWorldEvent)


class DeclaredReadsAreRequired(unittest.TestCase):
	def test_pay_reads_the_cast_so_the_mod_declares_it(self):
		given, sent = access(sends=(PayActor,))
		with self.assertRaises(UndeclaredRead) as caught:
			effects.pay(given, "a", "b", 1.0, "a gift")
		self.assertEqual((caught.exception.mod_id, caught.exception.view), (MOD, "cast"))
		self.assertEqual(sent, [])


class DeclaredEffectsReachTheOwner(unittest.TestCase):
	def test_a_declared_payment_is_the_owners_command(self):
		given, sent = access(reads=("cast",), sends=(PayActor,))
		effects.pay(given, "a", "b", 2.0, "a gift")
		self.assertEqual(sent, [PayActor("a", "b", 2.0, "a gift")])

	def test_declared_goods_are_the_markets_move_from_the_named_edge(self):
		given, sent = access(sends=(MoveGoods,))
		effects.add_goods(given, "account", "grain", "tile", 5.0, "a gift")
		effects.remove_goods(given, "account", "grain", "tile", 2.0, "a fire")
		self.assertEqual([(move.giver, move.receiver, move.quantity) for move in sent],
		                 [("edge:production", "account", 5.0), ("account", "edge:consumption", 2.0)])

	def test_a_declared_move_of_people_is_the_actors_command_and_the_event_follows(self):
		given, sent = access(sends=(MoveStratumPeople, RecordWorldEvent))
		effects.move_people(given, "stratum:a", "stratum:b", 3.0, "a reform")
		self.assertEqual(sent[0], MoveStratumPeople("stratum:a", "stratum:b", 3.0))
		self.assertEqual((sent[1].kind, sent[1].cause), (MOD + ":people_moved", "a reform"))


class UsesEffects(unittest.TestCase):
	def test_naming_an_effect_declares_the_view_and_the_command_it_needs(self):
		api = ModCodeApi(MOD)
		api.uses_effects("pay", "kill_people")
		self.assertEqual((api.operations.reads, api.operations.sends), (("cast",), (PayActor, KillPeople)))

	def test_an_effect_that_does_not_exist_is_refused_naming_the_mod(self):
		with self.assertRaises(ModError) as caught:
			ModCodeApi(MOD).uses_effects("conjure")
		self.assertIn(MOD, str(caught.exception))   # presentation: the refusal names the mod and the effect
		self.assertIn("conjure", str(caught.exception))


if __name__ == "__main__":
	unittest.main()
