"""The content module's command: which mods directory the game is over."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class OpenContent(Command):
	"""Name the directory whose mods this game is built over. Sent once, when the game's assembly is built."""
	directory: str
