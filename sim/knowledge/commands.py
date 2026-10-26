"""Commands to the owner of what each seat knows."""
from dataclasses import dataclass
from typing import Tuple

from sim.assembly.api import Command


@dataclass(frozen=True)
class ForgetTechniques(Command):
	"""The acting seat loses these techniques in `year`: no longer built, running or shut, and noted as forgotten so they
	can be built again. Every one is dropped before the seat's caches are told, once."""
	node_ids: Tuple[str, ...]
	year: int
