"""What the works of a very rich actor do beyond the effect channels: coverage (the transfers, the levies and the state's
standing are the polity module's; settled colonies and who holds each tile are the land module's).

Each topic is its own small mixin; this file only composes them for `Sim`.
"""
from .coverage import CoverageMixin


class BenefactionsMixin(CoverageMixin):
    pass
