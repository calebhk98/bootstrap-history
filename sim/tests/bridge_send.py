"""Give a stand-in game a `send` that applies commands the way the engine bridge does (and the
reporting commands as reporting does), for tests of code that still sends
to owners that have not moved (`ModEffects` sends `TransferTile`, `RecordWorldEvent` and `WriteStore`)."""
from typing import Any

from sim.engine import bridge, bridge_campaigns  # noqa: F401  (importing the bridge file registers its commands)
from sim.tests import event_stand_in


def attach_send(game: Any) -> Any:
	"""`game.send(command)` applies the command's bridge handler to `game`; returns the game."""
	applying = bridge.EngineBridge()
	applying.sim = game

	def send(command: Any) -> Any:
		applier = getattr(applying, "apply_" + type(command).__name__, None)
		return applier(command) if applier is not None else event_stand_in.send(game, command)   # reporting's own
	game.send = send
	return game
