"""The typed-command rendering and the `--pretty` entry point, split out of
render.py: rewriting a `{"cmd": ...}` worked example in a reply as the words
a player would actually type (_typed_form, _typed_deep, to_typed_hints,
TYPED_HINTS, MONEY_SHORT), the _RENDERERS table that maps a command name to
its screen function, and render_pretty, which looks a reply's screen up in
that table and turns it into text. Pure presentation, same as every module
in this split: nothing here touches the live Sim - see render.py and
ARCHITECTURE.md.
"""

import json, re

from .util import _fmt_num
from .render_screens_big import render_state, render_step, render_available, render_why
from .render_screens_economy import (
    render_capacity, render_materials, render_portfolio, render_economy,
    render_changes, render_money, render_mines, render_labour,
    render_population, render_ventures,
)
from .render_screens_status import (
    render_values, render_final, render_score, render_error, render_stuck,
    render_risk, render_generic, render_log, render_policy, render_rush,
    render_path,
)

_RENDERERS = {
    "policy": render_policy,
    "state": render_state, "step": render_step, "available": render_available,
    "why": render_why, "money": render_money, "ledger": render_money,
    "accounts": render_money, "labour": render_labour, "risk": render_risk,
    "hazards": render_risk, "ventures": render_ventures, "path": render_path,
    "mines": render_mines, "workings": render_mines,
    "stuck": render_stuck, "log": render_log, "history": render_log,
    "values": render_values, "rush": render_rush,
    "capacity": render_capacity, "industry": render_capacity,
    "materials": render_materials,
    "dashboard": render_capacity, "portfolio": render_portfolio,
    "economy": render_economy, "changes": render_changes,
    "population": render_population,
    "final": render_final, "score": render_score,
}


# A REPLY IS FULL OF WORKED EXAMPLES, all of them JSON: 'more:
# knowledge_risk -> {"cmd":"risk"}'. That is exactly right when a script
# is reading, and exactly wrong in front of a person who has just been
# told to type words. The JSON payload itself must not change - it is the
# protocol - so the translation happens here, on the rendered text only, and
# only when the caller says the reader is typing.
TYPED_HINTS = False
# The short form used in the compact lines ("400 den", "net +12 den/yr"). Set
# alongside TYPED_HINTS by whichever front end is rendering; see MONEY_WORDS.
MONEY_SHORT = "den"


def _typed_form(obj):
    """One command dict written the way a person would type it."""
    command = obj.get("cmd")
    if not command:
        return None
    bits = [str(command)]
    if command == "policy" and isinstance(obj.get("set"), dict):
        for switch, value in obj["set"].items():
            bits += [str(switch), "on" if value else "off"]
        return " ".join(bits)
    for key in ("id", "topic", "trade", "what", "material", "subject", "group",
                "file", "path"):
        if obj.get(key) not in (None, "", False):
            bits.append(str(obj[key]))
    for key, word in (("find", "find"), ("search", "find"), ("afford", "afford"),
                      ("limit", "limit"), ("offset", "offset")):
        if obj.get(key) not in (None, "", False):
            bits += [word, _fmt_num(obj[key]) if key != "find" and key != "search"
                     else str(obj[key])]
    for key in ("years", "n", "hours", "amount"):
        if obj.get(key) not in (None, "", False):
            bits.append(_fmt_num(obj[key]))
    if obj.get("all") is True:
        bits.append("all")
    if obj.get("full") is True:
        bits.append("full")
    return " ".join(bits)


# Values may be a bare word rather than a literal: several hints are written as
# worked examples with a placeholder in them ({"cmd":"buy","what":"slaves",
# "n":N}), which is not valid JSON, so the fallback below has to read the
# pairs out textually rather than leaving them untouched in front of a
# person who has been told to type words.


_JSON_HINT = re.compile(r'\{"cmd"\s*:\s*"[a-z_]+"(?:\s*,\s*"[a-z_]+"\s*:\s*'
                        r'(?:"[^"]*"|-?[0-9.]+|true|false|[A-Za-z_][A-Za-z0-9_]*'
                        r'|\{[^{}]*\}))*\}')
_JSON_PAIR = re.compile(r'"([a-z_]+)"\s*:\s*("(?:[^"]*)"|-?[0-9.]+|true|false'
                        r'|[A-Za-z_][A-Za-z0-9_]*)')


def _typed_deep(obj):
    """to_typed_hints applied to every string a renderer is about to read.

    Keys are left alone: a field name is protocol, and only the values a
    person reads get rewritten. Same rule, and same reason, as
    _localise_money.
    """
    if isinstance(obj, str):
        return to_typed_hints(obj)
    if isinstance(obj, list):
        return [_typed_deep(item) for item in obj]
    if isinstance(obj, dict):
        return {field: _typed_deep(value) for field, value in obj.items()}
    return obj


def to_typed_hints(text):
    """Rewrite every {"cmd":...} example in rendered text as a typed command.
    Best-effort: anything that will not parse is left exactly as it was."""
    def sub(match):
        raw = match.group(0)
        try:
            obj = json.loads(raw)
        except ValueError:
            # A worked example with a placeholder in it. Read the pairs off
            # textually and keep the placeholder as the player sees it.
            obj = {}
            for key, val in _JSON_PAIR.findall(raw):
                obj[key] = val[1:-1] if val.startswith('"') else val
            if "cmd" not in obj:
                return raw
        return _typed_form(obj) or raw
    return _JSON_HINT.sub(sub, text)


_DEN_RE = re.compile(r"\bden\b")


def render_pretty(command_name, resp):
    """The human rendering of one reply. Never touches stdout or the JSON
    itself - see cli.py, which prints this to stderr alongside the unchanged
    JSON line, only when --pretty is on.

    Rendering is best-effort ON PURPOSE: a bug in a formatter must cost the
    formatting, never the session. The JSON already went to stdout by the
    time this is called, so the worst this function can do is print an
    apology instead of a pretty table.
    """
    # LIVE, NOT A SNAPSHOT: cmd_play sets engine.protocol.TYPED_HINTS and
    # .MONEY_SHORT directly (module attributes, not a call) once per session
    # - see DISPLAY_WIDTH's own comment in engine/proto/util.py for the same
    # pattern. Reading them back through the protocol module itself, rather
    # than the plain names this file's own assignments below bind, is what
    # makes that patch visible here.
    from .. import protocol as _protocol
    TYPED_HINTS = _protocol.TYPED_HINTS
    MONEY_SHORT = _protocol.MONEY_SHORT
    try:
        if isinstance(resp, dict) and resp.get("ok") is False:
            err = render_error(resp)
            return to_typed_hints(err) if TYPED_HINTS else err
        renderer = _RENDERERS.get((command_name or "").strip().lower(), render_generic)
        # REWRITE THE HINTS BEFORE WRAPPING, NOT AFTER: wrapping around a
        # long {"cmd":"hire","trade":"smith","n":3} and only then replacing
        # it with `hire smith 3` leaves a ragged half-width block wherever
        # the game explains what to type - which is most of the places it
        # explains anything. Wrapping the final words is the only way the
        # line lengths can be right.
        out = renderer(_typed_deep(resp) if TYPED_HINTS else resp)
        if MONEY_SHORT != "den":
            # "Money: 400 den" must not survive unchanged in a game counted
            # in pence: every "den" in the rendered text has to be swapped
            # for MONEY_SHORT, or the reply mixes units.
            out = _DEN_RE.sub(MONEY_SHORT, out)
        return to_typed_hints(out) if TYPED_HINTS else out
    except Exception as error:
        return "(could not render a readable view of this reply: %s: %s)" % (type(error).__name__, error)
