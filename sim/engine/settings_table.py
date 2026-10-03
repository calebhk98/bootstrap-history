"""The settings table: what each entry of settings.CONFIG_DEFAULTS means to a player.

The main menu's Options screen and the `agent` `options` command are both
generated from SETTINGS, so a new setting needs one `Setting` here and no
edit to either menu. `undescribed()` lists any CONFIG_DEFAULTS key without one.

A setting's `kind` says how its text is read:
  path     a directory that can be written to
  width    a column count of at least twenty, or "auto"
  count    a whole number above zero
  flag     on or off
  choice   one of `choices`
  seed     a number or a word, or blank for a fresh random seed each game
  units    one unit per dimension (edited a dimension at a time in the menu)
  text     only the New Game wizard changes it
"""
import os
import re
from dataclasses import dataclass

from . import settings

MINIMUM_WIDTH = 20


@dataclass(frozen=True)
class Setting:
    label: str
    description: str
    kind: str
    choices: tuple = ()
    at_game_start: bool = False   # only read when a game starts
    editable: bool = True
    aliases: tuple = ()


SETTINGS = {
    "save_dir": Setting(
        "save location",
        "Where new games are saved, and where 'Load a saved game' looks. Existing "
        "save files are not moved. The ROME_SAVE_DIR environment variable, when set, "
        "overrides this.", "path", aliases=("save", "location")),
    "display_width": Setting(
        "display width",
        "How many columns text wraps to and tables are sized for. Left alone, the "
        "game asks your terminal; a number overrides it, 'auto' goes back to asking.",
        "width", aliases=("width", "display")),
    "rows_per_page": Setting(
        "rows per table",
        "How many rows a long table (chiefly `available`) shows before paging.",
        "count", aliases=("rows", "page")),
    "show_welcome": Setting(
        "welcome/tutorial text on new games",
        "Whether the arrival paragraph and starter-verb tutorial print for a new game.",
        "flag", aliases=("welcome", "tutorial")),
    "display_units": Setting(
        "display units",
        "The unit shown for each kind of quantity (area, mass, temperature, money). "
        "Commands still take the units their help names.", "units", aliases=("unit", "units")),
    "commission_display": Setting(
        "commission display",
        "Which mine dates are shown: when the mine is commissioned, when it is ready, "
        "or both.", "choice", choices=("commissioned", "ready", "both")),
    "default_seed": Setting(
        "seed for new games",
        "A number or one word (letters, digits, '-' or '_') the new-game menu uses "
        "when its seed question is left blank. Blank or 'random' draws a fresh one.",
        "seed", at_game_start=True, aliases=("seed",)),
    "default_events": Setting(
        "events (weather, plague, politics)",
        "Whether dated hazards roll in a typed `play` game. `agent` games use the "
        "--no-events flag instead.", "flag", at_game_start=True, aliases=("events",)),
    "default_deterministic": Setting(
        "deterministic dice",
        "Replace the dice with a fixed, luck-free generator in a typed `play` game. "
        "Not the same as turning events off. `agent` games use --deterministic.",
        "flag", at_game_start=True, aliases=("deterministic",)),
    "default_fog": Setting(
        "fog of war",
        "Whether the tree is hidden until you hear of it. A game keeps the fog it "
        "started with: it cannot be changed once the game is running.",
        "flag", at_game_start=True, aliases=("fog",)),
    "default_fuzzy_estimates": Setting(
        "fuzzy estimates",
        "Whether the needs of unfinished work are shown as estimates. The in-game "
        "options screen can turn it on later but not off again.",
        "flag", at_game_start=True, aliases=("fuzzy",)),
    "default_mortal": Setting(
        "mortality",
        "Whether the founder ages and can die. The in-game options screen can turn "
        "it on later but not off again.", "flag", at_game_start=True, aliases=("mortal",)),
    "default_horizon": Setting(
        "horizon (years)",
        "How many years a new game runs. The in-game options screen can move it later.",
        "count", at_game_start=True, aliases=("horizon",)),
    "default_civ": Setting(
        "civilisation",
        "The civilisation the New Game wizard offers first; it remembers your last choice.",
        "text", at_game_start=True, editable=False),
    "default_kit": Setting(
        "starting kit",
        "The starting kit the New Game wizard offers first; it remembers your last choice.",
        "text", at_game_start=True, editable=False),
    "default_goal": Setting(
        "goal",
        "The goal the New Game wizard offers first; blank is the tree's own default.",
        "text", at_game_start=True, editable=False),
}

UNCHANGED = object()   # parse_value result for a blank answer


def undescribed():
    """Settings with no entry in the table."""
    return sorted(key for key in settings.CONFIG_DEFAULTS if key not in SETTINGS)


def valid_seed_text(text):
    """A seed must be one word of letters, digits, '-' or '_', so it can be
    passed back to --seed unquoted."""
    return bool(re.fullmatch(r"[A-Za-z0-9_-]+", str(text).strip()))


def normal_seed(text):
    """A seed as the game keeps it: a whole number when it is all digits, else
    the word in lower case. random.Random seeds from either and replays the
    same dice for the same value."""
    if isinstance(text, int):
        return text
    text = str(text).strip().lower()
    return int(text) if text.isdigit() else text


def find(word):
    """The key a typed menu choice names: a 1-based number, the key, a label or an alias."""
    word = str(word).strip().lower()
    keys = list(SETTINGS)
    if word.isdigit() and 1 <= int(word) <= len(keys):
        return keys[int(word) - 1]
    for key, spec in SETTINGS.items():
        if word in (key, spec.label.lower()) or word in spec.aliases:
            return key
    return None


def display_value(key, cfg):
    """The setting's current value as a player reads it."""
    spec, value = SETTINGS[key], cfg.get(key, settings.CONFIG_DEFAULTS.get(key))
    if spec.kind == "path":
        return settings.resolve_save_dir(cfg, ensure=False)
    if spec.kind == "width":
        overridden = isinstance(value, (int, float)) and value
        return "%d columns (%s)" % (settings.resolve_display_width(cfg),
                                    "override" if overridden else "detected from your terminal")
    if spec.kind == "units":
        from sim.engine.units_summary import summary_line
        return summary_line(cfg)
    if spec.kind == "flag":
        return "on" if value else "off"
    if spec.kind == "seed":
        return "a fresh random seed" if value is None else str(value)
    if value is None:
        return "the tree's own default" if key == "default_goal" else "unset"
    return str(value)


def screen_lines(cfg):
    """The options screen's numbered rows, one per setting."""
    return ["   %d) %-34s: %s%s" % (
        number, spec.label, display_value(key, cfg),
        "   (applies when a game starts)" if spec.at_game_start else "")
        for number, (key, spec) in enumerate(SETTINGS.items(), 1)]


def _flag_value(raw):
    if isinstance(raw, bool):
        return raw
    word = str(raw).strip().lower()
    if word in ("y", "yes", "on", "true", "1"):
        return True
    if word in ("n", "no", "off", "false", "0"):
        return False
    return None


def _whole_number(raw, minimum):
    try:
        number = int(str(raw).strip())
    except ValueError:
        return None
    return number if number >= minimum else None


def _writable_directory(raw):
    path = os.path.expanduser(str(raw).strip())
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".rome-write-test")
        with open(probe, "w"):
            pass
        os.remove(probe)
    except OSError as error:
        return None, "could not use that directory: %s" % error
    return path, None


def parse_value(key, raw):
    """(value, None) for a good answer, (None, reason) for a bad one, or
    (UNCHANGED, None) for a blank one. `raw` is typed text or a JSON value."""
    spec = SETTINGS[key]
    if not spec.editable or spec.kind == "units":
        return None, "%s is not set by value here%s" % (
            spec.label, "; use the options screen in `play` or the main menu"
            if spec.kind == "units" else "; the New Game wizard remembers it")
    if isinstance(raw, str) and not raw.strip() and spec.kind != "seed":
        return UNCHANGED, None
    if spec.kind == "path":
        return _writable_directory(raw)
    if spec.kind == "width":
        if str(raw).strip().lower() in ("auto", "detect", "default"):
            return None, None
        width = _whole_number(raw, MINIMUM_WIDTH)
        return (width, None) if width else (None, "a whole number of columns (at least %d) or 'auto'" % MINIMUM_WIDTH)
    if spec.kind == "count":
        count = _whole_number(raw, 1)
        return (count, None) if count else (None, "a whole number above zero")
    if spec.kind == "flag":
        flag = _flag_value(raw)
        return (flag, None) if flag is not None else (None, "yes or no (on or off)")
    if spec.kind == "choice":
        word = str(raw).strip().lower()
        return (word, None) if word in spec.choices else (None, "one of: " + ", ".join(spec.choices))
    if spec.kind == "seed":
        word = "" if raw is None else str(raw).strip()
        if word.lower() in ("", "none", "random"):
            return None, None
        if valid_seed_text(word):
            return normal_seed(word), None
        return None, "one word of letters, digits, '-' or '_', or blank for a random seed"
    return None, "cannot be set here"


def rows(cfg):
    """Every setting as data, for the `agent` `options` command."""
    return [{"key": key, "label": spec.label, "value": cfg.get(key), "shown_as": display_value(key, cfg),
             "description": spec.description, "kind": spec.kind, "choices": list(spec.choices),
             "applies_when_a_game_starts": spec.at_game_start, "settable": spec.editable and spec.kind != "units"}
            for key, spec in SETTINGS.items()]
