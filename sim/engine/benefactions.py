"""What the works of a very rich actor do beyond the effect channels: coverage, the working day and settled colonies (the
transfers, the levies and the state's legitimacy are the polity module's).

Each topic is its own small mixin; this file only composes them for `Sim`.
"""
from .colonies import ColoniesMixin
from .coverage import CoverageMixin
from .tile_ownership import TileOwnershipMixin


class BenefactionsMixin(CoverageMixin, ColoniesMixin, TileOwnershipMixin):
    pass
