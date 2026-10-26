"""The materials package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the legacy state it still needs

from .commands import ApplyThrottle, CaptureReadings, ForgetReadings, RestoreReadings, SettleProjectMaterials
from .state import MaterialsSeat
from .capacity import (DEFAULT_MARKET_SHARE_OF_CAPACITY, ProducerCapacityCache, mined_capacity_tonnes,
                       producer_capacity_tonnes, producer_units_by_material)
from . import constants, rules
