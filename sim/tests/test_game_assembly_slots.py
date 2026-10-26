"""A module's world and seat state enters a game's saved state, survives a save, and a save from another module set is
refused. Each test calls one function of sim/engine/game_assembly.py on a hand-built state; no game is built."""

QUICK_TOPIC = True

import types
import unittest
from dataclasses import dataclass, field
from typing import Dict

from sim.assembly.api import Module, ModuleSpec, Operations, assemble, record
from sim.engine import game_assembly
from sim.engine.state import FounderState, HouseholdState, ProjectsState, SimulationState, deserialize_state, serialize_state
from sim.refusal import cause_of


@dataclass
class HerdWorld:
	wild_head: Dict[str, float] = field(default_factory=dict)


@dataclass
class HerdSeat:
	held_head: float = 0.0


class Herds(Module):
	pass


HERDS = ModuleSpec("herds", Herds, world_state=HerdWorld, seat_state=HerdSeat)


def _game(operations=()):
	state = SimulationState(household=HouseholdState(capital=1.0), projects=ProjectsState(), founder=FounderState())
	return types.SimpleNamespace(assembly=assemble([HERDS], operations), state=state)


class AttachTests(unittest.TestCase):
	def test_a_new_game_gets_fresh_world_and_seat_slots_and_the_module_is_pointed_at_them(self):
		game = _game()
		game_assembly.attach(game)
		module = game.assembly.modules["herds"]
		self.assertIs(module.world, game.state.modules["herds"])
		self.assertIs(module.seat, game.state.seats[game.state.acting_seat].modules["herds"])
		self.assertEqual(game.state.assembly_record, record(game.assembly))


class ReviveTests(unittest.TestCase):
	def test_module_state_survives_a_save_as_its_own_dataclass(self):
		game = _game()
		game_assembly.attach(game)
		game.state.modules["herds"].wild_head["goat"] = 40.0
		game.state.seats[game.state.acting_seat].modules["herds"].held_head = 7.0
		loaded = deserialize_state(serialize_state(game.state))
		game_assembly.revive(game, loaded, deserialize_state)
		self.assertEqual(loaded.modules["herds"], HerdWorld(wild_head={"goat": 40.0}))
		self.assertEqual(loaded.seats[loaded.acting_seat].modules["herds"], HerdSeat(held_head=7.0))

	def test_a_save_from_another_module_set_is_refused_with_a_cause(self):
		writer = _game()
		game_assembly.attach(writer)
		loaded = deserialize_state(serialize_state(writer.state))
		reader = _game([Operations("ana_test_k3f9", removed=("herds",))])
		with self.assertRaises(ValueError) as raised:
			game_assembly.revive(reader, loaded, deserialize_state)
		self.assertEqual(cause_of(raised.exception.args[0]), "save_module_set")


if __name__ == "__main__":
	unittest.main()
