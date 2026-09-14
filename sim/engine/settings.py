"""Where a player's stuff lives, and what they told the menu to remember.

Two different things share this file, and the difference matters:

  1. THE CONFIG - a handful of preferences that live OUTSIDE any one game,
     at a fixed place on disk, and are read again on the NEXT invocation of
     the process. This is what makes "put my saves somewhere else" stick
     without a flag: see PLAYER REQUEST #1 below.

  2. PER-SESSION META - a couple of fields (right now, just the horizon) that
     belong to one save file but are not part of the save format the engine
     itself owns (rome/sim/engine/protocol.py: SAVE_FIELDS, save_state,
     load_state). That file is rewritten from a fixed field list after every
     single command, so anything written here is not preserved there. It
     gets a small sidecar of its own instead.

Nothing in this module is imported by, or imports, protocol.py/core.py/
projects.py/labour.py/society.py/economy.py: it is filesystem bookkeeping
around the engine, not the engine. (protocol.py does carry a couple of
module-level variables this module's VALUES end up in - DISPLAY_WIDTH,
DEFAULT_AVAILABLE_LIMIT - but cli.py is what copies them there; this module
still never imports protocol.py, nor the reverse.)

THE CONFIG IS FOR THE APPLICATION, NOT FOR ANY ONE GAME. An earlier version
of this file, and of the main-menu Options screen built on it, held
"defaults for the next new game" here too - which civilisation, which
starting kit, fog of war, mortality, the horizon - on the reasoning that a
player who always starts the same way shouldn't have to retype it. That
reasoning was sound, but CONFIG_PATH is the wrong place for it: these are
facts about a PLAYTHROUGH, the same way fog and mortality are, and a player
asking "why is the save location next to 'which civilisation' on the same
settings screen" was asking the right question - the owner's own words, on
being shown that screen, were "change where saves are, change language,
change window size, etc? Not about each save, like fog or mortality?" So
the Options screen now holds only what is actually about the PROGRAM: where
saves go, how wide a line is, how many rows a table shows before paging,
and whether the welcome/tutorial text prints for a game that has not
started yet.

The "remembered default civilisation/kit/fog/mortality/horizon" capability
is not deleted, because a player who favours one civilisation and one kit
still should not have to retype them - it just no longer has a settings
screen of its own. _new_game (cli.py) still prefills its five questions from
whatever was chosen LAST TIME, and silently writes this sitting's answers
back as the new "last time" the moment the wizard finishes, the same way a
text editor remembers your last file dialog folder without asking you to
configure it. DEFAULT_CIV etc., below, are that memory; nothing edits them
directly any more.

Changing the horizon mid-game, or turning mortality on mid-game, are
reasonable things a player reaches for WHILE PLAYING, not before - that
capability lives in cli.py's in-game 'options' command (_ingame_options),
unrelated to this file's config and not moved by any of the above.

PLAYER REQUEST #1 - "saves in a place that survives": several players run
somewhere the default save directory (~/.rome-saves) is not the durable
storage they actually have - a fresh container on every terminal session,
with a persistent volume mounted somewhere else entirely. Three ways to say
where saves should go, checked in this order, so whichever one actually
survives in a given environment works:

  1. the ROME_SAVE_DIR environment variable, for a player who can export
     one line in a shell profile that DOES survive even when $HOME does not
  2. "save_dir" in the config file (see CONFIG_PATH below), for a player who
     sets it once from the Options menu and whose home directory is the
     thing that survives
  3. ~/.rome-saves, unchanged, for everyone who has not asked for anything
     else

DISPLAY WIDTH - "change window size": the renderers in protocol.py wrap text
and size tables to a number of columns that used to be a bare constant
(76, in most places), which is exactly the "terminal of a particular size"
assumption that cost players truncated ids on a narrower terminal. A player
can set an explicit width from Options; left alone (None), resolve_
display_width below asks the terminal itself via shutil.get_terminal_size,
and only falls back to the old hardcoded number when there is no terminal
to ask (a pipe, a redirected file, the test suite) - so nothing a script or
a regression check reads changes because this preference exists.

LANGUAGE - deliberately absent. The natural fourth item on a "window size,
save location" list is "language", and it is not here: this codebase has no
internationalisation to switch on. _localise_words/_localise_money in
protocol.py swap the NAME of the currency per civilisation (denarii,
hacksilver, beans, pence) - flavour, not translation - and the many
thousands of words of node notes (rome/data/tech_tree.json) and the
rome/knowledge/ corpus exist in English only. A menu entry offering
"language" with nothing behind it would be worse than no entry: a setting
that silently does nothing. Real language support would mean translating
every node note and every rendered sentence in protocol.py/cli.py (not a
small rewrite - protocol.py alone is thousands of lines of prose, generated
sentence by sentence from game state) and deciding what happens to
rome/knowledge/, which is English prose no translation layer touches
automatically. That is a project of its own, not a field in this file.
"""
import json
import os
import re
import shutil
import time


# ---------------------------------------------------------------------------
# The config file: a handful of preferences that outlive any one game.
# ---------------------------------------------------------------------------

# ROME_SIM_CONFIG lets a player put the config file itself somewhere durable,
# for the same reason ROME_SAVE_DIR exists: an environment where $HOME does
# not survive between terminal sessions cannot be fixed by writing a dotfile
# into $HOME, however sensible that dotfile is everywhere else.
SAVE_DIR_ENV = "ROME_SAVE_DIR"
CONFIG_PATH_ENV = "ROME_SIM_CONFIG"

_DEFAULT_SAVE_DIR = os.path.join(os.path.expanduser("~"), ".rome-saves")
_DEFAULT_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".rome-sim-config.json")

# APPLICATION PREFERENCES - the main-menu Options screen, in full. Every one
# of these is about the program, never about a playthrough: see the module
# docstring's "THE CONFIG IS FOR THE APPLICATION" section for why fog,
# mortality and the rest of a game's own setup are not in this list.
#
# display_width: None means "ask the terminal" (resolve_display_width,
#   below); an explicit number is a player override, for a terminal that
#   cannot be asked (some multiplexers, a logged session) or one the player
#   simply wants narrower or wider than their actual window.
# rows_per_page: how many rows a long, pageable table (chiefly `available`,
#   searched or paged) shows before a player has to ask for more.
# show_welcome: whether the one-time-per-new-game arrival paragraph and
#   starter-verb tutorial print. A player on their fifth new game does not
#   need the five starter verbs explained again; see cmd_play and cmd_menu.
CONFIG_DEFAULTS = {
    "save_dir": None,          # None means "use the rule above"
    "display_width": None,     # None means "ask the terminal; see below"
    "rows_per_page": 30,
    "show_welcome": True,
    # REMEMBERED, NOT CONFIGURED - see the module docstring. These four plus
    # the horizon are the New Game wizard's last-used answers, written back
    # by cli.py's _new_game the moment a game actually starts, and are not
    # edited from the Options screen; they exist so a player who favours
    # one civilisation and kit is not asked to retype them, not so there is
    # a settings page for "which civilisation".
    "default_civ": "rome_100ad",
    "default_kit": "poor_scholar",
    "default_fog": True,
    "default_mortal": False,
    # None means "the tree's own default" (meta.goal_node, the transistor) -
    # see _new_game, which resolves this the same way resolve_goal() does.
    "default_goal": None,
    "default_horizon": 500,
}

# THE OLD HARDCODED NUMBERS, named, so a process that cannot ask its
# terminal (a pipe, a redirected file, every subprocess the test suite
# spawns) sees the exact width/page-size the game always used, not some
# other arbitrary number - see resolve_display_width.
FALLBACK_DISPLAY_WIDTH = 76
FALLBACK_ROWS_PER_PAGE = 30


def resolve_display_width(cfg=None):
    """How many columns to wrap text to and size tables for: an explicit
    player override (cfg['display_width']) if one is set, otherwise the
    terminal's own width via shutil.get_terminal_size().

    shutil.get_terminal_size already does the right thing for "cannot be
    detected": it checks the COLUMNS environment variable, then asks the
    OS for the real size of whatever is attached to stdout, and only when
    NEITHER of those works (stdout is a pipe or a redirected file, exactly
    what every subprocess in this repository's own test suite runs with)
    does it fall back to the `fallback` argument - which is why that
    argument is FALLBACK_DISPLAY_WIDTH, the number every renderer already
    hardcoded, rather than some other guess. A test, or a player piping
    output to a file, sees precisely the old behaviour; a player at a real
    terminal gets its actual width.
    """
    if cfg is None:
        cfg = load_config()
    override = cfg.get("display_width")
    if isinstance(override, (int, float)) and override > 0:
        return int(override)
    return shutil.get_terminal_size(
        fallback=(FALLBACK_DISPLAY_WIDTH, 24)).columns


def resolve_rows_per_page(cfg=None):
    """How many rows a long table pages by before a player has to ask for
    more (see protocol.DEFAULT_AVAILABLE_LIMIT). A bare positive integer
    from the config, or FALLBACK_ROWS_PER_PAGE if it is missing or not one -
    never zero or negative, which would page nothing at all."""
    if cfg is None:
        cfg = load_config()
    try:
        n = int(cfg.get("rows_per_page", FALLBACK_ROWS_PER_PAGE))
    except (TypeError, ValueError):
        n = FALLBACK_ROWS_PER_PAGE
    return n if n > 0 else FALLBACK_ROWS_PER_PAGE


def config_path():
    return os.environ.get(CONFIG_PATH_ENV) or _DEFAULT_CONFIG_PATH


def load_config():
    """The player's saved preferences, or CONFIG_DEFAULTS if there are none
    yet or the file cannot be read. Never raises: a corrupt or missing
    config is a fresh install, not an error a player should see."""
    cfg = dict(CONFIG_DEFAULTS)
    try:
        with open(config_path()) as fh:
            raw = json.load(fh)
        if isinstance(raw, dict):
            for k in CONFIG_DEFAULTS:
                if k in raw:
                    cfg[k] = raw[k]
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    """Write the preferences back. Atomic, like the game's own save_state,
    for the same reason: a crash mid-write must not leave a config file that
    loads as neither the old preferences nor the new ones."""
    path = config_path()
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except OSError:
            return False
    out = {k: cfg.get(k, CONFIG_DEFAULTS[k]) for k in CONFIG_DEFAULTS}
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def resolve_save_dir(cfg=None, ensure=True):
    """Where saves go right now, in order: ROME_SAVE_DIR, the config file's
    save_dir, then ~/.rome-saves. Creates the directory if it does not exist
    yet and `ensure` is true; falls back to "." if it cannot be created or
    written to at all, the same fallback _pick_session_filename always had."""
    env = os.environ.get(SAVE_DIR_ENV)
    if env:
        d = os.path.expanduser(env)
    else:
        if cfg is None:
            cfg = load_config()
        d = cfg.get("save_dir") or _DEFAULT_SAVE_DIR
        d = os.path.expanduser(d)
    if ensure:
        try:
            os.makedirs(d, exist_ok=True)
            # Confirm it is actually writable, not merely present - a
            # directory that exists but is read-only would otherwise surface
            # as a save failure deep inside the game instead of here, where
            # the player is choosing a location and can pick another one.
            probe = os.path.join(d, ".rome-write-test")
            with open(probe, "w"):
                pass
            os.remove(probe)
        except OSError:
            return "."
    return d


# ---------------------------------------------------------------------------
# Per-session meta: the one field (horizon) a save's own file cannot carry.
# ---------------------------------------------------------------------------

def _meta_path(session):
    return session + ".meta.json" if session else None


def load_session_meta(session):
    """{} if there is no sidecar yet, or it cannot be read - never raises,
    the same policy as load_config: an absent or corrupt sidecar is exactly
    what an ordinary flag-driven save (never touched by the menu or the
    in-game options command) always has."""
    path = _meta_path(session)
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path) as fh:
            v = json.load(fh)
        return v if isinstance(v, dict) else {}
    except (OSError, ValueError):
        return {}


def save_session_meta(session, meta):
    path = _meta_path(session)
    if not path:
        return False
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as fh:
            json.dump(meta, fh, indent=1, sort_keys=True)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def move_session_meta(old_session, new_session):
    """Carry the sidecar along when a save is moved to a new path. Losing it
    silently would not corrupt anything - see load_session_meta - it would
    just quietly forget a horizon the player deliberately changed, which is
    exactly the kind of small unannounced loss a save-relocation feature
    exists to never cause."""
    old_meta = load_session_meta(old_session)
    old_path = _meta_path(old_session)
    if old_meta:
        save_session_meta(new_session, old_meta)
    if old_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# CHECKPOINTS: a manual save is frozen, an ongoing session is not.
#
# --session autosaves after every command, which is correct and wanted for an
# ongoing game - it is the one file that is always the LATEST word on where
# that game stands. A milestone (cli.py's bare 'save', mid-game) is a
# different thing on purpose: a moment a player chose to be able to come back
# to. Before this existed, "come back to it" meant pointing --session (or the
# main menu's Load screen, or the in-game bare 'load') AT the milestone file,
# which is exactly what turned it into the new autosave target - the very
# next command overwrote it, and a player who saved 380 AD to return to found
# it quietly became 420 AD the first time they looked. A player deep into a
# long campaign, using checkpoints to isolate a bug, discovered this the hard
# way: the first reload had already moved the evidence.
#
# is_checkpoint below is what the three resume paths (cli.py's cmd_play,
# cmd_agent, and _ingame_load) all check before deciding whether resuming a
# file may go on autosaving to that same file, or has to fork a new one - see
# cli.py's own comments at each of those call sites for what happens once the
# answer is yes.
_MILESTONE_RE = re.compile(r"_saved_\d+\.json$")


def is_checkpoint(path):
    """Whether `path` names a frozen checkpoint rather than an ordinary,
    freely-autosaved session file.

    Two independent signals, either one enough:

    1. THE FILENAME. Every milestone this game itself has ever written
       matches this pattern - see cli.py's _pick_milestone_filename - so a
       milestone nobody has touched by hand is always caught here, with no
       sidecar required at all (and no sidecar existed for milestones before
       this fix, so this is also what recognises one saved by an older
       version of the game).
    2. THE SIDECAR. _ingame_save_milestone also stamps a "checkpoint": true
       marker into the file's own .meta.json (see save_session_meta below).
       This is what keeps the answer right if the file is later renamed or
       moved BY THE GAME'S OWN "move this save" option (move_session_meta
       carries every sidecar field, this one included, to the new name) -
       the filename pattern alone would stop matching the moment the name
       changed. A rename made by hand, outside the game entirely, has no
       sidecar to carry either way and is not something this can see; that is
       the same limit civ_of_save/goal_of_save already live with for any
       other fact a save's own filename does not carry.

    Neither signal costs anything to check speculatively: an ordinary file a
    player simply happens to name in the milestone's own pattern is treated
    as frozen too, which only ever means a resume forks a fresh session
    file instead of writing back into the one they typed - never a lost
    game, and always said out loud when it happens.
    """
    if not path:
        return False
    if _MILESTONE_RE.search(os.path.basename(path)):
        return True
    return bool(load_session_meta(path).get("checkpoint"))


# ---------------------------------------------------------------------------
# Listing saves, for "Load a saved game".
# ---------------------------------------------------------------------------

def list_saves(save_dir):
    """One summary dict per save file in `save_dir`, newest-written first.

    Reads the JSON directly rather than going through the engine's
    load_state: this runs before any Sim exists (the whole point is to help
    a player choose which one to build), and it must not refuse a file just
    because it looks odd - a save this listing cannot make sense of is still
    shown, with what little can be read from it, rather than silently
    dropped from the list a player is choosing a filename out of.
    """
    out = []
    try:
        names = os.listdir(save_dir)
    except OSError:
        return out
    for fn in sorted(names):
        if not fn.endswith(".json") or fn.endswith(".meta.json"):
            continue
        path = os.path.join(save_dir, fn)
        try:
            st = os.stat(path)
        except OSError:
            continue
        if st.st_size == 0:
            # A slot claimed by _pick_session_filename's O_EXCL but never
            # actually played into - see cli.py's _is_claimed_slot. Not a
            # save; skip it rather than show a player an entry that errors
            # the moment they pick it.
            continue
        row = {"path": path, "filename": fn, "mtime": st.st_mtime,
               "readable": False}
        try:
            with open(path) as fh:
                blob = json.load(fh)
            if not isinstance(blob, dict) or "_civ" not in blob:
                continue
            row.update({
                "readable": True,
                "civ_id": blob.get("_civ"),
                "year": blob.get("year"),
                "fog": bool(blob.get("_fog", False)),
                "founder_alive": blob.get("founder_alive", True),
                "dead_reason": blob.get("dead_reason"),
                "goal_year": blob.get("goal_year"),
                "goal": blob.get("_goal"),
                "reputation": blob.get("reputation"),
                "scholars": blob.get("scholars"),
                "artisans": blob.get("artisans"),
                "capital": blob.get("capital"),
                "done": ((blob.get("done") or {}).get("__set__") or []),
            })
        except (OSError, ValueError):
            pass
        out.append(row)
    out.sort(key=lambda r: -r["mtime"])
    return out


def humanize_age(mtime):
    """'3 minutes ago', 'yesterday', 'on 2026-03-01' - roughly, not exactly:
    a player choosing between saves wants a sense of how stale one is, not a
    timestamp to do arithmetic on."""
    delta = max(0, time.time() - mtime)
    if delta < 90:
        return "moments ago"
    mins = delta / 60
    if mins < 90:
        return "%d minutes ago" % mins
    hours = mins / 60
    if hours < 36:
        return "%d hours ago" % hours
    days = hours / 24
    if days < 2:
        return "yesterday"
    if days < 14:
        return "%d days ago" % days
    return time.strftime("on %Y-%m-%d", time.localtime(mtime))
