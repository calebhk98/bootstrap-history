"""The JSON protocol a player or an agent speaks.

One object per line in, one object per line out. It explains itself: there is
no protocol document to read, on purpose.

This file is a thin re-export shim over engine/proto/ - see that package
and sim/ARCHITECTURE.md - kept so that `from engine.protocol import X`
goes on working for every name this module ever exported. Nothing below
is logic; read engine/proto/ for that.
"""

from .proto.util import (
    _factor, _fmt_num, _fmt_range, _pct, _wrap, DISPLAY_WIDTH,
    DEFAULT_AVAILABLE_LIMIT, SAVE_SUFFIXES, _unsafe_path, _qty, _num, _clean,
    _flag, _MONEY_RE, _localise_words, _localise_money
)
from .proto.nodes import (
    _NODES_ONCE, NODE_IDS, NODE_IDS_LOWER, _norm_name, NODE_NAME_NORM,
    _resolve_by_name, _downstream_of, _unlocked_by_cache, _unlocked_by_index,
    _unlocked_by, _did_you_mean
)
from .proto.ventures import (
    _VENTURE_SUPERVISION_NOTE
)
from .proto.state import (
    _agent_end_reason, _risk_without_the_essays, _staff_fraction_note,
    _waiting_on, _goal_progress_count, _founder_death_info,
    _worth_knowing_early, _agent_state, _FAILURE_MARKERS, _is_failure_line,
    _log_scrub, _agent_log
)
from .proto.score import (
    final_report, SCORE_WEIGHTS, _score_goal_floor_years, _score_components,
    _score_achievements, score_report, _SCORE_COMPONENT_ORDER, _score_lines
)
from .proto.techtree import (
    SUBJECTS, _subject_of, _staff_short, _short_of_staff, _staff_fields,
    _coarse_round, _revenue_known_exactly, _fog_revenue_estimate, _brief,
    _full_entry, _SORT_KEYS, _SORT_KEY_NAMES, _agent_available, _rests_band,
    _node_explain
)
from .proto.economy import (
    _VALUE_MEANINGS, _agent_values, _material_capacity_rows, _POWER_LADDER,
    _power_status, _agent_mines, _portfolio_constraint, _PORTFOLIO_ORDER,
    _portfolio_rows, _spare_capacity, _trade_demand_rows, _agent_portfolio,
    _agent_capacity, _dashboard_snapshot, _agent_economy, _agent_changes
)
from .proto.help import (
    HELP_TOPICS, _agent_help
)
from .proto.saveload import (
    SAVE_FIELDS, save_state, REQUIRED_SAVE_FIELDS, _SET_FIELDS_OF_NODE_IDS,
    _SET_FIELDS_OF_TRADE_NAMES, _validate_save, civ_of_save, goal_of_save,
    load_state
)
from .proto.render import (
    render_values, render_capacity, render_portfolio, render_economy,
    render_changes, render_final, render_score, render_error, render_state,
    _RESTS_SHORT, _cost_marker, _available_row, render_available, render_why,
    render_step, render_money, render_stuck, render_mines, render_labour,
    render_population, render_ventures, render_risk, _advice_line,
    render_generic, render_log, render_policy, render_rush, render_path,
    _RENDERERS, TYPED_HINTS, MONEY_SHORT, _typed_form, _JSON_HINT,
    _JSON_PAIR, _typed_deep, to_typed_hints, _DEN_RE, render_pretty
)
from .proto.typed import (
    TYPED_ALIASES, _typed_number, _absorb_key_colons, parse_typed
)
from .proto.dispatch import (
    KNOWN_COMMANDS, _ID_COMMANDS, _NAME_COMMANDS, _cmd_state, _cmd_available,
    _cmd_log, _cmd_score, _cmd_why, _cmd_path, _cmd_start, _cmd_stop,
    _cmd_rush, _cmd_bounty, _cmd_buy, _cmd_work, _cmd_allocate, _cmd_risk,
    _cmd_values, _cmd_money, _cmd_stuck, _cmd_mines, _cmd_capacity,
    _cmd_portfolio, _cmd_economy, _cmd_changes, _cmd_population, _cmd_labour,
    _cmd_hire, _cmd_fire, _cmd_train, _cmd_commission, _cmd_mothball,
    _cmd_restore, _cmd_quote, _cmd_close, _cmd_withdraw, _cmd_bribe,
    _cmd_open, _cmd_ventures, _cmd_policy, _cmd_save, _cmd_step, _cmd_quit,
    _AGENT_DISPATCH_TABLE, _agent_dispatch, _agent_dispatch_inner
)
