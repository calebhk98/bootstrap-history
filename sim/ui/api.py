"""The UI's only door: code outside sim/ui/ imports from here, never from a submodule.

The presentation constants load eagerly: tools that run while the engine is still importing
(treetool, through the tree build) need them. The protocol and command names load on first use,
because importing them pulls in the engine.
"""
import importlib
from typing import TYPE_CHECKING

from sim.ui.presentation import (  # noqa: F401
    MERGE_ERRORS_SHOWN, MERGE_WARNINGS_SHOWN,
    JUDGE_UNOBTAINABLE_DEPENDENCIES_SHOWN, JUDGE_NEAR_MATCH_SUGGESTIONS_SHOWN,
    JUDGE_WORST_NODES_SHOWN, JUDGE_NODE_ID_COLUMN_WIDTH_CHARS,
    JUDGE_DEFECT_CODES_SHOWN, APPLY_CAPS_SAMPLE_SHOWN,
    APPLY_CAPS_PREREQ_LIST_TRUNCATE_CHARS, APPLY_CAPS_REASON_TRUNCATE_CHARS,
    AUDIT_BAR_WIDTH_CHARS, AUDIT_UNPRICED_MATERIALS_SHOWN,
    AUDIT_RECIPE_LIST_TRUNCATE_CHARS)

_PROTOCOL_NAMES = (
    "_agent_available", "_agent_dispatch", "_agent_end_reason", "_agent_help", "_agent_state",
    "_waiting_on", "_brief", "_clean", "_flag", "_full_entry", "_node_explain", "_num",
    "_subject_of", "load_state", "save_state", "SAVE_FIELDS", "SUBJECTS", "HELP_TOPICS",
    "KNOWN_COMMANDS")
_CLI_NAMES = (
    "cmd_agent", "cmd_civs", "cmd_compare", "cmd_costs", "cmd_goals", "cmd_path", "cmd_plan",
    "cmd_play", "cmd_run", "cmd_search", "cmd_sensitivity", "cmd_sweep", "cmd_validate",
    "cmd_why", "cmd_menu", "load_strategy", "main", "topo_stable", "_summarise", "DetRNG",
    "ensure_fixed_hash_seed")

if TYPE_CHECKING:  # names for static readers; at run time they load through __getattr__
    from sim.ui.protocol import (  # noqa: F401
        _agent_available, _agent_dispatch, _agent_end_reason, _agent_help, _agent_state,
        _waiting_on, _brief, _clean, _flag, _full_entry, _node_explain, _num,
        _subject_of, load_state, save_state, SAVE_FIELDS, SUBJECTS, HELP_TOPICS,
        KNOWN_COMMANDS)
    from sim.ui.cli import (  # noqa: F401
        cmd_agent, cmd_civs, cmd_compare, cmd_costs, cmd_goals, cmd_path, cmd_plan,
        cmd_play, cmd_run, cmd_search, cmd_sensitivity, cmd_sweep, cmd_validate,
        cmd_why, cmd_menu, load_strategy, main, topo_stable, _summarise, DetRNG,
        ensure_fixed_hash_seed)


def __getattr__(name):
    for module_name, names in (("sim.ui.protocol", _PROTOCOL_NAMES), ("sim.ui.cli", _CLI_NAMES)):
        if name in names:
            return getattr(importlib.import_module(module_name), name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))
