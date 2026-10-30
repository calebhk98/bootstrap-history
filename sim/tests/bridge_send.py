"""Give a stand-in game a `send` that applies the commands mod effects send (the world event log as the hazards module does, a
`WriteStore` as the stores module does, the reporting commands as reporting does), for tests of `ModEffects` (it sends
`RecordWorldEvent`). The log is read back through `game.world_event_log` (the hazards module over a fresh world)."""
from typing import Any

from sim.hazards.api import RecordWorldEvent
from sim.stores.api import WriteStore
from sim.tests import event_stand_in, hazards_host


def attach_send(game: Any) -> Any:
	"""`game.send(command)` applies the command as its owner does; returns the game."""
	game.world_event_log = hazards_host.build(year=lambda: game.state.scenario.year)

	def send(command: Any) -> Any:
		if isinstance(command, RecordWorldEvent):
			return game.world_event_log.record_world_event(command)
		if isinstance(command, WriteStore):
			return game.stores_module.write_store(command)
		return event_stand_in.send(game, command)   # reporting's own
	game.send = send
	return game
