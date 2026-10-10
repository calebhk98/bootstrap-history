"""What the works of a very rich actor do beyond the effect channels: one-off transfers, levies, coverage, relief,
legitimacy, the working day and settled colonies.

Each topic is its own small mixin; this file only composes them for `Sim`.
"""
from .colonies import ColoniesMixin
from .concern_levy import ConcernLevyMixin
from .coverage import CoverageMixin
from .food_relief import FoodReliefMixin
from .legitimacy import LegitimacyMixin
from .transfers import TransfersMixin
from .working_day import WorkingDayMixin


class BenefactionsMixin(TransfersMixin, ConcernLevyMixin, CoverageMixin, FoodReliefMixin, LegitimacyMixin,
                        WorkingDayMixin, ColoniesMixin):
    pass
