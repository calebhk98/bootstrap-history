"""Turning a JSON reply into the readable text `--pretty` and `play` print. Pure presentation: every function here reads an already-built reply dict and returns text, never touching the live Sim - see ARCHITECTURE.md."""

# Split by subject across four siblings so no one file holds more than about
# a thousand lines of code: the big per-screen renderers (render_state,
# render_why, render_available, render_step, and the row helpers only they
# need) in render_screens_big.py; the economic and production accounting
# screens in render_screens_economy.py; the situational and meta screens in
# render_screens_status.py; and the typed-command rendering plus the
# render_pretty entry point in render_typed.py. This file stays the
# composition and re-export point - engine/protocol.py imports a fixed,
# explicit list of names from `.proto.render`, and every one of them is
# re-exported here regardless of which sibling actually defines it, so
# `from engine.protocol import X` and `from engine.proto.render import X`
# both go on working unchanged.

from .render_screens_big import (
    render_state, render_step, render_available, render_why,
    _RESTS_SHORT, _cost_marker, _available_row,
)
from .render_screens_economy import (
    render_capacity, render_materials, render_portfolio, render_economy,
    render_changes, render_money, render_mines, render_labour,
    render_population, render_ventures,
)
from .render_screens_status import (
    render_values, render_final, render_score, render_error, render_stuck,
    render_risk, _advice_line, render_generic, render_log, render_policy,
    render_rush, render_path,
)
from .render_typed import (
    _RENDERERS, TYPED_HINTS, MONEY_SHORT, _typed_form, _JSON_HINT, _JSON_PAIR,
    _typed_deep, to_typed_hints, _DEN_RE, render_pretty,
)
