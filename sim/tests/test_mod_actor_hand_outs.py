"""What the actors module hands a mod's code: an actor class runs inside the agents package and is handed the world narrowed to
what actors ask (`UndeclaredWorldMember` for any other member, naming the mod); a spawner and a player command are handed the
mod's `ModAccess`, never the registry, the player object or the world. Each test calls one function on toy classes and a toy
assembly, no game."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.assembly.api import LIST, ExtensionPoint, Module, ModuleSpec, UndeclaredRead, UndeclaredWorldMember, assemble
from sim.content.api import ModError
from sim.engine.mod_code import ModCodeApi, narrow_actor_class
from sim.tests.assembly_fixture import BASE, TOP

MOD = "test_acme_u8w3"
MOD_MODULE = "sim_mod.%s.hooks" % MOD


class ShippedBase:
	"""Stands for a shipped actor class: defined outside the mod, so it is not narrowed itself."""
	kind = "shipped"

	def advance(self, world):
		return ("shipped", world.edge("landowners"))


def mod_class(body_edge="thieves"):
	class Holder(ShippedBase):
		__module__ = MOD_MODULE
		kind = MOD + ":holder"

		def advance(self, world):
			return ("mod", world.edge(body_edge), super().advance(world))

		def peek(self, world):
			return world.registry

		def named(self, *, world):
			return world.year

		def helper(self, count):
			return count + 1
	return Holder


class World:
	registry = "the live registry"
	year = 1300

	def edge(self, name):
		return "edge " + name


class NarrowActorClassTests(unittest.TestCase):
	def test_a_member_the_protocol_names_answers_in_the_mods_method_and_in_the_shipped_one_it_calls(self):
		holder = narrow_actor_class(mod_class(), MOD)()
		self.assertEqual(holder.advance(World()), ("mod", "edge thieves", ("shipped", "edge landowners")))

	def test_any_other_member_is_refused_naming_the_mod_and_the_member(self):
		holder = narrow_actor_class(mod_class(), MOD)()
		with self.assertRaises(UndeclaredWorldMember) as caught:
			holder.peek(World())
		self.assertEqual((caught.exception.mod_id, caught.exception.view), (MOD, "registry"))
		self.assertIsInstance(caught.exception, UndeclaredRead)

	def test_a_world_given_by_keyword_is_narrowed_too(self):
		holder = narrow_actor_class(mod_class(), MOD)()
		self.assertEqual(holder.named(world=World()), 1300)

	def test_a_method_without_a_world_is_untouched(self):
		self.assertEqual(narrow_actor_class(mod_class(), MOD)().helper(2), 3)

	def test_the_shipped_class_the_mod_extends_is_left_as_it_was(self):
		narrow_actor_class(mod_class(), MOD)
		self.assertEqual(ShippedBase().advance(World()), ("shipped", "edge landowners"))
		self.assertEqual(ShippedBase.advance.__module__, __name__)

	def test_narrowing_a_class_twice_wraps_it_once(self):
		holder_class = mod_class()
		narrow_actor_class(holder_class, MOD)
		narrow_actor_class(holder_class, MOD)
		self.assertEqual(holder_class().advance(World()), ("mod", "edge thieves", ("shipped", "edge landowners")))


class Owner(Module):
	pass


POINTS = ModuleSpec("owner", Owner, extension_points=tuple(ExtensionPoint(name, LIST) for name in ("actor_spawners", "player_commands")))


def provided_game(register):
	api = ModCodeApi(MOD)
	register(api)
	return assemble([BASE, TOP, POINTS], [api.operations])


class SpawnerTests(unittest.TestCase):
	def test_the_spawner_is_called_with_its_mods_access_and_nothing_of_the_actors_module(self):
		received = []
		game = provided_game(lambda api: api.spawner("found", lambda *arguments: received.append(arguments)))
		((name, spawner),) = game.points["actor_spawners"]()[0]
		spawner("the registry", "the world")
		self.assertEqual((name, received), (MOD + ":found", [(game.mod_access[MOD],)]))

	def test_a_spawner_cannot_read_what_its_mod_did_not_declare(self):
		game = provided_game(lambda api: api.spawner("found", lambda access: access.view("double")()))
		((_name, spawner),) = game.points["actor_spawners"]()[0]
		with self.assertRaises(UndeclaredRead) as caught:
			spawner("the registry", "the world")
		self.assertEqual((caught.exception.mod_id, caught.exception.view), (MOD, "double"))


class ProvideTests(unittest.TestCase):
	def test_providing_straight_to_a_point_that_has_a_typed_call_is_refused_naming_the_mod_and_the_call(self):
		for point, call in (("actor_kinds", "actor_kind"), ("actor_spawners", "spawner"), ("player_commands", "player_command")):
			with self.assertRaises(ModError) as caught:
				ModCodeApi(MOD).provide(point, lambda: None)
			self.assertIn(MOD, str(caught.exception))   # presentation: the refusal names the mod and the call to use
			self.assertIn("api." + call, str(caught.exception))


class PlayerCommandTests(unittest.TestCase):
	def test_the_handler_is_called_with_the_access_the_players_id_and_the_order(self):
		received = []
		game = provided_game(lambda api: api.player_command("bless", lambda *arguments: received.append(arguments) or "blessed"))
		(table,) = game.points["player_commands"]()
		detail = table[MOD + ":bless"](SimpleNamespace(actor_id="player:1"), {"command": "bless", "tile": "t1"}, "the world")
		self.assertEqual(detail, "blessed")
		self.assertEqual(received, [(game.mod_access[MOD], "player:1", {"command": "bless", "tile": "t1"})])

	def test_a_handler_cannot_read_what_its_mod_did_not_declare(self):
		game = provided_game(lambda api: api.player_command("bless", lambda access, actor_id, order: access.view("double")()))
		(table,) = game.points["player_commands"]()
		with self.assertRaises(UndeclaredRead):
			table[MOD + ":bless"](SimpleNamespace(actor_id="player:1"), {}, "the world")


if __name__ == "__main__":
	unittest.main()
