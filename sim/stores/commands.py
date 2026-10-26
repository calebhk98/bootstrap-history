"""Commands to the owner of the declared key/value stores."""
from dataclasses import dataclass
from typing import Any

from sim.assembly.api import Command


@dataclass(frozen=True)
class WriteStore(Command):
	"""Set the value of `key` in the declared store `store` (the default value clears the entry). `owner` is the mod
	writing, empty for the base game; a mod may write only a store it declared."""
	store: str
	key: Any
	value: Any
	owner: str = ""
