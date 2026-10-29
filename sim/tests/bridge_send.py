"""Give a stand-in game a `send` that applies commands the way the engine bridge does (the world event log as the hazards
module does, and the reporting commands as reporting does), for tests of code that still sends to owners that have not
moved (`ModEffects` sends `RecordWorldEvent`; a `WriteStore` goes to the game's `stores_module`). The log is read back through
`game.world_event_log` (the hazards module over a fresh world)."""
from typing import Any

from sim.engine import bridge  # noqa: F401
from sim.hazards.api import RecordWorldEvent
from sim.stores.api import WriteStore
from sim.tests import event_stand_in, hazards_host


def attach_send(game: Any) -> Any:
	"""`game.send(command)` applies the command's bridge handler to `game`; returns the game."""
	applying = bridge.EngineBridge()
	applying.sim = game
	game.world_event_log = hazards_host.build(year=lambda: game.state.scenario.year)

	def send(command: Any) -> Any:
		if isinstance(command, RecordWorldEvent):
			return game.world_event_log.record_world_event(command)
		if isinstance(command, WriteStore):
			return game.stores_module.write_store(command)
		applier = getattr(applying, "apply_" + type(command).__name__, None)
		return applier(command) if applier is not None else event_stand_in.send(game, command)   # reporting's own
	game.send = send
	return game
