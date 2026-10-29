"""The knowledge package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the legacy state it still needs

from .commands import (ForgetTechnique, HandOverTechniques, LearnTechnique, ReceiveTechniques, RevealFrom, RevealNodes,
                       StartDoneYearRecord, ReplaceTree)
from .constants import CORPUS_HEDGE_FRACTION_LOST_NONE, CORPUS_HEDGE_LOSS_CHANCE_NONE
from .fog_words import (FOG_KIND_HINTS, FREE_PREREQ_NAMED_AT_MOST, HIDDEN_ID_PLACEHOLDER, free_prereq_hint,
                        hidden_prerequisite_kinds, missing_prereq_message, prerequisite_label, prerequisite_names,
                        scrub_hidden_ids, strip_self_play_advice, summary_sentence)
from .category_traits import check_category_traits
from .save_fog import fog_mismatch
from .starting_techs import declared_starting_techs
from .state import KnowledgeSeat
from .tree_paths import closure, critical_path, hard_pre, topo_order
from . import rules
