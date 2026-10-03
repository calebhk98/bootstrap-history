"""The only door into sim/labour/: what code outside the package may import.

The mixins load on first use (module `__getattr__`): the engine data modules import this door
for the wage constants while they are themselves still loading, and the mixins import them back.
"""
from . import wage_provider, wages
from .labour_market import production_data
from .wage_provider import build_schedule, people_fed_per_worker
from .wages import CAREER_YEARS, HOURS_PER_WORKER_YEAR

__all__ = [
    "wage_provider", "wages", "LabourMixin", "LabourAllocationMixin", "production_data",
    "build_schedule", "people_fed_per_worker", "CAREER_YEARS", "HOURS_PER_WORKER_YEAR",
]


def __getattr__(name):
    if name == "LabourMixin":
        from .labour import LabourMixin
        return LabourMixin
    if name == "LabourAllocationMixin":
        from .labour_allocation import LabourAllocationMixin
        return LabourAllocationMixin
    raise AttributeError(name)
