"""The interface module's command: what the game hands it that only the engine can answer."""
from dataclasses import dataclass
from typing import Callable

from sim.assembly.api import Command


@dataclass(frozen=True)
class OpenInterface(Command):
	"""Hand over the rule that says whether a data file may read a state path: `check_state_path(state_path, where)` raises
	`ModError` when it may not. Sent once, when the game's assembly is built."""
	check_state_path: Callable[[str, str], None]
