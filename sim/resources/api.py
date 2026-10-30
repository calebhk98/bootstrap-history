"""The resources package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the legacy state it still needs

from .catalogue import base_mine_catalog_hint
from .commands import (BuyForest, CloseMine, DrawDeposit, FellTimber, LayNitreBeds, AutoMothballMines, MothballMines, NoteMineCostPaid, OpenMine,
                       Prospect, RegrowTimber)
from .deposit_history import historical_rates
from .state import ResourcesSeat, ResourcesWorld
from .labour_profile import mine_labour_hours_per_tonne
from . import ceilings, constants, rules, sizing
