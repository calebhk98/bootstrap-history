"""The projects package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the legacy state it still needs

from .commands import Bribe, PostBounty, StartProject, StopProject
from .needed_commands import (ChangeStanding, ClearMothball, CompleteProject, NoteSpend, RecordAutomation,
                              RecordAutomationSkip, RecordEvent, SettleProjectMaterials)
from .blocker_rules import BLOCKER_KINDS, BLOCKER_MEANING, RUNNING_CONSTRAINT_KIND, START_CHECKS
from .training_words import training_advice_text
from . import (auto_start, blocker_rules, bribe_rules, constants, funding, instantaneous, phase_rules, record_rules,
               staff_gate, start_money, start_rules)
