"""Commands to the owner of debt and the capital market (finance, not moved yet: the bridge applies them)."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class RefreshLenderOffers(Command):
	"""The year's meeting of lenders: the pool pays the interest it holds, then who offers what is fixed."""


@dataclass(frozen=True)
class DefaultOnDebt(Command):
	"""The acting seat's household defaults on its debt in `year`."""
	year: int
