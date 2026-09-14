"""Small, dependency-free helpers shared across the protocol package: command-argument parsing (_qty/_num/_clean/_flag), save-path safety, and money-word localisation."""

import collections, hashlib, json, math, os, random, re
from collections import defaultdict

from ..data import *          # the shared tables and loaders
from ..data import (ANNUAL_WAGE, TRADES_ABSENT, TRADE_NOTES, WAGES, closure,
                   critical_path, downstream_count, is_downstream, load, money_word,
                   topo_order, trade_family)
from ..fog import strip_self_play_advice

from ..core import Sim




# ----------------------------------------------------------------------------
# A rendering for a person, alongside the JSON one, not instead of it.
#
# Two testers asked for this in almost the same words: the JSON is precise
# and correct and a wall to read. Everything below turns an outgoing reply
# dict - the exact same dict that gets json.dumps()'d to stdout - into text a
# person can scan. It NEVER changes what goes to stdout; see cli.py's --pretty
# handling, which prints this to stderr, alongside the unmodified JSON line,
# only when asked. The renderer reads the reply dict only, never the live Sim,
# so what a person reads and what a script reads are guaranteed to agree -
# there is only one source of truth for any number in here.
# ----------------------------------------------------------------------------


def _factor(v):
    """A multiplier, at the precision a player would need to reproduce a total.

    _fmt_num drops to one decimal above 1, which turned an opposition factor
    of 1.15 into "x1.1" and made 200 x 1.15 = 230 look like arithmetic the
    game had got wrong. A factor is not a quantity; it is a term in a product
    somebody is going to multiply out.
    """
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return _fmt_num(v)
    f = float(v)
    if abs(f - round(f)) < 5e-4:
        return "%d" % round(f)
    return ("%.3f" % f).rstrip("0")


def _fmt_num(v):
    """A number the way a person reads it: thousands separated, and no more
    precision than is useful. 12345.6 -> "12,346". 4.0 -> "4". 0.375 -> "0.38".

    Whole-feeling numbers (anything 1 and up) carry no decimal at all once
    they are the size a player actually deals in; a tester said reading raw
    JSON here "made me double-check arithmetic", which a rounded, comma'd
    figure does not invite.
    """
    if v is None:
        return "-"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float)):
        f = float(v)
        if f != f or f in (float("inf"), float("-inf")):
            return str(v)
        if f == 0:
            return "0"
        if abs(f) >= 1000:
            return "{:,.0f}".format(f)
        if abs(f) >= 1:
            return "{:,.0f}".format(f) if float(f).is_integer() else "{:,.1f}".format(f)
        return "{:,.2f}".format(f)
    return str(v)


def _fmt_range(v):
    """earns_per_year, under fog, for a thing you have never run: [lo, hi]
    rather than a bare number - see _fog_revenue_estimate. One column had to
    read both shapes, so this reads either and falls back to _fmt_num for
    the ordinary case.
    """
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return "%s-%s" % (_fmt_num(v[0]), _fmt_num(v[1]))
    return _fmt_num(v)


def _pct(v):
    """A 0..1 fraction as a percentage a person reads at a glance.

    NEVER ROUND A FATAL CHANCE TO ZERO. Two play testers were ended by
    something this had just printed as 0%: "1% chance something lands this
    year, of which 0% would end the run", and then the run ended. A number
    that means "this can kill you" and prints as "this cannot happen" is the
    one number in the game that must not be rounded down. Anything that can
    happen at all prints as at least "<1%".
    """
    if v is None:
        return "-"
    try:
        f = 100.0 * float(v)
    except (TypeError, ValueError):
        return str(v)
    if f <= 0.0:
        return "0%"
    if f < 0.5:
        return "<1%"
    return "%.0f%%" % f


def _wrap(text, width=None, indent=""):
    # WIDTH DEFAULTS TO DISPLAY_WIDTH, NOT A LITERAL NUMBER, so the one
    # player-facing preference for it (cli.py's Options screen, "display
    # width") reaches every caller that does not ask for a specific width of
    # its own - see DISPLAY_WIDTH's own comment, near TYPED_HINTS, for who
    # sets it and why `agent` never does.
    if width is None:
        # LIVE, NOT A SNAPSHOT: cli.py's _apply_display_prefs patches
        # engine.protocol.DISPLAY_WIDTH directly (a module attribute, not a
        # call), same as it always has - see DISPLAY_WIDTH's own comment in
        # engine/proto/util.py. Reading it back through the protocol module
        # itself, instead of the plain name this file's own DISPLAY_WIDTH
        # binds, is what makes that patch visible here after the split.
        from .. import protocol as _protocol
        width = _protocol.DISPLAY_WIDTH
    if not text:
        return ""
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(indent + cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(indent + cur)
    return "\n".join(lines)

# HOW WIDE A LINE IS, AND HOW MANY ROWS A PAGE SHOWS, BEFORE A PLAYER ASKS
# FOR SOMETHING ELSE. Both used to be bare numbers scattered through _wrap's
# own default, _available_row's column floor, and _agent_available's page
# slice - which means the game was silently assuming one terminal size and
# one page length for everyone, and a player whose actual terminal was
# narrower lost ids off the edge of a table they meant to copy one out of.
# These are APPLICATION preferences now (cli.py's main-menu Options screen,
# "display width" and "rows per table"; see settings.py's module docstring
# for why they are application-level and not part of any one save), set
# once at the top of cli.py's human-facing entry points - the menu and
# `play` - via cli.py's _apply_display_prefs. `agent` never calls it: its
# JSON protocol (and the --pretty rendering alongside it) is a stable
# machine interface and must render exactly as it always has regardless of
# whichever human happens to be running the script, on whatever terminal.
# The values below are exactly what every caller already hardcoded, so a
# process that never touches these (every `agent` invocation, and any
# `play`/menu session before a player has ever opened Options) renders
# byte-for-byte as it did before this existed.
DISPLAY_WIDTH = 76
DEFAULT_AVAILABLE_LIMIT = 30


SAVE_SUFFIXES = (".json", ".save")


def _unsafe_path(path):
    """None if this is a reasonable place for a save file; a refusal if not.

    Deliberately conservative rather than clever: a save must be a .json or
    .save file, must not be absolute, and must not climb out of where the game
    was started. That covers writing into /etc, which a tester did, without
    pretending to be a security boundary - anyone who can send commands to this
    process can already run code as this user. It is here so the ordinary
    accident does not happen, not because a sandbox exists.
    """
    if os.path.isabs(path):
        return ("a save file must be a relative path, not an absolute one. "
                "Try {\"cmd\":\"save\",\"file\":\"mygame.json\"}")
    norm = os.path.normpath(path)
    if norm.startswith(".." + os.sep) or norm == "..":
        return "a save file cannot be written outside the directory you started in"
    if not norm.lower().endswith(SAVE_SUFFIXES):
        return "a save file should end in %s" % " or ".join(SAVE_SUFFIXES)
    return None


def _qty(cmd, key, default=None):
    """Read a quantity, or say why it is not one. Returns (value, error).

    _num() silently substitutes a default for anything it cannot read, which
    meant {"cmd":"hire","trade":"smith","n":"banana"} hired one smith and
    echoed "n": "banana" back in the reply as though that had been honoured.
    A number that cannot be read is a mistake, and the useful thing to do with
    a mistake is name it. A numeric string is still accepted, because "5" is
    unambiguous and refusing it helps nobody.
    """
    v = cmd.get(key, default)
    if v is None:
        return None, "%s is required" % key
    if isinstance(v, bool):
        return None, "%s must be a number, not true or false" % key
    if isinstance(v, (int, float)):
        f = float(v)
    elif isinstance(v, str):
        try:
            f = float(v.strip())
        except ValueError:
            return None, "%s must be a number, not %r" % (key, v)
    else:
        return None, "%s must be a number, not %s" % (key, type(v).__name__)
    if f != f or f in (float("inf"), float("-inf")):
        return None, ("%s must be a real number; NaN and Infinity are not "
                      "quantities" % key)
    # A QUANTITY, NOT A FLOAT EXPERIMENT. `hire smith 999999999999999999999`
    # was answered with "hiring 1e+21 smiths costs 281250000000000012058624
    # denarii" - a refusal, but one written in scientific notation and binary
    # rounding error, which is the game losing its composure rather than
    # keeping it. Nothing in this world comes in more than a billion.
    if abs(f) > 1e9:
        return None, ("%s must be a quantity of something real. There are not "
                      "a thousand million of anything here" % key)
    return f, None


def _num(v, default=0.0):
    """Read a number from a command without ever raising at the player.

    NaN AND INFINITY ARE NOT NUMBERS FOR THIS PURPOSE. Python's json accepts
    bare NaN and Infinity as an extension, float() accepts the strings, and
    every comparison against NaN is False - so `NaN` walked through every "must
    be greater than zero" guard in the game, set capital to NaN permanently,
    made everything free, and then got written into the save file as bare NaN,
    which is not legal JSON and cannot be read back by anything else. A tester
    bought 999,999 hectares of woodland with 400 denarii this way.
    """
    try:
        f = float(v)
    except (TypeError, ValueError):
        return float(default)
    if f != f or f in (float("inf"), float("-inf")):
        return float(default)
    return f


def _clean(v):
    """True if this is a real, finite number (or something that is not a number
    at all and will be rejected elsewhere). False only for NaN and infinity."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return True
    return v == v and v not in (float("inf"), float("-inf"))


def _flag(v, default=False):
    """Read a switch. "false", "no", "0" and "" are all off.

    A tester set a policy to the STRING "false" and it came back true, because
    bool("false") is true. Every other language on earth has this bug too and it
    is still a bug.
    """
    if isinstance(v, str):
        return v.strip().lower() not in ("", "false", "no", "off", "0", "none")
    return bool(default if v is None else v)


_MONEY_RE = re.compile(r"\bdenarii\b|\bdenarius\b")


def _localise_words(obj, pairs):
    """Rewrite the phrases this civilisation says differently.

    Same mechanism as _localise_money and the same reason: the tree is written
    from Rome 100 AD and stays that way, and a play tester in Han China should
    not be told they are writing their corpus "in plain quantitative Greek and
    Latin" and seeking "Senatorial patronage". Only phrases specific enough to
    occur nowhere else; a historical note ABOUT Rome is left alone, because it
    is about Rome.
    """
    if not pairs:
        return obj
    if isinstance(obj, str):
        for a, b in pairs:
            if a in obj:
                obj = obj.replace(a, b)
        return obj
    if isinstance(obj, list):
        return [_localise_words(x, pairs) for x in obj]
    if isinstance(obj, dict):
        # Keys are protocol; only the values a person reads get rewritten.
        return {k: _localise_words(v, pairs) for k, v in obj.items()}
    return obj


def _localise_money(obj, word):
    """Rewrite the unit of account in anything a player is about to read.

    Every message in the engine is written in denarii because the whole price
    model is calibrated to Rome 100 AD, which is a real modelling decision and
    stays. What does not have to stay is telling a player in 1300 England, or
    in Tenochtitlan, that they are counting Roman coins. This is the one place
    every reply passes through, so the substitution happens once here rather
    than in the twenty-odd messages that mention money.
    """
    if word in ("denarii", "denarius"):
        return obj
    if isinstance(obj, str):
        return _MONEY_RE.sub(word, obj)
    if isinstance(obj, list):
        return [_localise_money(x, word) for x in obj]
    if isinstance(obj, dict):
        # KEYS ARE NOT PROSE. A field name is part of the protocol and scripts
        # match on it; only the values a person reads get rewritten.
        return {k: _localise_money(v, word) for k, v in obj.items()}
    return obj
